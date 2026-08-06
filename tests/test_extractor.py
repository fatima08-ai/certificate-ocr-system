from app.core.extractor import extract_fields, is_likely_certificate


def test_extract_fields_finds_name_and_date():
    """extract_fields should correctly parse a well-formed certificate text."""
    sample_text = """TEEROP INSTITUTE
CERTIFICATE OF COMPLETION
This certifies that
Fatima Jawad
has successfully completed the
AI-ML Internship
Teerop Institute 15/07/2026 ABCD-1234
ISSUED BY DATE CERTIFICATE ID"""

    result = extract_fields(sample_text)

    assert result["candidate_name"] == "Fatima Jawad"
    assert result["issue_date"] == "15/07/2026"
    assert result["certificate_number"] == "ABCD-1234"


def test_extract_fields_handles_missing_data():
    """extract_fields should return None for fields it can't find, not crash."""
    result = extract_fields("Some random text with no certificate structure.")
    assert result["candidate_name"] is None
    assert result["issue_date"] is None


def test_is_likely_certificate_detects_strong_phrase():
    assert is_likely_certificate("This certifies that John completed the course") is True


def test_is_likely_certificate_rejects_single_incidental_mention():
    assert is_likely_certificate("I bought a nice certificate frame today at the store") is False


def test_is_likely_certificate_rejects_unrelated_text():
    assert is_likely_certificate("Grocery list: milk, eggs, bread") is False