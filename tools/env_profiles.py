"""Environment preset activation helpers for PneumoStabSim."""

from __future__ import annotations

import argparse
import json
import os
import platform
from dataclasses import dataclass
from typing import Iterable, Mapping, MutableMapping

__all__ = [
    "DEFAULT_PRESET",
    "EnvActivation",
    "EnvProfile",
    "apply_activation",
    "apply_profile",
    "available_presets",
    "resolve_activation",
    "render_shell_exports",
]

DEFAULT_PRESET = "normal"
_WINDOWS_NAMES = {"windows", "win32", "cygwin"}
_HEADLESS_BACKENDS = {"software", "minimal", "minimalgl"}


@dataclass(frozen=True)
class EnvProfile:
    """Static definition for a named environment preset."""

    name: str
    description: str
    set_vars: Mapping[str, str]
    unset_vars: tuple[str, ...] = ()


@dataclass(frozen=True)
class EnvActivation:
    """Resolved environment mutation for a preset."""

    preset: str
    set_vars: Mapping[str, str]
    unset_vars: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "preset": self.preset,
            "set": dict(self.set_vars),
            "unset": list(self.unset_vars),
        }


_PROFILES: dict[str, EnvProfile] = {
    "normal": EnvProfile(
        name="normal",
        description="Minimal logging for day-to-day development.",
        set_vars={},
        unset_vars=("QT_LOGGING_RULES", "DEBUG_ENABLED", "DEVELOPMENT_MODE"),
    ),
    "trace": EnvProfile(
        name="trace",
        description="Verbose Qt logging, equivalent to historical defaults.",
        set_vars={
            "QT_LOGGING_RULES": "js.debug=true;qt.qml.debug=true",
            "DEBUG_ENABLED": "true",
            "DEVELOPMENT_MODE": "true",
        },
    ),
}


def available_presets() -> tuple[str, ...]:
    """Return the list of supported preset names."""

    return tuple(sorted(_PROFILES))


def _normalise_preset(preset: str | None) -> str:
    value = (preset or "").strip().lower()
    return value or DEFAULT_PRESET


def _normalise_platform(value: str | None) -> str:
    if not value:
        return platform.system().strip().lower()
    return value.strip().lower()


def _gpu_activation(system_name: str) -> EnvActivation:
    if system_name in _WINDOWS_NAMES:
        set_vars = {"QT_QUICK_BACKEND": "rhi", "QSG_RHI_BACKEND": "d3d11"}
        unset: tuple[str, ...] = ()
    else:
        set_vars = {"QT_QUICK_BACKEND": "rhi"}
        unset = ("QSG_RHI_BACKEND",)
    return EnvActivation(preset="gpu", set_vars=set_vars, unset_vars=unset)


def _should_allow_gpu(env: Mapping[str, str], allow_gpu_overrides: bool | None) -> bool:
    if allow_gpu_overrides is not None:
        return allow_gpu_overrides
    backend = env.get("QT_QUICK_BACKEND", "").strip().lower()
    if backend in _HEADLESS_BACKENDS:
        return False
    return True


def resolve_activation(
    preset: str | None,
    *,
    env: Mapping[str, str] | None = None,
    allow_gpu_overrides: bool | None = None,
    platform_override: str | None = None,
) -> EnvActivation:
    """Resolve the environment mutation for *preset* without applying it."""

    env_snapshot = env or os.environ
    preset_name = _normalise_preset(preset)
    profile = _PROFILES.get(preset_name)
    if profile is None:
        available = ", ".join(sorted(_PROFILES))
        raise ValueError(f"Unknown preset '{preset_name}'. Available: {available}")

    set_vars = dict(profile.set_vars)
    unset_vars = list(profile.unset_vars)

    set_vars["PSS_ENV_PRESET"] = preset_name

    allow_gpu = _should_allow_gpu(env_snapshot, allow_gpu_overrides)
    if allow_gpu:
        gpu_activation = _gpu_activation(_normalise_platform(platform_override))
        set_vars.update(gpu_activation.set_vars)
        unset_vars.extend(gpu_activation.unset_vars)

    seen: set[str] = set()
    ordered_unset = [key for key in unset_vars if not (key in seen or seen.add(key))]

    return EnvActivation(
        preset=preset_name, set_vars=set_vars, unset_vars=tuple(ordered_unset)
    )


