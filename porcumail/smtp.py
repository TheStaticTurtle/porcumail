import email.parser
import json
import logging
import smtplib
from io import StringIO
import mailparser

from .config import ConfigInstance
from .models import Message


class SMTPClient:
    def __init__(self, config: ConfigInstance):
        self._log = logging.getLogger(self.__class__.__name__)
        self._config = config


    def _send(self, message):
        errors = {}
        try:
            client = smtplib.SMTP(self._config.smtp.hostname, self._config.smtp.port)

            client.ehlo()
            if self._config.smtp.tls:
                client.starttls()

            if self._config.smtp.username is not None and self._config.smtp.password is not None:
                client.login(self._config.smtp.username, self._config.smtp.password.get_secret_value())


            header_and_parts = message.envelope.content.split(b'\r\n\r\n')
            headers = mailparser.parse_from_bytes(header_and_parts[0]).headers
            parts = b'\r\n\r\n'.join(header_and_parts[1:])

            body  = b'From: \"%s\" <%s>\r\n' % (message.mailing_list.name.encode("utf-8"), message.mailing_list.address.encode("utf-8"))
            body += b'BCC: %s\r\n' % b",".join([recipient.email.encode("utf-8") for recipient in message.mailing_list.recipients])
            for header_key, header_value in headers.items():
                if header_key in ["From", "To", "CC", "BCC", "User-Agent"]:
                    continue
                body += b'%s: %s\r\n' % (header_key.encode("utf-8"), header_value.encode("utf-8"))

            body += b'\r\n\r\n'
            body += parts

            try:
                errors = client.sendmail(
                    from_addr=f"\"{message.mailing_list.name}\" <{message.mailing_list.address}>",
                    to_addrs=[recipient.email for recipient in message.mailing_list.recipients],
                    msg=body
                )
            finally:
                client.quit()

        except smtplib.SMTPRecipientsRefused as e:
            errors = e.recipients
        except (OSError, smtplib.SMTPException) as e:
            self._log.error(f"Server returned an unknown error: {e.__class__}", exc_info=e)

        return errors

    async def handle_message(self, message: Message):
        self._log.info(f"Got an message from {message.envelope.mail_from} to {message.mailing_list.address} for {len(message.mailing_list.recipients)} recipients")
        errors = self._send(message)
        if len(errors.keys()) > 0:
            self._log.warning("Got errors while sending email:")
            for address, error in errors.items():
                self._log.warning(f"  - {address} → {error[0]}, {error[1].decode('utf-8')}")


