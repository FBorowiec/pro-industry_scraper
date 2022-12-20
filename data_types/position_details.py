from datetime import datetime

from pydantic import BaseModel, validator


class PositionDetails(BaseModel):
    location: str
    salary_range: str
    job_type: str
    contract_type: str
    position_name: str
    industry: str
    required_education: str
    time_length: str | None
    hours: str

    @validator("location", "job_type", "contract_type", "position_name", "industry", pre=True)
    def capitalize(cls, value: str) -> str:
        return value.capitalize()

    @validator("salary_range", pre=True)
    def validate_salary_range(cls, salary_range: str) -> str:
        return salary_range.replace(" ", "").replace("\xa0", "").replace("\n", "")

    class Config:
        allow_extra = False
