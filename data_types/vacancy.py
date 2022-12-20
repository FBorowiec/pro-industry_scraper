from datetime import datetime
from typing import Any
from urllib.parse import urljoin

from pydantic import BaseModel, validator

from config.config_handler import ParametersHandler
from data_types.position_details import PositionDetails

PARAMS: dict[str, Any] = ParametersHandler().get_params()


class Vacancy(BaseModel):
    title: str
    brief_description: str
    full_description: str
    url: str
    position_details: PositionDetails
    date_parsed: datetime | str = datetime.now()

    @validator("title", pre=True)
    def capitalize(cls, value: str) -> str:
        return value.capitalize()

    @validator("url", pre=True)
    def validate_url(cls, url: str) -> str:
        return str(urljoin(PARAMS["base_url"], url))

    class Config:
        allow_extra = False
