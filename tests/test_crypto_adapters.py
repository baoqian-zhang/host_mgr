import pytest
from cryptography.fernet import Fernet

from host_mgr.crypto.adapters import FernetEncryptor


def test_fernet_encryptor_round_trip():
    """使用合法 Fernet key 时，加密后再解密应与原文一致，且密文与明文不同。"""
    key = Fernet.generate_key().decode("utf-8")
    enc = FernetEncryptor(key)
    plaintext = "secret-root-password"
    ciphertext = enc.encrypt(plaintext)
    assert ciphertext != plaintext
    assert enc.decrypt(ciphertext) == plaintext


def test_fernet_encryptor_invalid_ciphertext_raises_value_error():
    """用另一把 key 生成的密文无法用当前 key 解密，应抛出带明确信息的 ValueError。"""
    key = Fernet.generate_key().decode("utf-8")
    other_key = Fernet.generate_key().decode("utf-8")
    enc = FernetEncryptor(key)
    ciphertext_from_other_key = FernetEncryptor(other_key).encrypt("payload")
    with pytest.raises(ValueError, match="ciphertext cannot be decrypted"):
        enc.decrypt(ciphertext_from_other_key)
