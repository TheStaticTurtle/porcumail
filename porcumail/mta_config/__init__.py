import typing
from typing import Union

import pydantic
from pydantic import validator

from .base_agent import BaseMTA
from .postfix_agent import PostfixMTA

agents = [
    PostfixMTA
]


class AppMTAgentsConfig(pydantic.BaseModel):
    type: Union[str, typing.Callable]
    config: Union[dict, object]

    @validator('type')
    def config_type_valid(cls, value, values, **kwargs):
        for agent in agents:
            if agent.__name__ == value:
                return agent
        raise ValueError(f'Agent type is invalid')

    @validator('config')
    def config_right_type(cls, value, values, **kwargs):
        if "type" not in values:
            raise ValueError(f'Agent type is missing')

        agents_conf = None
        for agent in agents:
            if agent == values["type"]:
                agents_conf = agent
        agent_conf_class = agents_conf.get_config_class()

        return agent_conf_class(**value)
