import logging
from typing import Type
import pydantic

from ..list_providers import BaseListProvider


class BaseMTAConfig(pydantic.BaseModel):
    pass


class BaseMTA:
    def __init__(self, list_provider: BaseListProvider, config: "ConfigInstance"):
        self._log = logging.getLogger(self.__class__.__name__)
        self._list_provider = list_provider
        self._config = config

    @staticmethod
    def get_config_class() -> Type[BaseMTAConfig]:
        return BaseMTAConfig

    def reconfigure(self):
        raise NotImplementedError()



