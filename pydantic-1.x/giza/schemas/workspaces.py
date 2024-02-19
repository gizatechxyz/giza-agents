from typing import Optional

from pydantic import BaseModel


class Workspace(BaseModel):
    url: Optional[str] = None
    status: str
