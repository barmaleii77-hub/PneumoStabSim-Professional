from src.bootstrap.dependency_config import (
    match_dependency_error,
    resolve_dependency_variant,
)


def test_resolve_dependency_variant_linux_config() -> None:
    variant = resolve_dependency_variant("opengl_runtime", platform_key="linux")

    assert variant.library_name == "GL"
    assert variant.human_name == "libGL.so.1"
    assert "libGL.so.1" in variant.error_markers
    assert variant.install_hint is not None


def test_match_dependency_error_detects_marker() -> None:
    variant = match_dependency_error(
        "opengl_runtime",
        "libGL.so.1: cannot open shared object file",
        platform_key="linux",
    )

    assert variant is not None
    assert variant.human_name == "libGL.so.1"
