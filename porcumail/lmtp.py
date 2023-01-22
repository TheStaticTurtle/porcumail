import logging

from aiosmtpd.controller import Controller
from aiosmtpd.lmtp import LMTP
from aiosmtpd.smtp import Session, Envelope

from .config import ConfigInstance
from .models import Message
from .smtp import SMTPClient


class LMTPHandler:
    def __init__(self, config: ConfigInstance, smtp_client: SMTPClient):
        self._log = logging.getLogger(self.__class__.__name__)
        self._config = config
        self._smtp_client = smtp_client
        self.message_callbacks = []

    async def handle_MAIL(self, server, session, envelope, address, mail_options):
        envelope.mail_from = address
        envelope.mail_options.extend(mail_options)
        self._log.info(f"Incoming mail from {server.hostname}, from={envelope.mail_from} to={envelope.rcpt_tos}")
        # Eventually sender rejection could be implemented here, responding for an 250 OK for now
        return '250 OK'

    async def handle_DATA(self, server: LMTP, session: Session, envelope: Envelope):
        self._log.info(f"Incoming data from {server.hostname}, from={envelope.mail_from} to={envelope.rcpt_tos} size={len(envelope.content)}")

        provider = self._config.get_provider()
        lists = [provider.get_list_for_address(address) for address in envelope.rcpt_tos if provider.has_list(address)]

        if len(lists) == 0:
            self._log.warning(f"Rejected: None of the recipients tos have been found in the list provider ({envelope.rcpt_tos})")
            return f"550 Porcumail rejected the message because no list was found"

        if len(lists) > 1:
            self._log.warning(f"Rejected: Multiple lists were found in the recipient tos ({envelope.rcpt_tos})")
            return f"550 Porcumail rejected the message because the message was addressed to multiple lists"

        if len(lists[0].recipients) == 0:
            self._log.warning(f"Rejected: List {lists[0]} does not have any recipients")
            return f"550 Porcumail rejected the message because the request list {lists[0]} does not have any recipients"

        message = Message(
            mailing_list=lists[0],
            session=session,
            envelope=envelope,
        )

        await self._smtp_client.handle_message(message)
        return '250 OK'


class LMTPController(Controller):
    """Implementation of the aiosmtpd Controller to create an LMTP mail."""
    def __init__(self, handler: LMTPHandler, config: ConfigInstance):
        self._config = config

        super().__init__(
            handler,
            hostname=self._config.lmtp.hostname,
            port=self._config.lmtp.port
        )

    # Factory creates LMTP instance with custom handler
    def factory(self):
        return LMTP(self.handler)  # custom handler gets passed to __init__
