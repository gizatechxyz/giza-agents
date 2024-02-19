import datetime
from typing import Optional

from pydantic import BaseModel


class Proof(BaseModel):
    id: int
    job_id: int
    proving_time: Optional[float] = None
    cairo_execution_time: Optional[float] = None
    metrics: Optional[dict] = None
    created_date: datetime.datetime


class ProofList(BaseModel):
    __root__: list[Proof]
