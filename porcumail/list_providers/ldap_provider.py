import json
import logging
import pprint
import typing
from typing import Type
import ldap

import pydantic
from pydantic import SecretStr

from .base_provider import BaseListProvider
from ..models import MailingList, User


class LdapListProviderServerConfig(pydantic.BaseModel):
    uri: str
    bind_dn: str
    bind_password: SecretStr


class LdapListProviderSearchUserAttributesConfig(pydantic.BaseModel):
    uuid: str = "sAMAccountName"
    name: str = "name"
    email: str = "mail"
    email_default_uuid_domain: typing.Optional[str] = None


class LdapListProviderSearchGroupAttributesConfig(pydantic.BaseModel):
    guid: str = "sAMAccountName"
    name: str = "name"
    email: str = "mail"


class LdapListProviderSearchConfig(pydantic.BaseModel):
    base: str
    scope: int = ldap.SCOPE_SUBTREE
    user_attribute_map: LdapListProviderSearchUserAttributesConfig
    group_attribute_map: LdapListProviderSearchGroupAttributesConfig


class LdapListProviderConfig(pydantic.BaseModel):
    server: LdapListProviderServerConfig
    search: LdapListProviderSearchConfig


class LdapListProvider(BaseListProvider):
    def __init__(self, config: LdapListProviderConfig):
        super().__init__(config)
        self._config = config
        self._ldap = ldap.initialize(config.server.uri)
        self._ldap.simple_bind_s(config.server.bind_dn, config.server.bind_password.get_secret_value())
        self._log.info(f"Initialized ldap client to {config.server.uri}")

        self._lists: typing.Dict[str, MailingList] = self._find_groups()

    @staticmethod
    def get_config_class() -> Type[LdapListProviderConfig]:
        return LdapListProviderConfig

    def _find_user_for_dn(self, dn: str) -> typing.Optional[User]:
        results = self._ldap.search_s(
            base=dn,
            filterstr="objectclass=user",
            scope=ldap.SCOPE_BASE
        )
        if len(results) == 0:
            self._log.warning(f"Could not get user: {dn}")
            return None

        result_dn = results[0][0]
        result_attributes = results[0][1]

        if self._config.search.user_attribute_map.uuid not in result_attributes:
            self._log.warning(f"User {result_dn} is missing attribute guid/{self._config.search.user_attribute_map.uuid}")
            return None
        if self._config.search.user_attribute_map.name not in result_attributes:
            self._log.warning(f"User {result_dn} is missing attribute name/{self._config.search.user_attribute_map.name}")
            return None
        if self._config.search.user_attribute_map.email not in result_attributes and self._config.search.user_attribute_map.email_default_uuid_domain is None:
            self._log.warning(f"User {result_dn} is missing attribute email/{self._config.search.user_attribute_map.email} and no default domain set")
            return None

        try:
            uid = result_attributes[self._config.search.user_attribute_map.uuid][0].decode("utf-8")
            name = result_attributes[self._config.search.user_attribute_map.name][0].decode("utf-8")
            email = result_attributes[self._config.search.user_attribute_map.email][0].decode("utf-8") if self._config.search.user_attribute_map.email in result_attributes else f"{uid}@{self._config.search.user_attribute_map.email_default_uuid_domain}"

            return User(
                uid=uid,
                name=name,
                email=email,
            )
        except pydantic.ValidationError as e:
            self._log.error(f"Failed to load user: {e}")
            return None

    def _find_groups(self) -> typing.Dict[str, MailingList]:
        results = self._ldap.search_s(
            base=self._config.search.base,
            scope=self._config.search.scope,
            filterstr=f"(objectclass=group)",
        )

        lists = {}
        for group_dn, group_attributes in results:
            self._log.debug(f"{group_dn}")
            if self._config.search.group_attribute_map.email not in group_attributes or len(group_attributes[self._config.search.group_attribute_map.email]) != 1:
                self._log.warning(f"Group {group_dn} doesn't have the '{self._config.search.group_attribute_map.email}' attribute")
                continue
            if "member" not in group_attributes:
                group_attributes["member"] = []

            if self._config.search.group_attribute_map.email not in group_attributes:
                self._log.warning(f"Group {group_dn} is missing attribute email/{self._config.search.group_attribute_map.email}")
                continue
            if self._config.search.group_attribute_map.name not in group_attributes:
                self._log.warning(f"Group {group_dn} is missing attribute name/{self._config.search.group_attribute_map.name}")
                continue

            users = []
            for group_member in group_attributes["member"]:
                user = self._find_user_for_dn(group_member.decode("utf-8"))
                if user:
                    self._log.debug(f"    {user}")
                    users.append(user)

            address = group_attributes[self._config.search.group_attribute_map.email][0].decode("utf-8")
            name = group_attributes[self._config.search.group_attribute_map.name][0].decode("utf-8")
            lists[address] = MailingList(
                address=address,
                name=name,
                recipients=users
            )

        self._log.info(f"Finished LDAP query, found {len(lists)} lists")

        return lists

    def update_lists(self):
        self._lists = self._find_groups()
