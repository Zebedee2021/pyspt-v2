"""Export a machine-readable catalogue of pyspt public APIs.

Writes ``docs/data/api.json`` containing one entry per
``@parity_verified`` function, keyed by the **public** qualname
(e.g. ``pyspt.waveforms.chirp``) so that AI tools and the docs site
can ingest it directly.

Usage
-----
    python scripts/export_api.py            # writes docs/data/api.json
    python scripts/export_api.py --check    # exits non-zero if stale

The ``--check`` mode is intended for CI: it fails when the on-disk
JSON does not match the live registry, catching cases where someone
added a new ``@parity_verified`` decorator without regenerating the
export.

校验
----
The script also asserts that every fixture listed under
``fixtures`` actually exists on disk under
``tests/fixtures/<module>/<name>.npz``. CI can therefore catch the
case where a parity claim was added but the corresponding fixture
was forgotten.
"""

from __future__ import annotations

import argparse
import importlib
import json
import pkgutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pyspt

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO_ROOT / "docs" / "data" / "api.json"
FIXTURES_ROOT = REPO_ROOT / "tests" / "fixtures"


def _walk_public_modules():
    """Yield ``(modname, module, __all__)`` for every pyspt submodule."""
    for info in pkgutil.walk_packages(pyspt.__path__, prefix="pyspt."):
        if info.ispkg:
            # Skip sub-packages-of-sub-packages for the first pass; the
            # walker recurses on its own, but we want every leaf
            # module too.
            continue
        try:
            mod = importlib.import_module(info.name)
        except Exception as exc:  # pragma: no cover - debug aid
            print(f"[export_api] skip {info.name}: {exc}", file=sys.stderr)
            continue
        public = getattr(mod, "__all__", None)
        if not public:
            continue
        yield info.name, mod, public


def _module_basename(modname: str) -> str:
    """``pyspt.waveforms._modulated`` → ``waveforms``."""
    parts = modname.split(".")
    if len(parts) >= 2 and parts[0] == "pyspt":
        return parts[1]
    return parts[-1]


def collect_api() -> dict:
    """Walk the public API surface and collect parity metadata."""
    api: dict[str, dict] = {}
    missing_fixtures: list[str] = []

    for modname, mod, public_names in _walk_public_modules():
        mod_basename = _module_basename(modname)
        for fname in public_names:
            fn = getattr(mod, fname, None)
            if fn is None:
                continue
            parity = getattr(fn, "__parity__", None)
            if parity is None:
                continue

            # Public qualname uses the submodule's basename (e.g.
            # ``waveforms``) not its internal layout
            # (``_modulated``). This is the name users type.
            public_key = f"pyspt.{mod_basename}.{fname}"
            entry = parity.to_dict()
            entry["module"] = f"pyspt.{mod_basename}"
            entry["name"] = fname
            entry["fixtures_resolved"] = []

            # Resolve fixture basenames to absolute paths under
            # tests/fixtures/<module>/. Bail loudly if any is missing.
            for fb in entry["fixtures"]:
                path = FIXTURES_ROOT / mod_basename / f"{fb}.npz"
                if not path.is_file():
                    missing_fixtures.append(
                        f"{public_key} claims '{fb}' but {path} not found"
                    )
                else:
                    entry["fixtures_resolved"].append(
                        str(path.relative_to(REPO_ROOT)).replace("\\", "/")
                    )

            api[public_key] = entry

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pyspt_version": getattr(pyspt, "__version__", "unknown"),
        "function_count": len(api),
        "functions": dict(sorted(api.items())),
    }
    return payload, missing_fixtures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if on-disk api.json does not match the live registry.",
    )
    args = parser.parse_args(argv)

    payload, missing = collect_api()

    if missing:
        print("[export_api] fixture-validation FAILED:", file=sys.stderr)
        for line in missing:
            print(f"  - {line}", file=sys.stderr)
        return 2

    new_text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    args.out.parent.mkdir(parents=True, exist_ok=True)

    if args.check:
        if not args.out.is_file():
            print(f"[export_api] --check: {args.out} not found", file=sys.stderr)
            return 1
        # Compare only the function-level payload, not `generated_at`
        # (which always changes between runs and would make --check
        # perpetually stale).
        try:
            on_disk_payload = json.loads(args.out.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"[export_api] --check: {args.out} is not valid JSON: {exc}",
                  file=sys.stderr)
            return 1
        on_disk_functions = on_disk_payload.get("functions", {})
        new_functions = payload["functions"]
        if on_disk_functions != new_functions:
            print(
                f"[export_api] --check: {args.out} is stale "
                f"(on-disk={len(on_disk_functions)} functions, "
                f"live={len(new_functions)} functions). "
                "Run `python scripts/export_api.py` and commit.",
                file=sys.stderr,
            )
            return 1
        print(f"[export_api] --check: {args.out} is up to date "
              f"({len(new_functions)} functions)")
        return 0

    args.out.write_text(new_text, encoding="utf-8")
    print(
        f"[export_api] wrote {args.out} ({payload['function_count']} functions, "
        f"sum fixtures = {sum(len(v['fixtures']) for v in payload['functions'].values())})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
