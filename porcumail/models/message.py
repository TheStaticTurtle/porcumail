import typing
from pydantic import BaseModel, EmailStr
from aiosmtpd.smtp import Session, Envelope, SMTP
from .mailing_list import MailingList


class Message(BaseModel):
    mailing_list: MailingList

    session: Session
    envelope: Envelope

    class Config:
        arbitrary_types_allowed = True
