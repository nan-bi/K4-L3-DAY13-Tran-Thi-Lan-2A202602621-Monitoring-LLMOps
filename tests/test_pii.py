from app.pii import hash_user_id, scrub_text, summarize_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    phone_numbers = (
        "0901234567",
        "090 123 4567",
        "090.123.4567",
        "090-123-4567",
        "+84 90 123 4567",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Contact: {phone_number}")
        assert phone_number not in out
        assert "REDACTED_PHONE_VN" in out


def test_scrub_cccd() -> None:
    out = scrub_text("So CCCD: 001234567890 cua toi")
    assert "001234567890" not in out
    assert "REDACTED_CCCD" in out


def test_scrub_credit_card() -> None:
    cards = (
        "4111 2222 3333 4444",
        "4111-2222-3333-4444",
        "4111222233334444",
    )
    for card in cards:
        out = scrub_text(f"Card number is {card}")
        assert card not in out
        assert "REDACTED_CREDIT_CARD" in out


def test_summarize_text() -> None:
    text = "Email user@test.com for any questions regarding accounts and billing"
    summary = summarize_text(text, max_len=45)
    assert len(summary) <= 48
    assert "user@test.com" not in summary
    assert "REDACTED_EMAIL" in summary


def test_hash_user_id() -> None:
    h1 = hash_user_id("user-123")
    h2 = hash_user_id("user-123")
    h3 = hash_user_id("user-456")
    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 12
