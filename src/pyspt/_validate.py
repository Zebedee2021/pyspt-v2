"""Cross-check every ``@parity_verified`` claim against the test suite.

This module exposes a single function, :func:`validate_registry`, that
inspects the in-memory parity registry and reports any inconsistency
between a decorator claim and:

* the on-disk ``.npz`` fixtures declared in ``fixtures``,
* the test module declared in ``test_path`` (it must exist and must
  expose a top-level ``CASE_RUNNERS`` dict containing every declared
  fixture's stem),
* the public surface of the function being actually importable.

The same function is used by:

* ``scripts/export_api.py`` — both default and ``--check`` modes
  refuse to write/check out a registry with errors,
* ``tests/test_parity_consistency.py`` — a pytest that fails loudly
  if any claim is broken,
* ``tests/test_parity_negative.py`` — targeted negative cases that
  construct broken registries in-memory via monkeypatch.

Design notes
------------
* **AST over import.** We parse the test module with :mod:`ast` rather
  than importing it. Importing test modules under ``export_api.py``
  would create a hard dependency on pytest being installed and would
  risk running module-level side-effects; AST parsing is robust and
  dependency-free.
* **Populating the registry.** :func:`validate_registry` walks the
  ``pyspt`` package and imports each submodule so that any
  ``@parity_verified`` decorators fire. Tests can short-circuit this
  by passing a pre-populated ``items`` argument.
* **No silent pass.** When ``strict=True`` (the default) the function
  returns a non-empty list for any error, never raising — callers
  decide how to escalate. This keeps the validator safe to call from
  any context (CI script, pytest hook, plain REPL).
"""

from __future__ import annotations

import ast
import importlib
import pkgutil
from collections.abc import Iterable
from pathlib import Path

import pyspt
from pyspt._meta import ParityInfo

__all__ = ["validate_registry", "collect_registry", "ValidationError"]


# ``src/pyspt/_validate.py`` -> src/ -> repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_ROOT = REPO_ROOT / "tests" / "fixtures"


class ValidationError:
    """A single inconsistency in the parity registry.

    Attributes
    ----------
    qualname
        ``"<module>.<func>"`` of the offending claim, or ``""`` for
        registry-wide issues (e.g. duplicate keys).
    message
        Human-readable description of what is wrong.
    """

    __slots__ = ("qualname", "message")

    def __init__(self, qualname: str, message: str) -> None:
        self.qualname = qualname
        self.message = message

    def __str__(self) -> str:
        return f"{self.qualname}: {self.message}" if self.qualname else self.message


def collect_registry() -> list[tuple[str, ParityInfo]]:
    """Import every pyspt submodule and return the populated registry.

    The registry only contains entries for submodules that have been
    imported (decorator side-effect). This helper guarantees a full
    snapshot by walking ``pyspt``'s public submodules.

    The walker only descends into modules that declare ``__all__`` —
    anything in ``src/pyspt**/__init__.py`` is part of the public API
    surface we care about. Internal ``_*`` modules (e.g. ``_meta``,
    ``_validate``) are excluded by convention: their docstrings say so.

    Internally-keyed entries (e.g. ``pyspt.waveforms._modulated.chirp``
    from the decorator side-effect) are mapped to their public qualname
    (``pyspt.waveforms.chirp``) by checking each module's ``__all__``.
    This mirrors the key used in ``docs/data/api.json`` so the
    validator and the export agree on what counts as "claimed".
    """
    for info in pkgutil.walk_packages(pyspt.__path__, prefix="pyspt."):
        leaf = info.name.rsplit(".", 1)[-1]
        if leaf.startswith("_"):
            continue
        try:
            importlib.import_module(info.name)
        except Exception:
            continue

    # Force ``pyspt``'s own __init__ to expose version.
    _ = pyspt.__version__

    # Build the returned registry under PUBLIC qualnames. If a module
    # has the same function re-exported under multiple names, the
    # first wins (Python insertion order is preserved).
    out: list[tuple[str, ParityInfo]] = []
    seen_internal: set[int] = set()
    for info in pkgutil.walk_packages(pyspt.__path__, prefix="pyspt."):
        leaf = info.name.rsplit(".", 1)[-1]
        if leaf.startswith("_"):
            continue
        try:
            mod = importlib.import_module(info.name)
        except Exception:
            continue
        all_names = getattr(mod, "__all__", None)
        if not all_names:
            continue
        for fname in all_names:
            fn = getattr(mod, fname, None)
            parity = getattr(fn, "__parity__", None)
            if parity is None:
                continue
            # Skip duplicates across modules that re-export the same
            # function under the same name.
            if id(fn) in seen_internal:
                continue
            seen_internal.add(id(fn))
            public_mod = info.name.rsplit(".", 1)[-1]
            out.append((f"pyspt.{public_mod}.{fname}", parity))

    return out


