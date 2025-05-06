import os

from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Field
from typing import Literal
from models.course import Course

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


class CourseRead(Course):
    embedding_vector: list[float] | None = None

    class Config:
        from_attributes = True
        fields = {"embedding_vector": {"exclude": True}}


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
    sources: list[CourseRead] = Field(
        ..., description="Top matching courses used as context"
    )


@app.post(
    "/api/v1/courses/search/semantic",
    response_model=list[CourseRead],
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
