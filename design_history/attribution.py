"""Which model drew a design, as far as the history can say.

Three kinds of evidence, strongest first:

``measured``  the resource ledger (``.llm_resource_tally``) names this commit and
              lists the models a session used. Present from about August 2026.
``declared``  a ``Co-Authored-By`` trailer in the commit message.
``message``   no trailer, but the subject or body names a model ("Big GPT 5.6
              Alice improvement"). Weaker: it may be a plan, not a signature.
``curated``   `authors.yaml` says who drew the lines of a file at a commit (a
              person's drawing committed by an agent session). It outranks
              everything below, for those files only.
``unsigned``  no ledger row, no model trailer and no model named, from Jon's
              account or an agent's: GPT (Jon's rule, 2026-10-25). Claude Code
              signs its commits and GPT mostly does not: of the ledger's
              measured commits, 42 of 908 Claude-only ones have no trailer and
              10 of 11 GPT-only ones have none. Jon's own hand commits (a
              pointer bump, a format run) look the same, so it stays a guess.
``unknown``   nothing says.

A commit is evidence about the session that made it, not proof that one model
drew every pixel: a session may use several, and a later commit may polish
earlier art. The result keeps the basis, so a reader can discount it.
"""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

from .store import Commit

# The email is optional ("Co-Authored-By: Claude Opus 5.5" is a trailer too).
_TRAILER = re.compile(r"^co-authored-by:\s*([^<\r\n]+?)\s*(?:<[^>]*>)?\s*$", re.IGNORECASE | re.MULTILINE)
# A trailer names a MODEL only if it says so; a human co-author is not one.
_AI_NAME = re.compile(
    r"\b(claude|anthropic|gpt|openai|codex|gemini|copilot|opus|sonnet|haiku|fable|qwen|llama|mistral|deepseek)", re.IGNORECASE
)
_MENTION = re.compile(
    r"\b(GPT[- ]?\d+(?:\.\d+)?(?:\s+(?:Sol|Astra|Thinking))?|Claude\s+(?:Opus|Sonnet|Haiku|Fable)\s*[\d.]*|"
    r"Opus\s*\d[\d.]*|Sonnet\s*\d[\d.]*|Fable\s*\d[\d.]*|Codex)\b",
    re.IGNORECASE,
)
_HUMAN_AUTHORS = {"joncrall", "jon crall", "jon.crall"}


@dataclasses.dataclass(frozen=True)
class Attribution:
    models: tuple[str, ...]
    basis: str  # curated | measured | declared | message | unsigned | unknown
    note: str = ""

    def label(self) -> str:
        if self.models:
            how = "no trailer" if self.basis == "unsigned" else self.basis
            return ", ".join(self.models) + ("" if self.basis == "measured" else f" ({how})")
        return self.note or self.basis


def _clean(name: str) -> str:
    # "Claude Opus 4.8 (1M context)" -> "Claude Opus 4.8": the context window is
    # a deployment detail, not a different model.
    name = re.sub(r"\s*\((?:\d+\w*\s*)?context\)", "", name)
    # "Claude Opus 4.8 [1M]": the bracketed window is the same deployment detail.
    name = re.sub(r"\s*\[\d+\w*\]", "", name)
    # "GPT-5.6 Thinking [noreply@openai.com](mailto:...)": an email written as
    # a Markdown link is not part of the name; nor is the model's id in
    # parentheses ("Claude Opus 5 (claude-opus-5)").
    name = re.sub(r"\s*\[[^\]]*\]\(mailto:[^)]*\)", "", name)
    name = re.sub(r"\s*\((?:claude|gpt)-[^)]*\)", "", name, flags=re.IGNORECASE)
    return normal(name)


def normal(name: str) -> str:
    """One spelling per model: "OpenAI GPT-5.6 Thinking" and "GPT 5.6
    Thinking" are "GPT-5.6 Thinking"."""
    name = re.sub(r"\s+", " ", name).strip()
    name = re.sub(r"^(?:OpenAI|Anthropic) ", "", name)
    return re.sub(r"^GPT[ -]?(?=\d)", "GPT-", name, flags=re.IGNORECASE)


def _add(seen: list[str], name: str) -> None:
    """Append `name` unless an equal one (ignoring case) is already there."""
    if name.lower() not in {existing.lower() for existing in seen}:
        seen.append(name)


