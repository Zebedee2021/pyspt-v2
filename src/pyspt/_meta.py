"""Parity-verification metadata for pyspt public functions.

This module exposes a small, dependency-free decorator
:func:`parity_verified` that marks a public function as numerically
aligned against a named reference implementation (typically
MATLAB R2025b Signal Processing Toolbox). The metadata is
introspectable via :func:`iter_parity_registry` and is consumed by:

* ``scripts/export_api.py`` to emit ``docs/data/api.json`` (a
  machine-readable API catalogue for AI tools and the docs site),
* ``pyspt/_validate.py`` (optional) to assert that any function
  claiming parity has a matching ``.npz`` fixture on disk,
* future Sphinx/HTML doc generators.

设计目标
--------
* **零运行时开销** — decorator 只在函数对象上挂一个 ``__parity__``
  属性和一个全局注册表项，不改函数行为。
* **可被 AI 摄入** — ``docs/data/api.json`` 是首要交付物，
  而不是给人看的 HTML。
* **可被 pytest 校验** — ``fixtures`` 字段列出 fixture 路径前缀，
  CI 可以照表检查 fixture 是否真的存在。
"""

from __future__ import annotations

from dataclasses import asdict as _asdict
from dataclasses import dataclass, field
from typing import Callable

__all__ = [
    "ParityInfo",
    "parity_verified",
    "iter_parity_registry",
    "get_parity",
]


@dataclass(frozen=True)
class ParityInfo:
    """Verified-against metadata attached to a public function.

    Attributes
    ----------
    reference
        Human-readable description of the reference implementation,
        e.g. ``"MATLAB R2025b Signal Processing Toolbox"``.
    fixtures
        Fixture identifiers (without file extension) under
        ``tests/fixtures/<module>/``. Each entry MUST correspond to
        a real ``.npz`` file on disk; this is checked at export time.
    test_path
        Posix-style path to the pytest module that consumes the
        fixtures, e.g. ``"tests/waveforms/test_waveforms_parity.py"``.
    max_abs_err
        Largest absolute deviation observed during the most recent
        parity run. ``None`` means "not measured".
    """

    reference: str
    fixtures: tuple[str, ...] = field(default_factory=tuple)
    test_path: str | None = None
    max_abs_err: float | None = None

    def to_dict(self) -> dict:
        d = _asdict(self)
        # JSON-friendly: convert tuple to list.
        d["fixtures"] = list(self.fixtures)
        return d


# Module-level registry: keyed by ``"<module>.<func>"`` (the qualname
# at the package root, i.e. what `from pyspt.X import Y` exposes).
_REGISTRY: dict[str, ParityInfo] = {}


def parity_verified(
    *,
    reference: str,
    fixtures: list[str] | tuple[str, ...] | None = None,
    test_path: str | None = None,
    max_abs_err: float | None = None,
) -> Callable[[Callable], Callable]:
    """Mark a public function as parity-verified against *reference*.

    Parameters
    ----------
    reference
        Free-form description of the reference implementation.
    fixtures
        List of fixture basenames (without ``.npz``) under
        ``tests/fixtures/<module>/``.
    test_path
        Path to the test module that exercises these fixtures.
    max_abs_err
        Maximum absolute deviation observed against the reference;
        pass ``None`` if unmeasured.

    Returns
    -------
    Callable
        A decorator that attaches a :class:`ParityInfo` to the wrapped
        function and returns the function unchanged.

    Examples
    --------
    >>> @parity_verified(
    ...     reference="MATLAB R2025b Signal Processing Toolbox",
    ...     fixtures=["chirp__linear", "chirp__quadratic"],
    ...     test_path="tests/waveforms/test_waveforms_parity.py",
    ... )
    ... def chirp(t, f0, t1, f1, *, method="linear", phi=0.0): ...
    """
    info = ParityInfo(
        reference=reference,
        fixtures=tuple(fixtures or ()),
        test_path=test_path,
        max_abs_err=max_abs_err,
    )

    def deco(fn: Callable) -> Callable:
        # Use qualname so re-exports via `from .X import Y` keep the
        # canonical name. Falls back to __name__ for safety.
        key = f"{fn.__module__}.{fn.__qualname__}"
        _REGISTRY[key] = info
        try:
            fn.__parity__ = info  # type: ignore[attr-defined]
        except (AttributeError, TypeError):
            # Some callable objects (e.g. builtins) forbid attribute
            # assignment — silently skip in that case.
            pass
        return fn

    return deco


def iter_parity_registry() -> list[tuple[str, ParityInfo]]:
    """Return ``[(qualname, ParityInfo), ...]`` for every decorated function.

    The order is stable across runs because insertion order is preserved
    (Python ≥ 3.7 dict semantics).
    """
    return list(_REGISTRY.items())


def get_parity(qualname: str) -> ParityInfo | None:
    """Look up :class:`ParityInfo` by ``"<module>.<func>"`` key.

    Returns ``None`` if the function is not in the registry.
    """
    return _REGISTRY.get(qualname)
