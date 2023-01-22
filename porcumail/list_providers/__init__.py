import typing
from typing import Union

import pydantic
from pydantic import validator

from .base_provider import BaseListProvider
from .ldap_provider import LdapListProvider

providers = [
    LdapListProvider
]


class AppListProviderConfig(pydantic.BaseModel):
    type: Union[str, typing.Callable]
    config: Union[dict, object]

    @validator('type')
    def config_type_valid(cls, value, values, **kwargs):
        for provider in providers:
            if provider.__name__ == value:
                return provider
        raise ValueError(f'Provider type is invalid')

    @validator('config')
    def config_right_type(cls, value, values, **kwargs):
        if "type" not in values:
            raise ValueError(f'provider type is missing')

        provider_conf = None
        for provider in providers:
            if provider == values["type"]:
                provider_conf = provider
        provider_conf_class = provider_conf.get_config_class()

        return provider_conf_class(**value)
