from fastapi import FastAPI
from sqlmodel import SQLModel, Field
from embedding.retrieve_courses import semantic_search
from utils.llm import generate_answer

app = FastAPI()


class RangeFilter(SQLModel):
    min: int = Field(..., ge=0, description="Lower bound (inclusive)")
    max: int = Field(..., ge=0, description="Upper bound (inclusive)")


class Filters(SQLModel):
    star_rating: RangeFilter | None = Field(None, description="Range of star ratings")
    learners_amount: RangeFilter | None = Field(None, description="Range of learners amounts")
    duration: RangeFilter | None = Field(None, description="Range of durations in minutes")
    category: list[str] | None = Field(
        None,
        min_items=1,
        description="List of course categories (e.g. ['cloud_computing','cs'])"
    )


# 3. Define the envelope for your search request
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
        orm_mode = True


class RAGResponse(SQLModel):
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
    raw_filters = {}
    if payload.filters:
        raw_filters = {
            k: v for k, v in payload.filters.model_dump().items()
            if v is not None
        }
    results = semantic_search(
        query=payload.query,
        threshold=payload.threshold,
        limit=payload.limit,
        filters=raw_filters
    )
    return results


@app.post(
    "/api/v1/rag",
    response_model=RAGResponse,
    summary="Retrieval‐Augmented Generation over courses",
    tags=["rag"],
    response_model_exclude_none=True
)
async def rag_endpoint(payload: SearchRequest):
    raw_filters = {}
    if payload.filters:
        raw_filters = {
            k: v for k, v in payload.filters.model_dump().items()
            if v is not None
        }
    tops = semantic_search(
        query=payload.query,
        threshold=payload.threshold,
        limit=payload.limit,
        filters=raw_filters
    )

    answer = await generate_answer(
        query=payload.query,
        contexts=[f"{c['title']}: {c['description']}" for c in tops]
    )

    return RAGResponse(answer=answer, sources=tops)
