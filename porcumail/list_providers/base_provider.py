import logging
import typing
from typing import Type
import pydantic

from ..models.mailing_list import MailingList


class BaseListProviderConfig(pydantic.BaseModel):
    pass


class BaseListProvider:
    def __init__(self, config: pydantic.BaseModel):
        self._log = logging.getLogger(self.__class__.__name__)
        self._config = config

        self._lists: typing.Dict[str, MailingList] = {}

    @staticmethod
    def get_config_class() -> Type[BaseListProviderConfig]:
        return BaseListProviderConfig

    def get_lists(self) -> typing.List[MailingList]:
        return self._lists.values()

    def get_list_for_address(self, address) -> typing.Optional[MailingList]:
        if self.has_list(address):
            return self._lists[address]
        raise KeyError(f"{address} is not known to the list provider")

    def has_list(self, address) -> bool:
        return address in self._lists

    def update_lists(self):
        raise NotImplementedError()



