from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python run.py INSTANCE_DIR", file=sys.stderr)
        return 2
    instance_dir = Path(sys.argv[1])
    metadata = json.loads((instance_dir / "instance.json").read_text(encoding="utf-8"))
    (instance_dir / metadata["circuit_a"]).read_text(encoding="utf-8")
    (instance_dir / metadata["circuit_b"]).read_text(encoding="utf-8")
    payload = {
        "instance_id": metadata["instance_id"],
        "decision": "EQUIVALENT",
        "evidence": {"note": "placeholder starter decision"},
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
