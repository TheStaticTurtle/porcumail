import time
import coloredlogs
import logging
import sys

import schedule
from . import config, lmtp, smtp

coloredlogs.install(stream=sys.stdout, level=logging.INFO, isatty=True)
logging.getLogger("mail.log").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)


if __name__ == '__main__':
    conf = config.load()

    smtp_client = smtp.SMTPClient(conf)

    handler = lmtp.LMTPHandler(conf, smtp_client)
    controller = lmtp.LMTPController(handler, conf)

    @schedule.repeat(schedule.every(15).minutes)
    def update_lists():
        logging.getLogger("schedule").info("Executing reload")
        conf.get_provider().update_lists()
        conf.get_mta().reconfigure()

    controller.start()

    while True:
        schedule.run_pending()
        time.sleep(1)

    controller.stop()

