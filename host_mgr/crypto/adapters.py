from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.utils.module_loading import import_string


class FernetEncryptor:
    def __init__(self, key: str):
        self.key = key
        # Validate key early (must be urlsafe base64-encoded 32-byte key)
        Fernet(key.encode("utf-8"))

    def encrypt(self, plaintext: str) -> str:
        token = Fernet(self.key.encode("utf-8")).encrypt(plaintext.encode("utf-8"))
        return token.decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        try:
            raw = Fernet(self.key.encode("utf-8")).decrypt(ciphertext.encode("utf-8"))
        except InvalidToken as e:
            raise ValueError("ciphertext cannot be decrypted with current key") from e
        return raw.decode("utf-8")


def get_host_password_encryptor():
    """
    简化版“适配器”：通过 settings 选择加密实现，并注入 key。

    - `HOST_PASSWORD_ENCRYPTOR`: 加密器类的 dotted path（默认 FernetEncryptor）
    - `HOST_PASSWORD_ENCRYPTION_KEY`: 加密 key（必填）
    """

    cls_path = getattr(
        settings,
        "HOST_PASSWORD_ENCRYPTOR",
        "host_mgr.crypto.adapters.FernetEncryptor",
    )
    key = getattr(settings, "HOST_PASSWORD_ENCRYPTION_KEY", None)
    if not key:
        raise RuntimeError("HOST_PASSWORD_ENCRYPTION_KEY is required")

    cls = import_string(cls_path)
    return cls(key=key)
