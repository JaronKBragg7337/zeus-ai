"""Local operating-system credential storage for optional Zeus connectors."""
from __future__ import annotations

import keyring


SERVICE_NAME = "Zeus AI"
SLACK_BOT_TOKEN = "slack_bot_token"
SLACK_APP_TOKEN = "slack_app_token"


def get_secret(name: str) -> str | None:
    try:
        return keyring.get_password(SERVICE_NAME, name)
    except keyring.errors.KeyringError:
        return None


def set_secret(name: str, value: str) -> None:
    value = value.strip()
    if not value:
        return
    try:
        keyring.set_password(SERVICE_NAME, name, value)
    except keyring.errors.KeyringError as error:
        raise RuntimeError(f"Windows Credential Manager could not save the connector credential: {error}") from error


def delete_secret(name: str) -> None:
    try:
        keyring.delete_password(SERVICE_NAME, name)
    except keyring.errors.PasswordDeleteError:
        return
    except keyring.errors.KeyringError:
        return
