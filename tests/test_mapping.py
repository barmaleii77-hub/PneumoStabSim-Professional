"""
Tests for line and port mapping
"""

import unittest
from src.pneumo.system import create_standard_diagonal_system
from src.pneumo.enums import Line, Wheel, Port
from src.app.config_defaults import create_default_system_configuration


class TestLineMapping(unittest.TestCase):
    """Test pneumatic line mapping and connections"""

    def setUp(self):
        """Setup test system"""
        config = create_default_system_configuration()
        self.system = create_standard_diagonal_system(
            cylinder_specs=config["cylinder_specs"],
            line_configs=config["line_configs"],
            receiver=config["receiver"],
            master_isolation_open=False,
        )

    def test_diagonal_connection_scheme(self):
        """Test the standard diagonal connection scheme"""
        expected_connections = {
            Line.A1: {(Wheel.LP, Port.ROD), (Wheel.PZ, Port.HEAD)},
            Line.B1: {(Wheel.LP, Port.HEAD), (Wheel.PZ, Port.ROD)},
            Line.A2: {(Wheel.PP, Port.ROD), (Wheel.LZ, Port.HEAD)},
            Line.B2: {(Wheel.PP, Port.HEAD), (Wheel.LZ, Port.ROD)},
        }

        for line_name, expected_endpoints in expected_connections.items():
            with self.subTest(line=line_name):
                line = self.system.lines[line_name]
                actual_endpoints = set(line.endpoints)

                self.assertEqual(
                    actual_endpoints,
                    expected_endpoints,
                    f"Line {line_name.value} has incorrect connections",
                )

    def test_all_wheels_connected(self):
        """Test that all wheels are connected in the system"""
        expected_wheels = {Wheel.LP, Wheel.PP, Wheel.LZ, Wheel.PZ}
        actual_wheels = set(self.system.cylinders.keys())

        self.assertEqual(actual_wheels, expected_wheels)

    def test_all_lines_present(self):
        """Test that all required lines are present"""
        expected_lines = {Line.A1, Line.B1, Line.A2, Line.B2}
        actual_lines = set(self.system.lines.keys())

        self.assertEqual(actual_lines, expected_lines)

    def test_port_coverage(self):
        """Test that all cylinder ports are connected to exactly one line"""
        # Count connections for each (wheel, port) combination
        port_connections = {}

        for wheel in [Wheel.LP, Wheel.PP, Wheel.LZ, Wheel.PZ]:
            for port in [Port.HEAD, Port.ROD]:
                port_connections[(wheel, port)] = 0

        # Count connections from all lines
        for line in self.system.lines.values():
            for wheel, port in line.endpoints:
                port_connections[(wheel, port)] += 1

        # Each port should be connected exactly once
        for (wheel, port), count in port_connections.items():
            with self.subTest(wheel=wheel, port=port):
                self.assertEqual(
                    count,
                    1,
                    f"Port {wheel.value}:{port.value} connected {count} times (expected 1)",
                )

    def test_diagonal_pairing(self):
        """Test that connections are truly diagonal (front-rear, left-right crossing)"""
        for line_name, line in self.system.lines.items():
            with self.subTest(line=line_name):
                self.assertTrue(
                    line.is_diagonal_connection(),
                    f"Line {line_name.value} is not diagonal: {line.get_connection_description()}",
                )

    def test_connection_symmetry(self):
        """Test connection scheme symmetries"""
        # A1 and A2 should be symmetric (ROD->HEAD connections)
        # B1 and B2 should be symmetric (HEAD->ROD connections)

        # Check A1: LP:ROD ? PZ:HEAD
        a1_line = self.system.lines[Line.A1]
        a1_endpoints = set(a1_line.endpoints)
        self.assertIn((Wheel.LP, Port.ROD), a1_endpoints)
        self.assertIn((Wheel.PZ, Port.HEAD), a1_endpoints)

        # Check A2: PP:ROD ? LZ:HEAD (symmetric to A1)
        a2_line = self.system.lines[Line.A2]
        a2_endpoints = set(a2_line.endpoints)
        self.assertIn((Wheel.PP, Port.ROD), a2_endpoints)
        self.assertIn((Wheel.LZ, Port.HEAD), a2_endpoints)

        # Check B1: LP:HEAD ? PZ:ROD
        b1_line = self.system.lines[Line.B1]
        b1_endpoints = set(b1_line.endpoints)
        self.assertIn((Wheel.LP, Port.HEAD), b1_endpoints)
        self.assertIn((Wheel.PZ, Port.ROD), b1_endpoints)

        # Check B2: PP:HEAD ? LZ:ROD (symmetric to B1)
        b2_line = self.system.lines[Line.B2]
        b2_endpoints = set(b2_line.endpoints)
        self.assertIn((Wheel.PP, Port.HEAD), b2_endpoints)
        self.assertIn((Wheel.LZ, Port.ROD), b2_endpoints)

    def test_line_validation(self):
        """Test that all lines pass validation"""
        for line_name, line in self.system.lines.items():
            with self.subTest(line=line_name):
                result = line.validate_invariants()

                # Should be valid
                self.assertTrue(
                    result["is_valid"],
                    f"Line {line_name.value} validation failed: {result['errors']}",
                )

    def test_connected_cylinders_lookup(self):
        """Test cylinder lookup by line connections"""
        for line_name in [Line.A1, Line.B1, Line.A2, Line.B2]:
            with self.subTest(line=line_name):
                connected = self.system.get_connected_cylinders(line_name)

                # Should have exactly 2 connections
                self.assertEqual(len(connected), 2)

                # Each connection should have wheel, port, and cylinder state
                for wheel, port, cylinder_state in connected:
                    self.assertIsInstance(wheel, Wheel)
                    self.assertIsInstance(port, Port)
                    self.assertIsNotNone(cylinder_state)

                    # Cylinder state should match the one in system
                    expected_cylinder = self.system.cylinders[wheel]
                    self.assertEqual(cylinder_state, expected_cylinder)


