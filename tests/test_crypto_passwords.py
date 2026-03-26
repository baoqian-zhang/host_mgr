import string

import pytest

from host_mgr.crypto.passwords import generate_root_password

_ALLOWED_SPECIAL = "!@#$%^&*()-_=+[]{};:,.?"
_ALPHABET = (
    string.ascii_letters
    + string.digits
    + _ALLOWED_SPECIAL
)


def test_generate_root_password_rejects_short_length():
    """长度小于 16 时必须抛出 ValueError，避免过短口令不符合安全下限。"""
    with pytest.raises(ValueError, match="length must be >= 16"):
        generate_root_password(15)


@pytest.mark.parametrize("length", [16, 24, 32])
def test_generate_root_password_length_and_charset(length):
    """合法长度下返回指定长度字符串，且含大小写、数字、规定特殊字符，字符均在允许集内、无空白。"""
    pwd = generate_root_password(length)
    assert isinstance(pwd, str)
    assert len(pwd) == length
    assert any(c in string.ascii_lowercase for c in pwd)
    assert any(c in string.ascii_uppercase for c in pwd)
    assert any(c in string.digits for c in pwd)
    assert any(c in _ALLOWED_SPECIAL for c in pwd)
    assert all(c in _ALPHABET for c in pwd)
    assert not pwd.isspace()
    assert " " not in pwd