def pretty(model: str) -> str:
    """``claude-opus-5-5`` -> ``Claude Opus 5.5``; ``gpt-5.5`` -> ``GPT-5.5``.
    Names it does not recognise pass through unchanged."""
    m = re.fullmatch(r"claude-(opus|sonnet|haiku|fable)-(\d+)(?:-(\d+))?(?:-\d{8})?", model)
    if m:
        version = m.group(2) + (f".{m.group(3)}" if m.group(3) else "")
        return f"Claude {m.group(1).title()} {version}"
    m = re.fullmatch(r"gpt-(\d+(?:\.\d+)?)(?:-(.+))?", model)
    if m:
        return f"GPT-{m.group(1)}" + (f" {m.group(2).replace('-', ' ')}" if m.group(2) else "")
    return model


def _measured(commit: Commit, ledger: dict[str, list[dict]]) -> list[str]:
    models: list[str] = []
    for row in ledger.get(commit.sha) or []:
        for model in row.get("m", []):
            if model.startswith("<") or model == "?":
                continue  # "<synthetic>": a ledger placeholder, not a model
            model = pretty(model)
            if model not in models:
                models.append(model)
    return models


def _trailers(commit: Commit) -> list[str]:
    trailers: list[str] = []
    for name in _TRAILER.findall(commit.body):
        name = _clean(name)
        if _AI_NAME.search(name):
            _add(trailers, name)
    return trailers


def _mentions(commit: Commit) -> list[str]:
    mentioned: list[str] = []
    for hit in _MENTION.findall(commit.subject + "\n" + commit.body):
        _add(mentioned, normal(hit))
    return mentioned


def signed_models(commit: Commit, ledger: dict[str, list[dict]]) -> list[str]:
    """The models that signed `commit`: its ledger rows and trailers."""
    out: list[str] = []
    for name in [*_measured(commit, ledger), *_trailers(commit)]:
        _add(out, name)
    return out


def named_models(commit: Commit, ledger: dict[str, list[dict]]) -> list[str]:
    """Every model `commit` names: its ledger rows, trailers and mentions."""
    out: list[str] = []
    for name in [*_measured(commit, ledger), *_trailers(commit), *_mentions(commit)]:
        _add(out, name)
    return out


def attribute(commit: Commit, ledger: dict[str, list[dict]], timeline=None) -> Attribution:
    """Who made `commit`. With a `timeline` (`models.Timeline`), a model named
    without its version takes the newest version of its family on the
    commit's date, and the note says so."""
    found = _raw(commit, ledger)
    if timeline is None or not found.models:
        return found
    named, by_date = [], False
    for model in found.models:
        name, dated = timeline.resolve(model, commit.date)
        by_date |= dated
        _add(named, name)
    if not by_date:
        return found
    note = "; ".join(x for x in (found.note, f"version from the date {commit.date[:10]}") if x)
    return Attribution(tuple(named), found.basis, note)


def _raw(commit: Commit, ledger: dict[str, list[dict]]) -> Attribution:
    models = _measured(commit, ledger)
    if models:
        return Attribution(tuple(models), "measured")
    trailers = _trailers(commit)
    if trailers:
        return Attribution(tuple(trailers), "declared")
    mentioned = _mentions(commit)
    if mentioned:
        return Attribution(tuple(mentioned), "message")
    if _AI_NAME.search(commit.author):
        return Attribution((_clean(commit.author),), "message")
    author = commit.author.lower()
    if author in _HUMAN_AUTHORS or author.split(" ")[0] == "agent":
        return Attribution(("GPT",), "unsigned", "no model trailer: GPT (Jon's rule)")
    return Attribution((), "unknown", "nothing names a model")


AUTHORS = Path(__file__).resolve().parent / "authors.yaml"


def curated(path: Path | None = None) -> dict[tuple[str, str], Attribution]:
    """`(commit, renderer-relative path) -> Attribution` from `authors.yaml`."""
    path = path or AUTHORS
    if not path.is_file():
        return {}
    import yaml  # noqa: PLC0415

    out: dict[tuple[str, str], Attribution] = {}
    for row in (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("authors") or []:
        for file in row.get("paths") or []:
            out[(str(row["commit"]), str(file))] = Attribution((str(row["who"]),), "curated", str(row.get("note", "")))
    return out
