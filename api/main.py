import os

from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Field
from typing import Literal

from embedding.retrieve_courses import semantic_search
from embedding.model_loader import load_embedding_model
from utils.llm import load_llm_model, generate_answer
from config.config import get_database_engine


resources = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    resources["embedding_model"] = load_embedding_model(os.getenv("EMBEDDING_MODEL_NAME"))
    resources["llm_model"], resources["llm_tokenizer"] = load_llm_model(os.getenv("LLM_MODEL_NAME"))
    resources["db_engine"] = get_database_engine(os.getenv("DATABASE_URL"))
    yield
    resources.clear()


app = FastAPI(lifespan=lifespan)
origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,              # or ["*"] to allow all (not recommended for prod)
    allow_credentials=True,
    allow_methods=["*"],                # e.g. ["GET", "POST", "PUT", "DELETE"]
    allow_headers=["*"],                # e.g. ["Authorization", "Content-Type"]
)


class RangeFilter(SQLModel):
    min: int | None = Field(None, ge=0, description="Lower bound (inclusive)")
    max: int | None = Field(None, ge=0, description="Upper bound (inclusive)")


class Filters(SQLModel):
    star_rating: RangeFilter | None = Field(None, description="Range of star ratings")
    learners_amount: RangeFilter | None = Field(None, description="Range of learners amounts")
    duration: RangeFilter | None = Field(None, description="Range of durations in minutes")
    category: list[str] | None = Field(
        None,
        min_items=1,
        description="List of course categories (e.g. ['cloud_computing','cs'])"
    )


class SearchRequest(SQLModel):
    query: str = Field(..., description="Natural‐language search string")
    threshold: float = Field(
        0.5, ge=0.0, le=1.0,
        description="Maximum pgvector distance"
    )
    limit: int = Field(5, ge=1, description="Maximum number of results")
    filters: Filters | None = Field(None, description="Filters for specific course attributes")


class CourseOut(SQLModel):
    course_id: str = Field(..., description="Primary key: unique course identifier")
    course_url: str = Field(None, description="URL to the course page")
    category: str | None = Field(None, description="High‑level course category")
    type: str | None = Field(None, description="Course format or type")
    title: str | None = Field(None, description="Course title")
    duration: int | None = Field(None, description="Duration in minutes")
    learners_amount: int | None = Field(None, description="Number of enrolled learners")
    star_rating: float | None = Field(None, description="Average star rating")
    star_num_ratings: int | None = Field(None, description="Total number of ratings")
    description: str | None = Field(None, description="Short course description")
    tags: list[str] | None = Field(None, description="Normalized tags array")
    title_raw: str | None = Field(None, description="Original, un‑normalized title")
    description_raw: str | None = Field(None, description="Original, un‑normalized description")
    languages: list[str] | None = Field(None, description="Languages in which course is offered")
    tags_raw: list[str] | None = Field(None, description="Original tags array")
    embedding_input_combined: str | None = Field(
        None,
        description="Text that was fed into the embedding model"
    )
    embedding_vector: list[float] | None = Field(
        None,
        description="384‑dimensional embedding vector (pgvector)",
        exclude=True
    )

    class Config:
        from_attributes = True


class ChatMessage(SQLModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(SQLModel):
    chat_history: list[ChatMessage]
    threshold: float = Field(0.5, ge=0.0, le=1.0)
    limit: int = Field(5, ge=1)
    filters: Filters | None = None


class ChatResponse(SQLModel):
    answer: str = Field(..., description="The LLM’s generated answer")
    sources: list[CourseOut] = Field(
        ..., description="Top matching courses used as context"
    )


@app.post(
    "/api/v1/courses/search/semantic",
    response_model=list[CourseOut],
    summary="Semantic search over courses",
    tags=["courses"],
    response_model_exclude_none=True
)
async def semantic_search_endpoint(payload: SearchRequest):
    raw_filters = {
        k: v
        for k, v in (payload.filters or Filters()).model_dump().items()
        if v is not None
    }
    results = semantic_search(
        query=payload.query,
        model=resources["embedding_model"],
        engine=resources["db_engine"],
        threshold=payload.threshold,
        limit=payload.limit,
        filters=raw_filters
    )
    return results


@app.post(
    "/api/v1/chat",
    response_model=ChatResponse,
    summary="Retrieval‐Augmented Generation over courses",
    tags=["rag"],
    response_model_exclude_none=True
)
async def rag_endpoint(payload: ChatRequest):
    try:
        last_user = next(
            msg.content
            for msg in reversed(payload.chat_history)
            if msg.role == "user"
        )
    except StopIteration:
        raise HTTPException(
            status_code=400,
            detail="chat_history must contain at least one user message"
        )

    raw_filters = {
        key: val
        for key, val in (payload.filters or Filters()).model_dump().items()
        if val is not None
    }

    tops = semantic_search(
        query=last_user,
        model=resources["embedding_model"],
        engine=resources["db_engine"],
        threshold=payload.threshold,
        limit=payload.limit,
        filters=raw_filters
    )

    if not tops:
        return ChatResponse(
            answer=(
                "I could not find anything close to your last query. "
                "Try rephrasing or broadening your search."
            ),
            sources=[]
        )

    answer = await generate_answer(
        query=last_user,
        courses=tops,
        chat_history=[msg.model_dump() for msg in payload.chat_history],
        model=resources["llm_model"],
        tokenizer=resources["llm_tokenizer"]
    )

    return ChatResponse(answer=answer, sources=tops)
