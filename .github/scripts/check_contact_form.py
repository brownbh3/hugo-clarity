"""FIG-1 I7 gate: assert the shared contact-form partial keeps its live wiring.

A theme upgrade / merge can silently overwrite layouts/partials/contact-form.html and
drop the API Gateway endpoint or the reCAPTCHA sitekey — the form then renders but
POSTs nowhere (silent breakage, no build error). This gate fails the theme build if
either piece of wiring goes missing.

Self-contained (stdlib only) so the theme repo's CI needs no cross-repo dependency.

Usage:
    python3 .github/scripts/check_contact_form.py
    python3 .github/scripts/check_contact_form.py path/to/contact-form.html
Exit: 0 = wiring intact, 1 = missing endpoint/sitekey or file absent.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

DEFAULT_PARTIAL = Path("layouts/partials/contact-form.html")

# An AWS API Gateway invoke URL: https://<id>.execute-api.<region>.amazonaws.com/...
ENDPOINT_RE = re.compile(r"https://[a-z0-9]+\.execute-api\.[a-z0-9-]+\.amazonaws\.com")
# reCAPTCHA wiring: a data-sitekey="..." attribute with a non-empty key.
SITEKEY_RE = re.compile(r'data-sitekey="([^"]+)"')


def check(path: Path) -> list[str]:
    """Return a list of problems (empty = intact)."""
    if not path.is_file():
        return [f"contact-form partial missing: {path}"]
    text = path.read_text()
    problems = []
    if not ENDPOINT_RE.search(text):
        problems.append("no API Gateway endpoint (execute-api…amazonaws.com) — form POSTs nowhere")
    m = SITEKEY_RE.search(text)
    if not m or not m.group(1).strip():
        problems.append("no reCAPTCHA data-sitekey — spam gate dropped")
    return problems


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    path = Path(argv[0]) if argv else DEFAULT_PARTIAL
    problems = check(path)
    if problems:
        print(f"I7 CONTACT-FORM GATE FAILED ({path}):", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"I7 OK: {path} — API endpoint + reCAPTCHA sitekey intact.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
