from sqlmodel import SQLModel, Field

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