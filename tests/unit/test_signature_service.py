# Team member: Vinayak Shivam Gupta (@vsh2504)

import hashlib
import hmac

from app.services.signature_service import verify_signature


def test_accepts_valid_signature() -> None:
    body = b'{"action":"opened"}'
    digest = hmac.new(b"secret", body, hashlib.sha256).hexdigest()

    assert verify_signature(body, f"sha256={digest}", "secret") is True


def test_rejects_tampered_body() -> None:
    digest = hmac.new(b"secret", b"original", hashlib.sha256).hexdigest()

    assert verify_signature(b"tampered", f"sha256={digest}", "secret") is False
