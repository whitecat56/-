from pharmalink.core.security import create_token, decode_token, hash_password, verify_password


def test_password_and_token():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed)
    token = create_token("42")
    assert decode_token(token) == "42"
