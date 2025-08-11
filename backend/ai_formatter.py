import json
import os
from typing import Dict, Tuple


def _fallback_format(submission: Dict[str, str]) -> Tuple[str, str]:
    name = submission.get("name", "").strip() or "Someone"
    email = submission.get("email", "").strip() or "unknown@example.com"
    message = submission.get("message", "").strip() or "(no message)"
    subject = f"New contact from {name}"
    body = (
        f"You received a new contact submission.\n\n"
        f"Name: {name}\n"
        f"Email: {email}\n\n"
        f"Message:\n{message}\n"
    )
    return subject, body


def craft_subject_and_body(submission: Dict[str, str]) -> Tuple[str, str]:
    """
    Create a subject and body for an email from the submission dict.
    Tries to use OpenAI when OPENAI_API_KEY is available; otherwise falls back.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _fallback_format(submission)

    try:
        # Lazy import to avoid hard dependency in environments without the package installed
        from openai import OpenAI  # type: ignore

        client = OpenAI(api_key=api_key)
        prompt = (
            "You are an assistant that formats a professional email subject and body from form input.\n"
            "Return ONLY JSON with keys: subject, body. Keep body concise and clear.\n\n"
            f"Form Input:\n{json.dumps(submission, indent=2)}\n"
        )
        completion = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You format emails and respond in strict JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        content = completion.choices[0].message.content or "{}"
        parsed = json.loads(content)
        subject = (parsed.get("subject") or "New form submission").strip()
        body = (parsed.get("body") or "See details in the submission.").strip()
        return subject, body
    except Exception:
        # Any failure falls back to a deterministic format
        return _fallback_format(submission)