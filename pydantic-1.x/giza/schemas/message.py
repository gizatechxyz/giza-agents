from pydantic import BaseModel


class Msg(BaseModel):
    """
    Response message model
    """

    msg: str
