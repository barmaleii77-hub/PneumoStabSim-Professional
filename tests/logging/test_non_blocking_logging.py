import time
from pathlib import Path

from src.common import logging_setup


def test_queue_handler_drops_when_full(tmp_path: Path) -> None:
    logger = logging_setup.init_logging(
        "NonBlockingTest",
        tmp_path,
        max_queue_size=5,
        queue_poll_interval=0.001,
        drain_delay=0.02,
    )

    start = time.perf_counter()
    for idx in range(200):
        logger.info("msg-%s", idx)
    duration = time.perf_counter() - start

    assert duration < 1.0

    time.sleep(0.3)
    stats = logging_setup.get_queue_stats()
    assert stats["max_size"] == 5
    assert stats["dropped"] > 0

    logging_setup._cleanup_logging("NonBlockingTest")


def test_listener_stop_returns_promptly(tmp_path: Path) -> None:
    logging_setup.init_logging(
        "StopTest",
        tmp_path,
        max_queue_size=10,
        queue_poll_interval=0.005,
    )
    time.sleep(0.05)

    start = time.perf_counter()
    logging_setup._cleanup_logging("StopTest")
    duration = time.perf_counter() - start

    assert duration < 0.5
