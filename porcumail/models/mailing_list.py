import typing
from .user import User
import pydantic


class MailingList(pydantic.BaseModel):
    name: str
    address: str
    recipients: typing.List[User]

    @property
    def porcumail_addresses(self):
        return [self.address]
