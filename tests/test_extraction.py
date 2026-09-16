from app.extraction.pipeline import run_document_pipeline


def test_pipeline_returns_expected_keys():
    output = run_document_pipeline("sample.pdf", b"invoice for contoso")
    assert "file_path" in output
    assert "structured_data" in output
    assert "confidence" in output
    assert output["confidence"] >= 0.0
