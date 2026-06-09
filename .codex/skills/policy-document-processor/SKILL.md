---
name: policy-document-processor
description: Use for parsing local policy files, extracting policy timeline/scope/treatment-coding facts, and turning policy documents into source registers and design-card inputs.
---

## Goal

Transform policy files into structured evidence for causal identification.

## Inputs

- Local policy files or folders: `.txt`, `.md`, `.html`, `.csv`, `.json`; optional `.pdf` with `pypdf`, optional `.docx` with `python-docx` when installed.
- Optional study slug under `studies/<slug>/`.
- Optional source URL or manual authority notes.

## Workflow

1. Keep raw files immutable in `studies/<slug>/policy_documents/raw/`.
2. Parse files with the local helper when possible:

```bash
python scripts/causal_policy_cli.py process-policy-doc \
  --input studies/<slug>/policy_documents/raw \
  --study-slug <slug>
```

3. Review `policy_document_summary.md` and `source_register.csv` manually; automated extraction is a first pass.
4. Confirm separate dates: announcement, publication, approval, effective, implementation, revision/expiry.
5. Extract treated units, comparison units, intensity, exemptions, enforcement, and data mapping keys.
6. Push verified facts into `studies/<slug>/design_card.yaml` and `evidence_log.md`.
7. Hand off to `$causal-method-router` after policy facts are sufficiently verified.

## Output

- `studies/<slug>/policy_documents/source_register.csv`
- `studies/<slug>/policy_documents/processed/policy_document_extraction.json`
- `studies/<slug>/policy_documents/processed/policy_document_summary.md`
- treatment coding notes for design card
- unresolved conflicts and manual verification queue

## Guardrails

Do not treat automated text extraction as verified truth. Always label uncertain dates, OCR gaps, unsupported PDF/DOCX parsing, and non-official sources.
