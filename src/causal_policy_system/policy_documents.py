from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import csv
import hashlib
import json
import mimetypes
import re
import textwrap
import yaml


class _HTMLTextExtractor(HTMLParser):
    """Small dependency-free HTML-to-text extractor for official web pages."""

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
        if tag in {"p", "br", "li", "tr", "h1", "h2", "h3", "div"}:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
        if tag in {"p", "li", "tr", "h1", "h2", "h3"}:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self._parts.append(data)

    def text(self) -> str:
        raw = "".join(self._parts)
        lines = [re.sub(r"\s+", " ", line).strip() for line in raw.splitlines()]
        return "\n".join(line for line in lines if line)


@dataclass
class PolicyDocumentRecord:
    source_id: str
    title: str
    source_type: str
    source_url: str | None
    local_path: str | None
    content_sha256: str
    captured_at: str
    authority_score: int
    issuing_agency: str | None
    jurisdiction: str | None
    publication_date: str | None
    effective_date: str | None
    policy_action: str | None
    target_population: str | None
    treatment_definition: str | None
    treatment_intensity: str | None
    outcomes_mentioned: list[str]
    timeline: list[dict[str, str]]
    key_quotes: list[str]
    extraction_warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_DATE_PATTERNS = [
    re.compile(r"(?P<date>20\d{2}[-/.年]\s?\d{1,2}[-/.月]\s?\d{1,2}日?)"),
    re.compile(r"(?P<date>20\d{2}[-/.年]\s?\d{1,2}月?)"),
    re.compile(r"(?P<date>20\d{2}\s?年)"),
    re.compile(r"(?P<date>\b20\d{2}-\d{1,2}-\d{1,2}\b)"),
]
_AGENCY_HINTS = [
    "国务院", "国家发展改革委", "发展改革委", "财政部", "教育部", "生态环境部", "交通运输部", "工业和信息化部",
    "市场监管总局", "人民政府", "委员会", "办公厅", "Department", "Ministry", "Commission", "Agency", "Office",
]
_JURISDICTION_HINTS = [
    "全国", "中国", "北京市", "上海市", "深圳市", "广州市", "杭州市", "成都市", "省", "市", "县", "州",
    "United States", "California", "European Union", "EU",
]
_ACTION_HINTS = [
    "实施", "施行", "执行", "发布", "印发", "通知", "办法", "条例", "规定", "试点", "补贴", "限制", "禁止", "征收", "减免", "监管", "治理",
    "effective", "implemented", "issued", "adopted", "ban", "subsidy", "tax", "mandate", "pilot", "regulation",
]
_OUTCOME_HINTS = {
    "pollution": ["PM2.5", "污染", "空气质量", "排放", "emissions", "AQI"],
    "sales": ["销量", "销售", "sales", "registrations"],
    "employment": ["就业", "工资", "岗位", "employment", "wage", "jobs"],
    "education": ["成绩", "入学", "辍学", "education", "enrollment", "test score"],
    "health": ["健康", "住院", "死亡", "hospital", "mortality", "health"],
    "market_entry": ["进入", "退出", "商家", "firm entry", "market entry", "exit"],
}
_SUPPORTED_SUFFIXES = {".txt", ".md", ".rst", ".html", ".htm", ".json", ".csv", ".pdf", ".docx"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_date(raw: str | None) -> str | None:
    if not raw:
        return None
    s = raw.strip().replace("年", "-").replace("月", "-").replace("日", "")
    s = s.replace("/", "-").replace(".", "-")
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    parts = s.split("-")
    try:
        if len(parts) == 3:
            y, m, d = parts
            return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
        if len(parts) == 2:
            y, m = parts
            return f"{int(y):04d}-{int(m):02d}"
    except ValueError:
        return raw.strip()
    if re.fullmatch(r"20\d{2}", s):
        return s
    return raw.strip()


def strip_html(html: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(html)
    return parser.text()


def read_policy_text(path: str | Path) -> tuple[str, bytes, str]:
    """Read a local policy file and return text, raw bytes, and source type.

    Dependency-free formats: .txt, .md, .html, .json, .csv. PDF requires optional `pypdf`; DOCX requires optional `python-docx`.
    """
    p = Path(path)
    raw = p.read_bytes()
    suffix = p.suffix.lower()
    if suffix in {".txt", ".md", ".rst"}:
        return raw.decode("utf-8", errors="replace"), raw, "text"
    if suffix in {".html", ".htm"}:
        return strip_html(raw.decode("utf-8", errors="replace")), raw, "html"
    if suffix == ".json":
        data = json.loads(raw.decode("utf-8", errors="replace"))
        return json.dumps(data, ensure_ascii=False, indent=2), raw, "json"
    if suffix == ".csv":
        return raw.decode("utf-8", errors="replace"), raw, "csv"
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("PDF parsing requires optional dependency `pypdf`. Install requirements-optional.txt.") from exc
        reader = PdfReader(str(p))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text, raw, "pdf"
    if suffix == ".docx":
        try:
            from docx import Document  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("DOCX parsing requires optional dependency `python-docx`. Install requirements-optional.txt.") from exc
        doc = Document(str(p))
        text = "\n".join(paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip())
        return text, raw, "docx"
    guessed = mimetypes.guess_type(str(p))[0] or "unknown"
    return raw.decode("utf-8", errors="replace"), raw, guessed


def fetch_policy_url(url: str, out_dir: str | Path, *, timeout: int = 30) -> dict[str, Any]:
    """Fetch a policy URL and save raw bytes plus extracted text.

    Use this only for user-approved source capture. Codex should prefer official sources and
    keep evidence logs; this helper does not decide whether a source is substantively correct.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    req = Request(url, headers={"User-Agent": "causal-policy-codex-system/0.2"})
    with urlopen(req, timeout=timeout) as resp:  # noqa: S310 - user-initiated source capture
        raw = resp.read()
        final_url = resp.geturl()
        content_type = resp.headers.get("content-type", "")
    digest = sha256_bytes(raw)
    ext = ".html" if "html" in content_type else mimetypes.guess_extension(content_type.split(";")[0].strip()) or ".bin"
    raw_path = out / f"{digest[:16]}{ext}"
    raw_path.write_bytes(raw)
    text = strip_html(raw.decode("utf-8", errors="replace")) if "html" in content_type else raw.decode("utf-8", errors="replace")
    text_path = out / f"{digest[:16]}.txt"
    text_path.write_text(text, encoding="utf-8")
    return {
        "url": url,
        "final_url": final_url,
        "content_type": content_type,
        "sha256": digest,
        "raw_path": str(raw_path),
        "text_path": str(text_path),
        "captured_at": _now_iso(),
    }


def score_source_authority(source_url: str | None, local_path: str | None = None) -> int:
    """0–5 source-priority heuristic. It is not a truth score."""
    if not source_url:
        return 2 if local_path else 0
    host = urlparse(source_url).netloc.lower()
    if host.endswith(".gov") or ".gov." in host or host.endswith(".gov.cn") or host.endswith("gov.cn"):
        return 5
    if any(x in host for x in ["npc.gov", "gov.uk", "europa.eu", "oecd.org", "worldbank.org", "imf.org", "stats", "data."]):
        return 4
    if host.endswith(".edu") or ".edu." in host or host.endswith(".org"):
        return 3
    if any(x in host for x in ["reuters", "apnews", "bloomberg", "ft.com", "caixin", "people.com.cn", "xinhuanet"]):
        return 2
    return 1


def _find_labeled_date(text: str, labels: Iterable[str]) -> str | None:
    label_pattern = "|".join(re.escape(label) for label in labels)
    # Capture a date close to explicit labels such as 发布日期 / 实施日期.
    pattern = re.compile(rf"(?:{label_pattern})\s*[:：]?\s*(20\d{{2}}[-/.年]\s?\d{{1,2}}[-/.月]\s?\d{{1,2}}日?|20\d{{2}}[-/.年]\s?\d{{1,2}}月?|20\d{{2}}\s?年)", re.IGNORECASE)
    match = pattern.search(text)
    if match:
        return normalize_date(match.group(1))
    return None


def _pick_labeled_line(text: str, labels: Iterable[str]) -> str | None:
    labels = list(labels)
    for line in [x.strip() for x in text.splitlines() if x.strip()]:
        if any(line.lower().startswith(label.lower()) for label in labels):
            return line[:220]
    for line in [x.strip() for x in text.splitlines() if x.strip()]:
        if any(label.lower() in line.lower() for label in labels):
            return line[:220]
    return None


def _find_dates_with_context(text: str) -> list[dict[str, str]]:
    timeline: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for pattern in _DATE_PATTERNS:
        for match in pattern.finditer(text):
            raw = match.group("date")
            norm = normalize_date(raw) or raw
            start = max(0, match.start() - 45)
            end = min(len(text), match.end() + 60)
            context = re.sub(r"\s+", " ", text[start:end]).strip()
            key = (norm, context)
            if key not in seen:
                timeline.append({"date": norm, "context": context})
                seen.add(key)
            if len(timeline) >= 20:
                return timeline
    return timeline


def _pick_line(text: str, hints: Iterable[str]) -> str | None:
    for line in [x.strip() for x in text.splitlines() if x.strip()]:
        if any(h.lower() in line.lower() for h in hints):
            return line[:220]
    return None


def _guess_title(text: str, fallback: str | None = None) -> str:
    for line in [x.strip("# ").strip() for x in text.splitlines() if x.strip()][:20]:
        if 6 <= len(line) <= 160 and not re.fullmatch(r"[\d\W_]+", line):
            return line
    return fallback or "Untitled policy document"


def _extract_date_by_context(timeline: list[dict[str, str]], words: Iterable[str]) -> str | None:
    words_lower = [w.lower() for w in words]
    for item in timeline:
        context = item["context"].lower()
        if any(w in context for w in words_lower):
            return item["date"]
    return timeline[0]["date"] if timeline else None


def _extract_outcomes(text: str) -> list[str]:
    low = text.lower()
    return [label for label, hints in _OUTCOME_HINTS.items() if any(h.lower() in low for h in hints)]


def _extract_key_quotes(text: str, max_quotes: int = 5) -> list[str]:
    action_re = re.compile("|".join(re.escape(x) for x in _ACTION_HINTS), flags=re.IGNORECASE)
    quotes: list[str] = []
    for line in [x.strip() for x in text.splitlines() if x.strip()]:
        if action_re.search(line) or any(x in line for x in ["适用", "对象", "范围", "补贴", "限制", "试点", "effective"]):
            quotes.append(textwrap.shorten(line, width=260, placeholder="…"))
        if len(quotes) >= max_quotes:
            break
    return quotes


def extract_policy_metadata(
    text: str,
    *,
    source_url: str | None = None,
    local_path: str | None = None,
    source_type: str = "text",
    source_id: str | None = None,
) -> PolicyDocumentRecord:
    cleaned = re.sub(r"\r\n?", "\n", text).strip()
    digest = sha256_bytes(cleaned.encode("utf-8", errors="replace"))
    timeline = _find_dates_with_context(cleaned)
    agency_line = _pick_labeled_line(cleaned, ["发布机构", "发文机关", "制定机关", "发布部门", "issuing agency", "issuer"]) or _pick_line(cleaned, _AGENCY_HINTS)
    action_line = _pick_labeled_line(cleaned, ["政策措施", "主要内容", "为", "自", "policy action", "action"]) or _pick_line("\n".join(cleaned.splitlines()[1:]), _ACTION_HINTS)
    publication_date = _find_labeled_date(cleaned, ["发布日期", "公布日期", "印发日期", "发布时间", "published", "issued"])
    effective_date = _find_labeled_date(cleaned, ["实施日期", "生效日期", "施行日期", "执行日期", "effective", "implementation"])
    warnings: list[str] = []
    if not timeline:
        warnings.append("No date detected; verify publication and effective dates manually.")
    if not agency_line:
        warnings.append("No issuing agency detected; verify source authority manually.")
    if not action_line:
        warnings.append("No policy action line detected; define treatment manually.")
    if source_url and score_source_authority(source_url) < 3:
        warnings.append("Source is not clearly official/institutional; find a primary source before causal analysis.")
    return PolicyDocumentRecord(
        source_id=source_id or digest[:12],
        title=_guess_title(cleaned, fallback=Path(local_path).name if local_path else None),
        source_type=source_type,
        source_url=source_url,
        local_path=local_path,
        content_sha256=digest,
        captured_at=_now_iso(),
        authority_score=score_source_authority(source_url, local_path),
        issuing_agency=agency_line,
        jurisdiction=_pick_labeled_line(cleaned, ["适用范围", "适用地区", "实施范围", "jurisdiction", "scope"]) or _pick_line(cleaned, _JURISDICTION_HINTS),
        publication_date=publication_date or _extract_date_by_context(timeline, ["发布", "印发", "公布", "通知", "issued", "published", "adopted"]),
        effective_date=effective_date or _extract_date_by_context(timeline, ["施行", "实施", "执行", "生效", "effective", "implemented", "comes into force"]),
        policy_action=action_line,
        target_population=_pick_line(cleaned, ["对象", "适用", "范围", "target", "eligible", "covered"]),
        treatment_definition=action_line,
        treatment_intensity=_pick_line(cleaned, ["标准", "额度", "比例", "强度", "上限", "下限", "amount", "rate", "limit"]),
        outcomes_mentioned=_extract_outcomes(cleaned),
        timeline=timeline[:10],
        key_quotes=_extract_key_quotes(cleaned),
        extraction_warnings=warnings,
    )


def record_from_file(path: str | Path, *, source_url: str | None = None) -> PolicyDocumentRecord:
    text, raw, source_type = read_policy_text(path)
    record = extract_policy_metadata(text, source_url=source_url, local_path=str(path), source_type=source_type)
    record.content_sha256 = sha256_bytes(raw)
    return record


def iter_policy_files(paths: Iterable[str | Path]) -> list[Path]:
    files: list[Path] = []
    for item in paths:
        p = Path(item)
        if p.is_dir():
            files.extend(
                child for child in sorted(p.rglob("*"))
                if child.is_file() and child.suffix.lower() in _SUPPORTED_SUFFIXES and not child.name.startswith(".")
            )
        elif p.is_file():
            files.append(p)
        else:
            raise FileNotFoundError(f"Policy input not found: {p}")
    return files


def process_policy_documents(paths: Iterable[str | Path], *, jurisdiction: str | None = None) -> list[PolicyDocumentRecord]:
    records: list[PolicyDocumentRecord] = []
    for i, path in enumerate(iter_policy_files(paths), start=1):
        record = record_from_file(path)
        record.source_id = f"POL-{i:03d}" if not record.source_id else record.source_id
        if jurisdiction:
            record.jurisdiction = jurisdiction
        records.append(record)
    return records


def write_record_yaml(record: PolicyDocumentRecord, output: str | Path) -> None:
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(yaml.safe_dump(record.to_dict(), allow_unicode=True, sort_keys=False), encoding="utf-8")


def write_records_json(path: str | Path, records: Iterable[PolicyDocumentRecord]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps([r.to_dict() for r in records], ensure_ascii=False, indent=2), encoding="utf-8")


def append_evidence_log_csv(record: PolicyDocumentRecord, csv_path: str | Path) -> None:
    p = Path(csv_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "source_id": record.source_id,
        "title": record.title,
        "source_type": record.source_type,
        "authority_score": record.authority_score,
        "source_url": record.source_url or "",
        "local_path": record.local_path or "",
        "publication_date": record.publication_date or "",
        "effective_date": record.effective_date or "",
        "issuing_agency": record.issuing_agency or "",
        "jurisdiction": record.jurisdiction or "",
        "content_sha256": record.content_sha256,
        "captured_at": record.captured_at,
        "status": "needs_manual_verification" if record.extraction_warnings else "parsed",
        "notes": "; ".join(record.extraction_warnings),
    }
    write_header = not p.exists()
    with p.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def write_source_register_csv(path: str | Path, records: Iterable[PolicyDocumentRecord]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source_id", "title", "source_type", "authority_score", "source_url", "local_path",
        "publication_date", "effective_date", "issuing_agency", "jurisdiction", "content_sha256",
        "captured_at", "policy_action", "target_population", "treatment_definition",
        "treatment_intensity", "extraction_warnings",
    ]
    with p.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            d = record.to_dict()
            writer.writerow({k: ", ".join(d[k]) if isinstance(d.get(k), list) else d.get(k, "") for k in fieldnames})


def _safe_cell(value: object, max_len: int = 100) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        value = ", ".join(str(v) for v in value)
    return str(value).replace("|", "/").replace("\n", " ")[:max_len]


def records_to_markdown(records: Iterable[PolicyDocumentRecord]) -> str:
    records = list(records)
    if not records:
        return "# Policy document extraction summary\n\nNo files processed.\n"
    lines = ["# Policy document extraction summary", ""]
    lines.append("| source_id | title | authority | issuer | jurisdiction | publication | effective | warnings |")
    lines.append("|---|---|---:|---|---|---|---|---|")
    for r in records:
        lines.append(
            f"| {r.source_id} | {_safe_cell(r.title, 80)} | {r.authority_score} | "
            f"{_safe_cell(r.issuing_agency, 80)} | {_safe_cell(r.jurisdiction, 80)} | "
            f"{_safe_cell(r.publication_date)} | {_safe_cell(r.effective_date)} | {_safe_cell(r.extraction_warnings, 140)} |"
        )
    lines.append("\n## Treatment-coding hints\n")
    for r in records:
        effective = r.effective_date or "DATE_TO_VERIFY"
        action = r.treatment_definition or r.policy_action or "POLICY_ACTION_TO_CODE"
        pop = r.target_population or "AFFECTED_UNITS_TO_VERIFY"
        lines.append(f"- **{r.source_id}**: treated=1 for `{pop}` after `{effective}`; action/intensity: `{action}`")
    lines.append("\n## Key quotes / locators for manual verification\n")
    for r in records:
        lines.append(f"### {r.source_id}: {r.title}")
        if r.key_quotes:
            for quote in r.key_quotes:
                lines.append(f"- {quote}")
        else:
            lines.append("- No key quote detected; inspect the original manually.")
    return "\n".join(lines) + "\n"


def policy_source_plan(question: str) -> dict[str, Any]:
    q = question.lower()
    domains: list[str] = []
    if any(x in q for x in ["污染", "pm2.5", "排放", "环保", "environment", "emissions"]):
        domains.append("environment")
    if any(x in q for x in ["交通", "限行", "拥堵", "transport", "vehicle"]):
        domains.append("transport")
    if any(x in q for x in ["补贴", "税", "财政", "subsidy", "tax"]):
        domains.append("fiscal/industrial policy")
    if any(x in q for x in ["教育", "学校", "education", "school"]):
        domains.append("education")
    if any(x in q for x in ["平台", "商家", "algorithm", "platform"]):
        domains.append("platform governance")
    if not domains:
        domains.append("general policy")
    return {
        "question": question,
        "likely_domains": domains,
        "priority_sources": [
            "official policy text or gazette entry",
            "implementation notice, pilot list, or enforcement guidance",
            "data portal/statistical table for outcome and covariates",
            "secondary source only for lead discovery, not final evidence",
        ],
        "search_strings": [
            f"{question} 发布机构 通知 办法 条例 公告 公报 实施",
            f"{question} 试点 名单 生效 日期 执行 适用范围",
            f"{question} official gazette regulation effective date implementation dataset",
        ],
        "must_extract": [
            "publication_date", "effective_date", "issuing_agency", "jurisdiction", "covered_units",
            "eligibility_or_threshold", "treatment_intensity", "exemptions", "amendments_or_repeal",
            "outcome_data_source", "covariate_data_source",
        ],
        "recommended_folder": "studies/<slug>/policy_documents/{raw,processed}",
        "next_command": "python scripts/causal_policy_cli.py process-policy-doc --input studies/<slug>/policy_documents/raw --study-slug <slug>",
    }
