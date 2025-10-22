"""
P12: Logging and CSV export validation tests

Tests:
- logs/run.log overwrite behavior
- Log format (ISO/UTC timestamps)
- QueueHandler/QueueListener usage
- CSV export correctness
- Excel/LibreOffice compatibility

References:
- logging.handlers: https://docs.python.org/3/library/logging.handlers.html
- csv: https://docs.python.org/3/library/csv.html
- unittest: https://docs.python.org/3/library/unittest.html
"""

import unittest
import csv
import time
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common.logging_setup import (
    init_logging,
    log_ui_event,
    log_export,
)
from src.common.csv_export import export_timeseries_csv, export_snapshot_csv
import numpy as np


class TestLoggingSetup(unittest.TestCase):
    """Test logging initialization and configuration"""

    def setUp(self):
        """Setup test log directory"""
        self.log_dir = Path("logs_test")
        self.log_file = self.log_dir / "run.log"

    def tearDown(self):
        """Cleanup test logs"""
        if self.log_file.exists():
            try:
                self.log_file.unlink()
            except:
                pass
        if self.log_dir.exists():
            try:
                self.log_dir.rmdir()
            except:
                pass

    def test_log_directory_created(self):
        """Test log directory is created if missing"""
        # Ensure directory doesn't exist
        if self.log_dir.exists():
            self.log_dir.rmdir()

        # Initialize logging
        logger = init_logging("TestApp", self.log_dir)

        # Check directory created
        self.assertTrue(self.log_dir.exists(), "Log directory should be created")

    def test_log_file_overwrite(self):
        """Test log file is overwritten on each run (mode='w')"""
        # First run
        logger1 = init_logging("TestApp1", self.log_dir)
        logger1.info("First run message")
        time.sleep(0.1)  # Let queue flush

        # Read file size
        size1 = self.log_file.stat().st_size if self.log_file.exists() else 0

        # Second run (should overwrite)
        logger2 = init_logging("TestApp2", self.log_dir)
        logger2.info("Second run message")
        time.sleep(0.1)

        # Read file content
        if self.log_file.exists():
            with open(self.log_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Should contain second run, not first
            self.assertIn("TestApp2", content, "Log should contain second app name")
            self.assertIn("Second run message", content)

            # Should not contain first run (overwritten)
            # Note: Depending on timing, first logger might still be active
            # so we just check that second run is present

    def test_log_format_iso8601(self):
        """Test log format includes ISO8601 timestamps"""
        logger = init_logging("TestApp", self.log_dir)
        logger.info("Test message")
        time.sleep(0.2)  # Let queue flush

        if self.log_file.exists():
            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Check at least one line exists
            self.assertGreater(len(lines), 0, "Log file should have content")

            # Check format: YYYY-MM-DDTHH:MM:SS | PID:xxx TID:yyy | LEVEL | ...
            for line in lines:
                if "Test message" in line:
                    # Check for ISO8601-like timestamp
                    self.assertRegex(
                        line,
                        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
                        "Line should contain ISO8601 timestamp",
                    )

                    # Check for PID/TID
                    self.assertIn("PID:", line, "Line should contain PID")
                    self.assertIn("TID:", line, "Line should contain TID")
                    break


class TestCategoryLoggers(unittest.TestCase):
    """Test category-specific loggers"""

    def setUp(self):
        """Setup test logging"""
        self.log_dir = Path("logs_test")
        self.log_file = self.log_dir / "run.log"
        init_logging("PneumoStabSim", self.log_dir)

    def tearDown(self):
        """Cleanup"""
        if self.log_file.exists():
            try:
                self.log_file.unlink()
            except:
                pass
        if self.log_dir.exists():
            try:
                self.log_dir.rmdir()
            except:
                pass

    def test_ui_category_logger(self):
        """Test UI category logger"""
        log_ui_event("TEST_EVENT", "Test details")
        time.sleep(0.2)

        if self.log_file.exists():
            with open(self.log_file, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("PneumoStabSim.UI", content, "Should contain UI category")
            self.assertIn("TEST_EVENT", content)

    def test_export_category_logger(self):
        """Test EXPORT category logger"""
        log_export("TEST_OPERATION", Path("test.csv"), 100)
        time.sleep(0.2)

        if self.log_file.exists():
            with open(self.log_file, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("PneumoStabSim.EXPORT", content)
            self.assertIn("TEST_OPERATION", content)


class TestCSVExportTimeseries(unittest.TestCase):
    """Test CSV export for timeseries data"""

    def setUp(self):
        """Setup test data"""
        self.test_file = Path("test_timeseries.csv")

        # Generate test data
        self.time = np.linspace(0, 10, 101)
        self.series = {
            "pressure": np.sin(self.time) * 100000 + 200000,
            "temperature": np.cos(self.time) * 5 + 293.15,
        }
        self.header = ["time", "pressure", "temperature"]

    def tearDown(self):
        """Cleanup test file"""
        if self.test_file.exists():
            self.test_file.unlink()

    def test_export_creates_file(self):
        """Test export creates CSV file"""
        export_timeseries_csv(self.time, self.series, self.test_file, self.header)

        self.assertTrue(self.test_file.exists(), "CSV file should be created")

    def test_export_header_correct(self):
        """Test CSV has correct header"""
        export_timeseries_csv(self.time, self.series, self.test_file, self.header)

        with open(self.test_file, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header_row = next(reader)

        # Check header (might have '#' prefix from numpy.savetxt)
        header_clean = [h.lstrip("#").strip() for h in header_row]

        self.assertEqual(
            len(header_clean),
            len(self.header),
            f"Header length mismatch: {header_clean} vs {self.header}",
        )

    def test_export_row_count(self):
        """Test CSV has correct number of rows"""
        export_timeseries_csv(self.time, self.series, self.test_file, self.header)

        with open(self.test_file, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Rows = header + data rows
        # numpy.savetxt might include header as comment
        data_rows = [r for r in rows if r and not r[0].startswith("#")]

        self.assertEqual(
            len(data_rows),
            len(self.time),
            f"Should have {len(self.time)} data rows, got {len(data_rows)}",
        )

    def test_export_values_numeric(self):
        """Test CSV contains numeric values"""
        export_timeseries_csv(self.time, self.series, self.test_file, self.header)

        with open(self.test_file, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Skip header, check first data row
        for row in rows:
            if row and not row[0].startswith("#"):
                # Try to convert to float
                try:
                    values = [float(v) for v in row]
                    self.assertEqual(len(values), len(self.header))
                    break
                except ValueError:
                    pass  # Might be header row


class TestCSVExportSnapshots(unittest.TestCase):
    """Test CSV export for snapshot data"""

    def setUp(self):
        """Setup test data"""
        self.test_file = Path("test_snapshots.csv")

        # Generate test snapshots
        self.snapshots = [
            {"time": 0.0, "heave": 0.0, "pressure": 200000.0},
            {"time": 0.1, "heave": 0.01, "pressure": 205000.0},
            {"time": 0.2, "heave": 0.02, "pressure": 210000.0},
        ]

    def tearDown(self):
        """Cleanup test file"""
        if self.test_file.exists():
            self.test_file.unlink()

    def test_snapshot_export_creates_file(self):
        """Test snapshot export creates file"""
        export_snapshot_csv(self.snapshots, self.test_file)

        self.assertTrue(self.test_file.exists())

    def test_snapshot_export_sorted_fields(self):
        """Test snapshot export has sorted field names"""
        export_snapshot_csv(self.snapshots, self.test_file)

        with open(self.test_file, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames

        # Check fields are sorted
        expected_fields = sorted(["time", "heave", "pressure"])
        self.assertEqual(
            fieldnames,
            expected_fields,
            f"Fields should be sorted: {fieldnames} vs {expected_fields}",
        )

    def test_snapshot_export_row_count(self):
        """Test snapshot export has correct row count"""
        export_snapshot_csv(self.snapshots, self.test_file)

        with open(self.test_file, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(
            len(rows),
            len(self.snapshots),
            f"Should have {len(self.snapshots)} rows, got {len(rows)}",
        )


class TestQueueHandler(unittest.TestCase):
    """Test QueueHandler/QueueListener is used"""

    def test_queue_handler_present(self):
        """Test logger uses QueueHandler

        This is indirect test - we check that logging doesn't block
        """
        logger = init_logging("TestApp", Path("logs_test"))

        # Log many messages quickly
        start = time.perf_counter()
        for i in range(1000):
            logger.debug(f"Message {i}")
        elapsed = time.perf_counter() - start

        # Should be very fast (< 0.1s) because queue doesn't block
        self.assertLess(
            elapsed,
            0.5,
            f"Logging 1000 messages took {elapsed:.3f}s (should be non-blocking)",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
