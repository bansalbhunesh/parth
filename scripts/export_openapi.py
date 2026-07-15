"""Generate or verify the reviewed v1 OpenAPI contract snapshot."""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "contracts" / "openapi-v1.json"
sys.path.insert(0, str(ROOT))


def contract_schema() -> dict[str, Any]:
    from backend.main import app

    # FastAPI returns its cached schema object. Filter a deep copy so running
    # this exporter inside a test process cannot delete routes from the app.
    schema = deepcopy(app.openapi())
    schema["paths"] = {
        path: value
        for path, value in schema["paths"].items()
        if path.startswith("/api/v1") or path in {"/health/live", "/health/ready"}
    }
    return schema


def render_contract() -> str:
    return json.dumps(contract_schema(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when the snapshot differs")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    rendered = render_contract()
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != rendered:
            print(f"OpenAPI contract drift detected: regenerate {args.output}")
            return 1
        print(f"OpenAPI contract is current: {args.output}")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
