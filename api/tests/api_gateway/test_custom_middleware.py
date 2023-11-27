from api_gateway import custom_middleware


def test_redact():
    assert custom_middleware.redact("1234567890") == "****567890"
    assert custom_middleware.redact("123456") == "123456"
    assert custom_middleware.redact(123456) == 123456
    assert custom_middleware.redact(None) == None
