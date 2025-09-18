from __future__ import annotations

from typing import Any, Dict, Optional, Tuple
import re

# Lightweight, dependency-free decision engine with templates and platform-aware formatting

PLATFORMS = {"web", "email", "slack", "discord", "sms", "plain"}
URGENCY_LEVELS = {"low": 0, "normal": 1, "high": 2, "critical": 3}

URGENCY_BADGES = {
    "low": "",
    "normal": "",
    "high": "🔥 High",
    "critical": "🚨 Critical",
}


def _first_sentence(text: str) -> str:
    s = text.strip().split(". ")[0].strip()
    return s if s else text.strip()[:80]


def _clamp(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 1)].rstrip() + "…"


def _normalize_platform(p: Optional[str]) -> str:
    if not p:
        return "web"
    p = p.lower().strip()
    return p if p in PLATFORMS else "web"


def _normalize_urgency(u: Optional[str]) -> str:
    if not u:
        return "normal"
    u = u.lower().strip()
    return u if u in URGENCY_LEVELS else "normal"


# Simple intent detection
INTENTS = ("action_required", "reminder", "status_update", "answer")


def detect_intent(task_text: Optional[str], context: Optional[Dict[str, Any]]) -> str:
    text = (task_text or "").lower()
    # Context hints
    kind = (context or {}).get("kind")
    if isinstance(kind, str) and kind in INTENTS:
        return kind

    # Keyword heuristics
    if any(k in text for k in ("please approve", "need approval", "review", "blocker", "asap")):
        return "action_required"
    if any(k in text for k in ("remind", "reminder", "follow up", "due")):
        return "reminder"
    if any(k in text for k in ("status", "update", "progress", "summary")):
        return "status_update"
    return "answer"


# Template definitions (dependency-free). Variables available: title, body, bullets, tldr, next_steps
TEMPLATES: Dict[str, Dict[str, Any]] = {
    "action_required": {
        "title": "Action Required",
        "structure": [
            "TL;DR: {tldr}",
            "Next steps:",
            "- {next_steps}",
            "Details:\n{body}",
        ],
    },
    "reminder": {
        "title": "Reminder",
        "structure": [
            "TL;DR: {tldr}",
            "Reminder: {title}",
            "Details:\n{body}",
        ],
    },
    "status_update": {
        "title": "Status Update",
        "structure": [
            "TL;DR: {tldr}",
            "Highlights:",
            "- {bullets}",
            "Details:\n{body}",
        ],
    },
    "answer": {
        "title": "Answer",
        "structure": [
            "TL;DR: {tldr}",
            "Answer:\n{body}",
        ],
    },
}


def render_template(template_id: str, variables: Dict[str, Any]) -> str:
    tpl = TEMPLATES.get(template_id, TEMPLATES["answer"])  # fallback
    parts = []
    for seg in tpl["structure"]:
        try:
            parts.append(seg.format(**variables))
        except Exception:
            parts.append(seg)
    return "\n".join([p for p in parts if p and p.strip()])


# Platform-aware formatting

