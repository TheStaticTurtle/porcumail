import pydantic


class User(pydantic.BaseModel):
    uid: str
    name: str
    email: str