class TestSystemInvariants(unittest.TestCase):
    """Test system-level invariants"""

    def setUp(self):
        """Setup test system"""
        config = create_default_system_configuration()
        self.system = create_standard_diagonal_system(
            cylinder_specs=config["cylinder_specs"],
            line_configs=config["line_configs"],
            receiver=config["receiver"],
            master_isolation_open=False,
        )

    def test_system_validation(self):
        """Test complete system validation"""
        result = self.system.validate_invariants()

        # System should be valid
        self.assertTrue(
            result["is_valid"], f"System validation failed: {result['errors']}"
        )

        # Log any warnings
        if result["warnings"]:
            print("\nSystem validation warnings:")
            for warning in result["warnings"]:
                print(f"  - {warning}")

    def test_volume_calculations(self):
        """Test line volume calculations"""
        volumes = self.system.get_line_volumes()

        # Should have volumes for all lines
        expected_lines = {Line.A1, Line.B1, Line.A2, Line.B2}
        actual_lines = set(volumes.keys())
        self.assertEqual(actual_lines, expected_lines)

        # All volumes should be positive
        for line_name, vol_info in volumes.items():
            with self.subTest(line=line_name):
                total_vol = vol_info["total_volume"]
                self.assertGreater(
                    total_vol,
                    0,
                    f"Line {line_name.value} has non-positive volume: {total_vol}",
                )

                # Should have exactly 2 endpoints
                self.assertEqual(len(vol_info["endpoints"]), 2)

                # Endpoint volumes should sum to total
                endpoint_sum = sum(ep["volume"] for ep in vol_info["endpoints"])
                self.assertAlmostEqual(endpoint_sum, total_vol, places=10)


if __name__ == "__main__":
    unittest.main()
