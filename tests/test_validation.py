from app.extraction.validation import validate_extraction


def test_validation_passes_for_valid_payload():
    result = validate_extraction({"vendor": "Contoso"})
    assert result["valid"] is True
    assert result["issues"] == []


def test_validation_flags_missing_vendor():
    result = validate_extraction({})
    assert result["valid"] is False
    assert "Missing vendor" in result["issues"]
