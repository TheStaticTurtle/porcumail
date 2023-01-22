# Porcumail

<img src="https://data.thestaticturtle.fr/ShareX/2023/01/22/porcumail.png" height="128">

Porcumail is dead simple tool to manage mailing list. It works by querying a [list provider](#list-providers) and sending the emails via [SMTP](#smtp-config). It also can reconfigure [mail transport agents](#mail-transport-agents) like postfix.

Porcumail uses [LMTP](#lmtp-config) to receive mails from the MTA and forwards them via SMTP to the list members

## SMTP Config
```yaml
smtp:
    hostname: localhost
    port: 25
    tls: false
    username: "porcumail"
    password: "12345678"
```

## LMTP Config
Make sure that the MTA can reach porcumail from this hostname/port combo
```yaml
lmtp:
    hostname: localhost
    port: 10024
```


## List providers
A list provider is a class that implement functions like `get_lists`, `get_list_for_address`, `has_list` and `update_lists`

It returns a `MailingList` object that contains an address and a list of member called `Users`

### LDAP
```yaml
list_provider:
    type: LdapListProvider
    config:
        server:
            uri: ldap://ad.example.com
            bind_dn: "ldap_bind"
            bind_password: ""
        search:
            base: "OU=Mailing Lists,DC=example,DC=com"
            group_attribute_map:
                name: name
                email: mail
            user_attribute_map:
                uuid: sAMAccountName
                name: name
                email: mail
                email_default_uuid_domain: "example.com"
```
 - The `server` block is the configuration for the server address an credentials
 - The `search`/`base` is the base path where user groups can be found
 - The `search`/`base`/`group_attribute_map` is the correspondence between the `name` and `email` to the attributes for the group
 - The `search`/`base`/`user_attribute_map` is the correspondence between the `uuid`, `name` and `email` to the attributes for the user. The `email_default_uuid_domain` will be used if a user does not have the email attribute, it will instead use the format `{uuid}@{email_default_uuid_domain}`


## Mail Transport Agents
A mail transport agent is a class that implements a `reconfigure` function that is called when the mailing list, list is updated.

### Postfix

```yaml
mta:
    type: PostfixMTA
    config:
        paths:
            transport_maps: /etc/porcumail/postfix/transport_maps
            local_recipient_maps: /etc/porcumail/postfix/local_recipient_maps
            virtual_mailbox_maps: /etc/porcumail/postfix/virtual_mailbox_maps
            smtpd_sender_login_maps: /etc/porcumail/postfix/smtpd_sender_login_maps
```
 - The `transport_maps` is the file that tells postfix where to send the message from the recipient address
 - The `local_recipient_maps` is the file that tells postfix that the address is handled by this server
 - The `virtual_mailbox_maps` is the file that tells postfix the path to the address mailbox
 - The `smtpd_sender_login_maps` is the file that tells postfix that a particular user owns an address

