import argparse
import json
import logging
import typing

import pydantic
import yaml
from pydantic import SecretStr

from . import list_providers, mta_config


class AppConfigLMTPServerConfig(pydantic.BaseModel):
    hostname: str = "localhost"
    port: int = 10024


class AppConfigSMTPClientConfig(pydantic.BaseModel):
    hostname: str = "localhost"
    port: int = 25
    tls: bool = False
    username: typing.Optional[str]
    password: typing.Optional[SecretStr]
    header_from: typing.Optional[str] = "Porcumail <procumail@example.com>"


class AppConfig(pydantic.BaseModel):
    list_provider: list_providers.AppListProviderConfig
    mta: mta_config.AppMTAgentsConfig
    lmtp: AppConfigLMTPServerConfig = AppConfigLMTPServerConfig()
    smtp: AppConfigSMTPClientConfig = AppConfigSMTPClientConfig()

    class Config:
        json_encoders = {
            type: lambda v: v.__name__
        }


class ConfigInstance:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConfigInstance, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    @staticmethod
    def _load_config(path):
        with open(path) as f:
            config_json = yaml.safe_load(f.read())
        return AppConfig(**config_json)

    def __init__(self):
        self._log = logging.getLogger(self.__class__.__name__)
        self.parser = argparse.ArgumentParser(prog='Porcumail', description='Porcumail mailing list server')
        self.parser.add_argument('-c', '--conf', help="Path to the config file")
        self.args = self.parser.parse_args()
        self._log.info("Parsed args")
        self._log.info(f"  - Config file: {self.args.conf}")

        self._conf = self._load_config(path=self.args.conf)
        self._log.info("Parsed config file successfully")
        self.dump()

        self._log.info(f"Using list provider: {self._conf.list_provider.type.__name__}")
        self._provider_instance = self._conf.list_provider.type(self._conf.list_provider.config)

        self._log.info(f"Using mta agent: {self._conf.mta.type.__name__}")
        self._mta_agent = self._conf.mta.type(self._provider_instance, self._conf)

    def dump(self):
        self._log.debug("Config dump:")
        data = str(yaml.safe_dump(json.loads(self._conf.json())))
        for line in data.splitlines(False):
            self._log.debug("    "+line)

    def get_provider(self) -> list_providers.BaseListProvider:
        return self._provider_instance

    def get_mta(self) -> mta_config.BaseMTA:
        return self._mta_agent

    def __getattr__(self, item):
        if hasattr(self._conf, item):
            return getattr(self._conf, item)
        raise AttributeError(f"{item} is not available in the config")


def load():
    return ConfigInstance()