def format_for_platform(text: str, platform: str, urgency: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
    platform = _normalize_platform(platform)
    urgency = _normalize_urgency(urgency)

    meta: Dict[str, Any] = {"platform": platform, "urgency": urgency}

    # Derive a subject from first sentence for email
    subject_prefix = URGENCY_BADGES.get(urgency, "")
    subject_prefix = f"[{subject_prefix}] " if subject_prefix else ""

    if platform == "email":
        # Convert to a simple email with Subject + Body
        subject = subject_prefix + _clamp(_first_sentence(text), 80)
        # Basic HTML body for readability while also providing plaintext fallback
        body_text = text
        body_html = (
            "<div>"
            + (f"<p><strong>{subject_prefix.strip()}</strong></p>" if subject_prefix else "")
            + "<pre style=\"white-space:pre-wrap; font-family:inherit;\">"
            + text
            + "</pre></div>"
        )
        meta.update({"subject": subject, "content_type": "multipart/alternative"})
        return body_text, meta | {"html": body_html}

    if platform in {"slack", "discord"}:
        # Slack/Discord-friendly Markdown and emoji
        badge = URGENCY_BADGES.get(urgency, "")
        badge_md = f"*{badge}*\n" if badge else ""
        # Convert simple headings
        md = badge_md + re.sub(r"^TL;DR:", "*TL;DR:*", text, flags=re.IGNORECASE | re.MULTILINE)
        md = re.sub(r"^Details:", "*Details:*", md, flags=re.IGNORECASE | re.MULTILINE)
        return md, meta | {"format": "markdown"}

    if platform == "sms":
        # Very concise; clamp to 320 chars, keep TL;DR and one next step if present
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        # Keep TL;DR first if present
        tldr_line = next((l for l in lines if l.lower().startswith("tl;dr")), None)
        next_step_line = next((l for l in lines if l.lower().startswith("- ")), None)
        core = " ".join([p for p in [tldr_line, next_step_line] if p]) or " ".join(lines[:2])
        concise = _clamp(core, 320)
        return concise, meta | {"max_chars": 320}

    if platform == "plain":
        return text, meta | {"format": "plain"}

    # default: web
    # Provide slight HTML emphasis for TL;DR and section headers
    html = re.sub(r"^TL;DR:", "<strong>TL;DR:</strong>", text, flags=re.IGNORECASE | re.MULTILINE)
    html = re.sub(r"^Details:", "<strong>Details:</strong>", html, flags=re.IGNORECASE | re.MULTILINE)
    html = html.replace("\n", "<br/>")
    return html, meta | {"format": "html"}


# End-to-end decision + generation wrapper

def decide_and_generate(
    task_id: str,
    task_text: Optional[str],
    platform: Optional[str] = None,
    urgency: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str, str, Dict[str, Any]]:
    """
    Returns: formatted_text, tone, template_id, metadata
    """
    platform = _normalize_platform(platform)
    urgency = _normalize_urgency(urgency)

    # Base body: use task_text if provided, otherwise synthetic message from responder_agent
    base_body: str
    tone = "polite"
    if task_text and task_text.strip():
        base_body = task_text.strip()
    else:
        try:
            # Optional dynamic import to avoid hard dependency
            from responder_agent import generate_response as agent_generate

            base, tone = agent_generate(task_id)
            base_body = base
        except Exception:
            base_body = f"Generated response for task {task_id}"
            tone = "polite"

    # Construct variables influenced by urgency/context
    u = urgency
    is_urgent = URGENCY_LEVELS.get(u, 1) >= 2

    # TL;DR prioritizes urgency
    tldr = _first_sentence(base_body)
    if is_urgent:
        badge = URGENCY_BADGES.get(u, "")
        tldr = (badge + ": " if badge else "") + tldr

    next_steps = (context or {}).get("next_steps") or "Acknowledge and proceed as outlined."
    if isinstance(next_steps, list):
        next_steps = "; ".join(str(x) for x in next_steps)

    bullets = (context or {}).get("highlights") or []
    if isinstance(bullets, str):
        bullets = [bullets]
    if not bullets:
        # heuristics for auto bullets from body
        body_lines = [l.strip("- •\t ") for l in base_body.splitlines() if l.strip()]
        bullets = body_lines[:3]

    variables = {
        "title": (context or {}).get("title") or _first_sentence(base_body),
        "tldr": tldr,
        "body": base_body,
        "bullets": "\n- ".join(bullets) if bullets else "",
        "next_steps": next_steps,
    }

    intent = detect_intent(task_text, context)
    # Critical/high urgency coerces to action_required
    if is_urgent and intent != "action_required":
        intent = "action_required"

    composed = render_template(intent, variables)

    formatted, meta = format_for_platform(composed, platform, urgency, context)

    meta.update({
        "intent": intent,
        "template_id": intent,
    })

    return formatted, tone, intent, meta
