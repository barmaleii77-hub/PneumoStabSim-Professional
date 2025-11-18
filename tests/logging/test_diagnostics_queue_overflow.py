import logging
import time

from src.diagnostics.logger_factory import (
    configure_logging,
    get_logger,
    get_logging_queue_stats,
    shutdown_logging,
)


def test_queue_listener_handles_overflow_without_blocking(monkeypatch):
    monkeypatch.setenv("PSS_FORCE_LOG_QUEUE", "1")
    configure_logging(
        level=logging.INFO,
        use_queue_listener=True,
        queue_size=1,
        queue_poll_interval=0.01,
        queue_drain_delay=0.02,
    )

    logger = get_logger("diagnostics.queue-test")

    start = time.monotonic()
    for idx in range(200):
        logger.info("burst_event", idx=idx)
    duration = time.monotonic() - start

    # Allow the listener to drain pending entries.
    time.sleep(0.05)
    stats = get_logging_queue_stats()
    shutdown_logging()

    assert duration < 1.0, "Queue-backed logging should not block the producer"
    assert stats["max_size"] == 1
    assert stats["dropped"] > 0
