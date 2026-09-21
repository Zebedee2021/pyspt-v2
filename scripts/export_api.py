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
JSON does not match the live registry, OR when the live registry
itself fails :func:`pyspt._validate.validate_registry`. Catching the
latter means CI also flags the moment someone adds a
``@parity_verified`` decorator whose fixtures/runner/test_path are
broken — *before* a stale JSON ships.

校验
----
The script also calls
:func:`pyspt._validate.validate_registry` which enforces:

* every ``@parity_verified`` function declares a non-empty ``fixtures``
  list and a non-None ``test_path``,
* every declared fixture exists at
  ``tests/fixtures/<module>/<name>.npz``,
* every declared fixture has a corresponding entry in the
  ``CASE_RUNNERS`` dict of ``test_path``,
* the test module itself parses cleanly.

Any of the above failing causes the script to exit with a non-zero
status in BOTH default and ``--check`` modes. ``--check`` additionally
verifies that ``pyspt_version`` and ``function_count`` in the on-disk
JSON match the live registry, and that the function-level payload is
byte-identical (after sorting) before reporting success. ``--check``
does not write any files.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pyspt
from pyspt._meta import ParityInfo
from pyspt._validate import ValidationError, collect_registry, validate_registry

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO_ROOT / "docs" / "data" / "api.json"


def _entry_for(qualname: str, info: ParityInfo) -> dict:
    """Translate a (qualname, ParityInfo) pair into a JSON-serializable dict.

    The ``module`` and ``name`` fields duplicate the qualname so that
    consumers that only want a flat list (e.g. the docs site's
    parity-badge script) don't have to re-parse the dotted key. The
    ``fixtures_resolved`` field is a list of repo-relative POSIX paths,
    kept in sync with ``fixtures`` for human readability.
    """
    mod_basename = qualname.split(".", 2)[1] if qualname.count(".") >= 2 else ""
    entry = info.to_dict()
    entry["module"] = f"pyspt.{mod_basename}" if mod_basename else ""
    entry["name"] = qualname.rsplit(".", 1)[-1]
    entry["fixtures_resolved"] = []
    if mod_basename:
        fixtures_root = REPO_ROOT / "tests" / "fixtures" / mod_basename
        for fb in entry["fixtures"]:
            path = fixtures_root / f"{fb}.npz"
            entry["fixtures_resolved"].append(
                str(path.relative_to(REPO_ROOT)).replace("\\", "/")
            )
    return entry


def collect_api() -> dict:
    """Build the JSON payload that will be written to disk.

    The function-level ``fixtures`` and ``fixtures_resolved`` fields
    match the live registry; per-fixture path resolution failures
    surface here as empty entries *and* via the validator (so the
    caller's exit code is non-zero).

    Returns
    -------
    dict
        Payload with keys ``generated_at``, ``pyspt_version``,
        ``function_count``, ``functions``.
    """
    api: dict[str, dict] = {}
    for qualname, info in collect_registry():
        api[qualname] = _entry_for(qualname, info)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pyspt_version": getattr(pyspt, "__version__", "unknown"),
        "function_count": len(api),
        "functions": dict(sorted(api.items())),
    }


def _print_validation_errors(errors: list[ValidationError]) -> None:
    print("[export_api] registry-validation FAILED:", file=sys.stderr)
    for err in errors:
        print(f"  - {err}", file=sys.stderr)


def _normalize_payload(payload: dict) -> dict:
    """Strip ``generated_at`` so two payloads with different timestamps compare equal."""
    return {k: v for k, v in payload.items() if k != "generated_at"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if on-disk api.json does not match the live registry "
             "OR if the registry itself fails validation. Never writes files.",
    )
    args = parser.parse_args(argv)

    # Step 1: build the live registry, then cross-check it.
    payload = collect_api()
    errors = validate_registry()
    if errors:
        _print_validation_errors(errors)
        return 2

    # Step 2: --check is read-only. Compare against the on-disk JSON
    # field-by-field; failure here means somebody changed a fixture,
    # decorator, or version without regenerating.
    if args.check:
        if not args.out.is_file():
            print(
                f"[export_api] --check: {args.out} not found "
                "(run `python scripts/export_api.py` to create it)",
                file=sys.stderr,
            )
            return 1
        try:
            on_disk_text = args.out.read_text(encoding="utf-8")
        except OSError as exc:
            print(
                f"[export_api] --check: cannot read {args.out}: {exc}",
                file=sys.stderr,
            )
            return 1
        try:
            on_disk = json.loads(on_disk_text)
        except json.JSONDecodeError as exc:
            print(
                f"[export_api] --check: {args.out} is not valid JSON: {exc}",
                file=sys.stderr,
            )
            return 1

        # Compare stable fields. ``generated_at`` is excluded by design
        # because it changes between runs and would make --check
        # perpetually stale.
        new_norm = _normalize_payload(payload)
        on_disk_norm = _normalize_payload(on_disk)

        for field in ("pyspt_version", "function_count"):
            if on_disk_norm.get(field) != new_norm.get(field):
                print(
                    f"[export_api] --check: stale {field!r} "
                    f"(on-disk={on_disk_norm.get(field)!r}, "
                    f"live={new_norm.get(field)!r}). "
                    "Run `python scripts/export_api.py` and commit.",
                    file=sys.stderr,
                )
                return 1

        if on_disk_norm.get("functions", {}) != new_norm.get("functions", {}):
            print(
                f"[export_api] --check: {args.out} function-level payload is stale "
                f"(on-disk={len(on_disk_norm.get('functions', {}))} functions, "
                f"live={len(new_norm.get('functions', {}))} functions). "
                "Run `python scripts/export_api.py` and commit.",
                file=sys.stderr,
            )
            return 1

        print(
            f"[export_api] --check: {args.out} is up to date "
            f"({payload['function_count']} functions, "
            f"version {payload['pyspt_version']})"
        )
        return 0

    # Step 3: default mode — write the file. Validation already passed
    # in Step 1, so reaching this line means it's safe to publish.
    new_text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(new_text, encoding="utf-8")
    total_fixtures = sum(
        len(v["fixtures"]) for v in payload["functions"].values()
    )
    print(
        f"[export_api] wrote {args.out} "
        f"({payload['function_count']} functions, "
        f"{total_fixtures} fixture cases, "
        f"version {payload['pyspt_version']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
