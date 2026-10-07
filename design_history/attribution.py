"""Which model drew a design, as far as the history can say.

Three kinds of evidence, strongest first:

``measured``  the resource ledger (``.llm_resource_tally``) names this commit and
              lists the models a session used. Present from about August 2026.
``declared``  a ``Co-Authored-By`` trailer in the commit message.
``message``   no trailer, but the subject or body names a model ("Big GPT 5.6
              Alice improvement"). Weaker: it may be a plan, not a signature.
``author``    no model is named, and the author field says who committed:
              Jon's accounts mean a human commit OR an unattributed agent one.
``unknown``   nothing says.

A commit is evidence about the session that made it, not proof that one model
drew every pixel: a session may use several, and a later commit may polish
earlier art. The result keeps the basis, so a reader can discount it.
"""

from __future__ import annotations

import dataclasses
import re

from .store import Commit

# The email is optional ("Co-Authored-By: Claude Opus 5.5" is a trailer too).
_TRAILER = re.compile(r"^co-authored-by:\s*([^<\r\n]+?)\s*(?:<[^>]*>)?\s*$", re.IGNORECASE | re.MULTILINE)
# A trailer names a MODEL only if it says so; a human co-author is not one.
_AI_NAME = re.compile(
    r"\b(claude|anthropic|gpt|openai|codex|gemini|copilot|opus|sonnet|haiku|fable)\b", re.IGNORECASE
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
    basis: str  # measured | declared | author | unknown
    note: str = ""

    def label(self) -> str:
        if self.models:
            return ", ".join(self.models) + ("" if self.basis == "measured" else f" ({self.basis})")
        return self.note or self.basis


def _clean(name: str) -> str:
    # "Claude Opus 4.8 (1M context)" -> "Claude Opus 4.8": the context window is
    # a deployment detail, not a different model.
    name = re.sub(r"\s*\((?:\d+\w*\s*)?context\)", "", name)
    # "Claude Opus 4.8 [1M]": the bracketed window is the same deployment detail.
    name = re.sub(r"\s*\[\d+\w*\]", "", name)
    return re.sub(r"\s+", " ", name).strip()


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


def attribute(commit: Commit, ledger: dict[str, list[dict]]) -> Attribution:
    rows = ledger.get(commit.sha)
    if rows:
        models: list[str] = []
        for row in rows:
            for model in row.get("m", []):
                model = pretty(model)
                if model not in models:
                    models.append(model)
        if models:
            return Attribution(tuple(models), "measured")
    trailers: list[str] = []
    for name in _TRAILER.findall(commit.body):
        name = _clean(name)
        if _AI_NAME.search(name):
            _add(trailers, name)
    if trailers:
        return Attribution(tuple(trailers), "declared")
    mentioned: list[str] = []
    for hit in _MENTION.findall(commit.subject + "\n" + commit.body):
        _add(mentioned, re.sub(r"\s+", " ", hit).strip())
    if mentioned:
        return Attribution(tuple(mentioned), "message")
    if commit.author.lower() in _HUMAN_AUTHORS:
        return Attribution((), "author", "no model named; committed from Jon's account")
    if commit.author.lower() == "agent":
        return Attribution((), "unknown", "an agent commit that names no model")
    return Attribution((), "unknown", "nothing names a model")