def apply_activation(
    activation: EnvActivation, env: MutableMapping[str, str] | None = None
) -> MutableMapping[str, str]:
    """Apply a pre-resolved activation to *env* (defaults to ``os.environ``)."""

    target = env if env is not None else os.environ
    for key in activation.unset_vars:
        target.pop(key, None)
    for key, value in activation.set_vars.items():
        target[key] = value
    return target


def apply_profile(
    preset: str | None,
    env: MutableMapping[str, str] | None = None,
    *,
    allow_gpu_overrides: bool | None = None,
    platform_override: str | None = None,
) -> MutableMapping[str, str]:
    """Convenience wrapper combining :func:`resolve_activation` and apply."""

    activation = resolve_activation(
        preset,
        env=env,
        allow_gpu_overrides=allow_gpu_overrides,
        platform_override=platform_override,
    )
    return apply_activation(activation, env)


def render_shell_exports(
    activation: EnvActivation,
    *,
    shell: str = "posix",
    include_header: bool = True,
) -> str:
    """Render shell commands that apply *activation* in the specified *shell*."""

    shell_key = shell.lower()
    if shell_key not in {"posix", "powershell", "cmd"}:
        raise ValueError("shell must be one of: posix, powershell, cmd")

    lines: list[str] = []
    if include_header:
        if shell_key == "posix":
            lines.extend(
                [
                    "# PneumoStabSim environment preset",
                    f"# preset={activation.preset}",
                ]
            )
        elif shell_key == "powershell":
            lines.extend(
                [
                    "# PneumoStabSim environment preset",
                    f"# preset={activation.preset}",
                ]
            )
        else:
            lines.extend(
                [
                    "@echo off",
                    f"REM PneumoStabSim environment preset: {activation.preset}",
                ]
            )

    def add_unset(key: str) -> None:
        if shell_key == "posix":
            lines.append(f"unset {key}")
        elif shell_key == "powershell":
            lines.append(f"Remove-Item Env:{key} -ErrorAction SilentlyContinue")
        else:
            lines.append(f"set {key}=")

    def add_set(key: str, value: str) -> None:
        if shell_key == "posix":
            lines.append(f"export {key}={json.dumps(value)}")
        elif shell_key == "powershell":
            escaped = value.replace('"', '""')
            lines.append(f'$Env:{key} = "{escaped}"')
        else:
            escaped = value.replace("%", "%%").replace("\n", "^\n")
            escaped = escaped.replace('"', '\\"')
            lines.append(f'set "{key}={escaped}"')

    for key in activation.unset_vars:
        add_unset(key)

    for key, value in activation.set_vars.items():
        add_set(key, value)

    if shell_key == "cmd" and include_header:
        lines.append("")

    return "\n".join(lines)


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render or apply PneumoStabSim environment presets",
    )
    parser.add_argument(
        "--preset",
        default=None,
        help=f"Preset name (default: {DEFAULT_PRESET})",
    )
    parser.add_argument(
        "--format",
        choices=["posix", "powershell", "cmd", "json"],
        default="posix",
        help="Output format",
    )
    parser.add_argument(
        "--platform",
        default=None,
        help="Override detected platform when computing GPU defaults",
    )
    parser.add_argument(
        "--allow-gpu-overrides",
        dest="allow_gpu_overrides",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Force enabling/disabling GPU backend overrides",
    )
    parser.add_argument(
        "--no-header",
        dest="include_header",
        action="store_false",
        help="Omit comment header in shell output",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = _build_argument_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    activation = resolve_activation(
        args.preset,
        allow_gpu_overrides=args.allow_gpu_overrides,
        platform_override=args.platform,
    )

    if args.format == "json":
        payload = activation.to_dict()
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    output = render_shell_exports(
        activation,
        shell=args.format,
        include_header=args.include_header,
    )
    print(output)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
