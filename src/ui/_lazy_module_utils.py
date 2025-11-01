"""Utilities for lazily imported UI packages.

The lazy ``__getattr__`` hooks in :mod:`src.ui.main_window_pkg` and
:mod:`src.ui.panels` need to co-operate with tooling that expects modules to
expose a ``__wrapped__`` attribute.  Qt and some inspection helpers call
``inspect.unwrap`` (or drop-in replacements) which internally use ``hasattr``
to probe for ``__wrapped__``.  Returning the module instance for every lookup
confuses those helpers, leading to infinite unwrap loops and noisy
``AttributeError`` traces during application start-up.

This module centralises the heuristics that detect such unwrap probes and tells
the lazy packages when to hide ``__wrapped__`` by re-raising ``AttributeError``.
Direct ``getattr(module, "__wrapped__")`` calls remain supported so external
consumers that rely on the attribute continue to work.
"""

from __future__ import annotations

import builtins
import dis
import inspect
from functools import lru_cache
from types import CodeType
from typing import Optional, Sequence

_SKIPPED_OPNAMES: frozenset[str] = frozenset(
    {
        "CACHE",
        "COPY_FREE_VARS",
        "EXTENDED_ARG",
        "LOAD_CONST",
        "LOAD_FAST",
        "PUSH_NULL",
        "PRECALL",
        "RESUME",
    }
)


@lru_cache(maxsize=None)
def _global_called_at(code: CodeType, offset: int) -> Optional[str]:
    """Return the global function name invoked at ``offset`` in ``code``.

    The CPython bytecode sequence for ``hasattr(x, "y")`` (3.12+/3.13) loads
    the global ``hasattr`` before issuing ``PRECALL``/``CALL`` instructions.
    By walking backwards from ``offset`` we can discover which builtin was
    invoked and decide whether the ``__wrapped__`` lookup originated from an
    unwrap routine.
    """

    instructions = tuple(dis.get_instructions(code))
    index = next(
        (i for i, instr in enumerate(instructions) if instr.offset == offset), None
    )
    if index is None:
        return None

    for instr in _reverse_skip(instructions, index):
        if instr.opname == "LOAD_GLOBAL" and isinstance(instr.argval, str):
            return instr.argval
    return None


def _reverse_skip(instructions: Sequence[dis.Instruction], start: int):
    """Yield instructions in reverse order skipping bookkeeping opcodes."""

    for index in range(start - 1, -1, -1):
        instr = instructions[index]
        if instr.opname in _SKIPPED_OPNAMES:
            continue
        yield instr


def should_suppress_wrapped() -> bool:
    """Return ``True`` when ``__getattr__`` should hide ``__wrapped__``.

    When an unwrap helper probes ``module.__wrapped__`` via ``hasattr`` we
    raise ``AttributeError`` to signal the absence of a wrapper and keep tools
    such as :func:`inspect.unwrap` from looping indefinitely.  Direct
    ``getattr`` access continues to return the module object itself.
    """

    frame = inspect.currentframe()
    if frame is None:
        return False

    caller = frame.f_back
    while caller is not None:
        module_name = caller.f_globals.get("__name__", "")
        function_name = caller.f_code.co_name

        if "unwrap" in function_name or module_name == "inspect":
            global_name = _global_called_at(caller.f_code, caller.f_lasti)
            if global_name == "hasattr":
                builtin_hasattr = getattr(builtins, "hasattr", None)
                resolved = caller.f_globals.get("hasattr", builtin_hasattr)
                if resolved is builtin_hasattr:
                    return True

        caller = caller.f_back

    return False


__all__ = ["should_suppress_wrapped"]
