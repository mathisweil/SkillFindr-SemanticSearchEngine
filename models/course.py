from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import TEXT, INTEGER, REAL, ARRAY
from pgvector.sqlalchemy import Vector

class Course(SQLModel, table=True):
    __tablename__ = "courses"

    course_id: str = Field(
        sa_column=Column(TEXT, primary_key=True)
    )
    course_url: str = Field(
        sa_column=Column(TEXT, unique=True, nullable=False)
    )
    category: str | None = Field(
        default=None,
        sa_column=Column(TEXT)
    )
    type: str | None = Field(
        default=None,
        sa_column=Column(TEXT)
    )
    title: str | None = Field(
        default=None,
        sa_column=Column(TEXT)
    )
    duration: int | None = Field(
        default=None,
        sa_column=Column(INTEGER)
    )
    learners_amount: int | None = Field(
        default=None,
        sa_column=Column(INTEGER)
    )
    star_rating: float | None = Field(
        default=None,
        sa_column=Column(REAL)
    )
    star_num_ratings: int | None = Field(
        default=None,
        sa_column=Column(INTEGER)
    )
    description: str | None = Field(
        default=None,
        sa_column=Column(TEXT)
    )
    tags: list[str] | None = Field(
        default=None,
        sa_column=Column(ARRAY(TEXT))
    )
    title_raw: str | None = Field(
        default=None,
        sa_column=Column(TEXT)
    )
    description_raw: str | None = Field(
        default=None,
        sa_column=Column(TEXT)
    )
    languages: list[str] | None = Field(
        default=None,
        sa_column=Column(ARRAY(TEXT))
    )
    tags_raw: list[str] | None = Field(
        default=None,
        sa_column=Column(ARRAY(TEXT))
    )
    embedding_input_combined: str | None = Field(
        default=None,
        sa_column=Column(TEXT)
    )
    embedding_vector: list[float] | None = Field(
        default=None,
        sa_column=Column(Vector(384))
    )
    distance: float | None = Field(default=None, sa_column=None)
