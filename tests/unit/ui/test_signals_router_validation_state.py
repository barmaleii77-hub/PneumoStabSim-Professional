from __future__ import annotations

from types import SimpleNamespace

from src.ui.main_window_pkg.signals_router import SignalsRouter


class _StatusBar:
    def __init__(self) -> None:
        self.messages: list[tuple[str, int]] = []

    def showMessage(self, message: str, timeout: int = 0) -> None:  # noqa: N802
        self.messages.append((message, timeout))


def test_validation_state_is_recorded_and_surfaces_status_bar() -> None:
    window = SimpleNamespace(status_bar=_StatusBar())

    SignalsRouter.handle_accordion_field_validation_state(
        window,
        "modes",
        "ambient_temperature_c",
        "error",
        "invalid temperature",
    )

    assert ("modes", "ambient_temperature_c") in window._accordion_validation_states
    record = window._accordion_validation_states[("modes", "ambient_temperature_c")]
    assert record["state"] == "error"
    assert record["message"] == "invalid temperature"
    assert window.status_bar.messages[-1] == ("invalid temperature", 6000)