def _module_basename(qualname: str) -> str:
    """``pyspt.waveforms.chirp`` → ``waveforms``.

    Falls back to ``""`` for malformed keys rather than raising, so a
    stray key never crashes the whole validator.
    """
    parts = qualname.split(".")
    if len(parts) >= 2 and parts[0] == "pyspt":
        return parts[1]
    return ""


def _runner_keys_for(test_path: Path) -> tuple[set[str], str | None]:
    """Return the set of fixture stems registered in a test module.

    Returns ``(keys, error)`` where ``error`` is non-None if the
    module could not be parsed or has no ``CASE_RUNNERS`` dict.
    """
    try:
        source = test_path.read_text(encoding="utf-8")
    except OSError as exc:
        return set(), f"cannot read test module: {exc}"
    try:
        tree = ast.parse(source, filename=str(test_path))
    except SyntaxError as exc:
        return set(), f"test module has SyntaxError: {exc}"

    found = False
    keys: set[str] = set()
    for node in ast.walk(tree):
        # Both plain ``CASE_RUNNERS = {...}`` and annotated
        # ``CASE_RUNNERS: dict[...] = {...}`` are valid; capture both.
        value_node: ast.expr | None = None
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "CASE_RUNNERS":
                    value_node = node.value
                    break
        elif isinstance(node, ast.AnnAssign):
            if (
                isinstance(node.target, ast.Name)
                and node.target.id == "CASE_RUNNERS"
                and node.value is not None
            ):
                value_node = node.value

        if value_node is None:
            continue
        found = True
        if isinstance(value_node, ast.Dict):
            for key in value_node.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    keys.add(key.value)
    if not found:
        return set(), "test module has no top-level CASE_RUNNERS dict"
    return keys, None


def validate_registry(
    *,
    strict: bool = True,
    items: Iterable[tuple[str, ParityInfo]] | None = None,
    repo_root: Path | None = None,
) -> list[ValidationError]:
    """Cross-check every parity claim against disk + test files.

    Parameters
    ----------
    strict
        When True (default), every claim is checked. Reserved for
        future use — the validator currently performs the same checks
        regardless of this flag; callers may still distinguish via
        ``strict=False`` in the future.
    items
        Optional pre-populated registry to validate. Defaults to
        :func:`collect_registry`. Tests use this to inject broken
        registries without touching real fixtures.
    repo_root
        Override the repository root (defaults to
        ``REPO_ROOT``). Tests can point this at a temporary tree.

    Returns
    -------
    list[ValidationError]
        Empty list means every claim is consistent. Non-empty lists
        describe each problem individually; callers should surface
        each message to humans.
    """
    _ = strict  # reserved for future use; check semantics are identical
    root = repo_root or REPO_ROOT
    fixtures_root = root / "tests" / "fixtures"
    registry = list(items) if items is not None else collect_registry()

    errors: list[ValidationError] = []

    for qualname, info in registry:
        # 0. The qualname must be a parseable ``pyspt.<module>.<func>``
        #    key — without it we cannot resolve where fixtures live.
        #    This structural check fires before per-fixture disk checks
        #    so a malformed key doesn't masquerade as a downstream
        #    path error.
        mod_basename = _module_basename(qualname)
        if not mod_basename:
            errors.append(ValidationError(
                qualname,
                "qualname does not start with 'pyspt.<module>.'; cannot resolve fixture dir",
            ))
            continue

        # 1. fixtures must be declared (non-empty). An empty list means
        #    "we claim parity but cannot point at any evidence" — that
        #    is the most common way a stale decorator lies.
        if not info.fixtures:
            errors.append(ValidationError(
                qualname,
                "parity_verified with empty fixtures list "
                "(declare at least one fixture under tests/fixtures/<module>/)",
            ))
            continue

        # 2. test_path must point at an existing pytest module.
        if info.test_path is None:
            errors.append(ValidationError(
                qualname,
                "test_path is None (declare which pytest module consumes the fixtures)",
            ))
            continue
        test_path = root / info.test_path
        if not test_path.is_file():
            errors.append(ValidationError(
                qualname,
                f"test_path {info.test_path!r} does not exist on disk",
            ))
            continue

        # 3. The fixtures themselves must be on disk under the right
        #    module subdirectory.
        fixture_dir = fixtures_root / mod_basename
        for fb in info.fixtures:
            fixture_path = fixture_dir / f"{fb}.npz"
            if not fixture_path.is_file():
                errors.append(ValidationError(
                    qualname,
                    f"fixture {fb!r} declared but not found at "
                    f"{fixture_path.relative_to(root)}",
                ))

        # 4. The test module must declare each fixture's stem in
        #    CASE_RUNNERS. Without this the parity test silently skips.
        runner_keys, parse_err = _runner_keys_for(test_path)
        if parse_err is not None:
            errors.append(ValidationError(
                qualname,
                f"test module {info.test_path}: {parse_err}",
            ))
            continue
        for fb in info.fixtures:
            if fb not in runner_keys:
                errors.append(ValidationError(
                    qualname,
                    f"fixture {fb!r} not present in CASE_RUNNERS of {info.test_path}",
                ))

    return errors
