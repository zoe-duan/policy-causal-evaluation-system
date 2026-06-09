from pathlib import Path

from causal_policy_system.policy_documents import (
    append_evidence_log_csv,
    policy_source_plan,
    process_policy_documents,
    record_from_file,
    records_to_markdown,
    write_source_register_csv,
)


SAMPLE = Path("examples/policy_documents/sample_transport_restriction_policy.md")


def test_policy_document_sample_parse():
    record = record_from_file(SAMPLE)
    assert "限行" in (record.title + " " + (record.policy_action or ""))
    assert record.publication_date == "2021-04-01"
    assert record.effective_date == "2021-05-01"
    assert "pollution" in record.outcomes_mentioned
    assert record.content_sha256


def test_policy_source_plan_mentions_official_sources():
    plan = policy_source_plan("某城市限行政策是否降低 PM2.5？")
    assert "environment" in plan["likely_domains"]
    assert any("official" in x for x in plan["priority_sources"])
    assert plan["search_strings"]


def test_policy_document_outputs(tmp_path):
    records = process_policy_documents([SAMPLE], jurisdiction="北京市")
    assert len(records) == 1
    assert records[0].jurisdiction == "北京市"
    md = records_to_markdown(records)
    assert "Treatment-coding hints" in md
    csv_path = tmp_path / "source_register.csv"
    write_source_register_csv(csv_path, records)
    assert "source_id" in csv_path.read_text(encoding="utf-8")
    evidence_path = tmp_path / "evidence.csv"
    append_evidence_log_csv(records[0], evidence_path)
    assert records[0].content_sha256 in evidence_path.read_text(encoding="utf-8")
