"""Cross-check the parity registry against disk + test files.

This test imports the live ``@parity_verified`` registry (not a
monkeypatched one — see ``test_parity_negative.py`` for synthetic
cases) and asserts that every claim is consistent with the
fixtures and test files it points at.

What this test catches
----------------------
* A function claims ``fixtures=[...]`` but the ``.npz`` is missing.
* A function claims ``fixtures=[...]`` but the test module's
  ``CASE_RUNNERS`` dict has no key for that stem (so the test would
  silently skip, not fail).
* A function's ``test_path`` doesn't exist (e.g. the test file was
  renamed).
* A function's ``fixtures`` list is empty (an honest claim needs at
  least one piece of evidence).
* A function's ``test_path`` points at a module that lacks a
  ``CASE_RUNNERS`` dict at all.

If this test passes, every decorator in ``src/pyspt/**/_*.py`` is
genuinely backed by an on-disk fixture and a wired-up parity test.
"""

from __future__ import annotations

from pyspt._validate import collect_registry, validate_registry


def test_live_registry_has_no_validation_errors() -> None:
    """Every claim in the live registry is backed by disk + runner."""
    errors = validate_registry()
    assert not errors, (
        "Parity registry has inconsistencies:\n"
        + "\n".join(f"  - {e}" for e in errors)
    )


def test_live_registry_is_nonempty() -> None:
    """Sanity: at least one parity-verified function exists."""
    registry = collect_registry()
    assert len(registry) >= 3, (
        f"Expected at least 3 parity-verified functions, got {len(registry)}: "
        f"{[q for q, _ in registry]}"
    )


def test_live_registry_keys_use_public_qualnames() -> None:
    """Public qualnames must be of the form ``pyspt.<module>.<func>``.

    Decorators register under the *internal* module
    (``pyspt.waveforms._modulated``) by default; ``collect_registry``
    is responsible for remapping to the public surface so the
    validator, the export, and the docs site all agree.
    """
    for qualname, _ in collect_registry():
        parts = qualname.split(".")
        assert len(parts) == 3, f"bad qualname: {qualname!r}"
        assert parts[0] == "pyspt"
        assert not parts[1].startswith("_"), (
            f"qualname leaks internal module: {qualname!r}"
        )
        assert not parts[2].startswith("_")
