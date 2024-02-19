import datetime
from typing import Optional

from pydantic import BaseModel

from giza.utils.enums import Framework, VersionStatus


class VersionCreate(BaseModel):
    size: int
    description: Optional[str] = None
    framework: Framework


class VersionUpdate(BaseModel):
    status: Optional[VersionStatus] = None
    description: Optional[str] = None


class Version(BaseModel):
    version: int
    size: int
    status: VersionStatus
    message: Optional[str] = None
    description: Optional[str] = None
    created_date: datetime.datetime
    last_update: datetime.datetime


class VersionList(BaseModel):
    __root__: list[Version]
