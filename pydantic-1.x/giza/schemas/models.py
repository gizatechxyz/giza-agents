from typing import Optional

from pydantic import BaseModel


class Model(BaseModel):
    id: int
    name: Optional[str] = None
    description: Optional[str] = None


class ModelCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ModelUpdate(BaseModel):
    description: str


class ModelList(BaseModel):
    __root__: list[Model]
