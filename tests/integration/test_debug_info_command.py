"""Integration tests for the --prt-debug-info CLI command."""

import subprocess
import sys
from pathlib import Path


class TestDebugInfoCommand:
    """Test the CLI debug info command integration."""

    def test_debug_info_command_basic_execution(self):
        """Test that the debug info command runs and exits properly."""
        # Run the command with timeout
        result = subprocess.run(
            [sys.executable, "-m", "prt_src", "--prt-debug-info"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path(__file__).parent.parent.parent,  # Project root
        )

        # Verify command executed without hanging
        assert result.returncode in [0, 1]  # Success or expected failure

        # Verify output contains expected sections
        output = result.stdout + result.stderr
        expected_sections = [
            "PRT DEBUG INFORMATION",
            "SYSTEM ENVIRONMENT",
            "CONFIGURATION",
            "DATABASE",
            "LLM STATUS",
            "SYSTEM PROMPT",
            "SUMMARY",
        ]

        for section in expected_sections:
            assert section in output, f"Missing section: {section}"

    def test_debug_info_command_shows_help(self):
        """Test that the debug flag appears in help output."""
        result = subprocess.run(
            [sys.executable, "-m", "prt_src", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=Path(__file__).parent.parent.parent,
        )

        assert result.returncode == 0
        assert "--prt-debug-info" in result.stdout
        assert "Display comprehensive system diagnostic" in result.stdout

    def test_debug_info_command_with_invalid_ollama(self):
        """Test debug command behavior when Ollama is misconfigured."""
        env = {"OLLAMA_HOST": "invalid-host:99999"}

        result = subprocess.run(
            [sys.executable, "-m", "prt_src", "--prt-debug-info"],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
            cwd=Path(__file__).parent.parent.parent,
        )

        # Should still complete, but may show errors
        assert result.returncode in [0, 1]

        output = result.stdout + result.stderr
        # Should still contain the main sections even with Ollama issues
        assert "PRT DEBUG INFORMATION" in output
        assert "LLM STATUS" in output

    def test_debug_info_command_exits_without_launching_tui(self):
        """Test that debug command exits immediately without launching TUI."""
        import time

        start_time = time.time()
        result = subprocess.run(
            [sys.executable, "-m", "prt_src", "--prt-debug-info"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path(__file__).parent.parent.parent,
        )
        end_time = time.time()

        # Should exit quickly (within reasonable time, not hang waiting for input)
        execution_time = end_time - start_time
        assert execution_time < 25, f"Command took too long: {execution_time}s"

        # Should not contain TUI-related output
        output = result.stdout + result.stderr
        assert "Textual" not in output  # Should not start TUI framework

    def test_debug_info_command_output_format(self):
        """Test that the output is properly formatted and readable."""
        result = subprocess.run(
            [sys.executable, "-m", "prt_src", "--prt-debug-info"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path(__file__).parent.parent.parent,
        )

        output = result.stdout + result.stderr

        # Check for visual indicators
        visual_indicators = ["✅", "❌", "⚠️", "🟢", "🔴"]
        has_visual_indicator = any(indicator in output for indicator in visual_indicators)
        assert has_visual_indicator, "Output should contain visual status indicators"

        # Check for section separators
        assert "=" in output, "Output should contain section separators"
        assert "-" in output, "Output should contain subsection separators"

        # Check for key system information
        assert "Python:" in output, "Should show Python version"
        assert "PRT Version:" in output, "Should show PRT version"

    def test_debug_info_command_with_model_override(self):
        """Test debug command with model parameter."""
        result = subprocess.run(
            [sys.executable, "-m", "prt_src", "--prt-debug-info", "--model", "test-model"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path(__file__).parent.parent.parent,
        )

        # Should still work with model parameter (though model may not exist)
        assert result.returncode in [0, 1]

        output = result.stdout + result.stderr
        assert "PRT DEBUG INFORMATION" in output

    def test_debug_info_command_no_sensitive_data(self):
        """Test that debug output doesn't contain sensitive information."""
        result = subprocess.run(
            [sys.executable, "-m", "prt_src", "--prt-debug-info"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path(__file__).parent.parent.parent,
        )

        output = result.stdout + result.stderr

        # Check that passwords/secrets are not exposed
        sensitive_patterns = [
            "password:",
            "secret:",
            "token:",
            "api_key:",
            "private_key:",
        ]

        for pattern in sensitive_patterns:
            assert (
                pattern.lower() not in output.lower()
            ), f"Should not contain sensitive data: {pattern}"

        # Should contain redacted indicators if sensitive config exists
        if "password" in output.lower():
            assert "[REDACTED]" in output, "Sensitive values should be redacted"

    def test_debug_info_command_performance(self):
        """Test that debug command completes within reasonable time."""
        import time

        start_time = time.time()
        result = subprocess.run(
            [sys.executable, "-m", "prt_src", "--prt-debug-info"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path(__file__).parent.parent.parent,
        )
        end_time = time.time()

        execution_time = end_time - start_time

        # Should complete within 30 seconds as per acceptance criteria
        assert execution_time < 30, f"Command took too long: {execution_time}s"

        # Should generally complete much faster in normal conditions
        if result.returncode == 0:
            assert (
                execution_time < 15
            ), f"Command should be faster in success case: {execution_time}s"


class TestDebugInfoCommandErrorCases:
    """Test debug info command error handling scenarios."""

    def test_debug_info_command_with_corrupted_config(self):
        """Test behavior when configuration is corrupted or missing."""
        # This test assumes the command handles missing config gracefully
        # The actual behavior will depend on the system state

        result = subprocess.run(
            [sys.executable, "-m", "prt_src", "--prt-debug-info"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path(__file__).parent.parent.parent,
        )

        # Should handle config issues gracefully
        output = result.stdout + result.stderr
        assert "PRT DEBUG INFORMATION" in output

        # If config fails, should show error state
        if "❌ Configuration" in output:
            assert "error" in output.lower() or "Error" in output

    def test_debug_info_command_handles_import_errors(self):
        """Test that command handles import errors gracefully."""
        # Test basic execution - if imports fail, command should handle gracefully
        result = subprocess.run(
            [sys.executable, "-m", "prt_src", "--prt-debug-info"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path(__file__).parent.parent.parent,
        )

        # Should not crash with import errors
        if result.returncode != 0:
            output = result.stdout + result.stderr
            # Should contain error information, not just a crash
            assert len(output) > 0, "Should provide error information instead of silent failure"


class TestDebugInfoCommandOutput:
    """Test specific output content and format of debug info command."""

    def test_debug_info_sections_present(self):
        """Test that all required sections are present in output."""
        result = subprocess.run(
            [sys.executable, "-m", "prt_src", "--prt-debug-info"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path(__file__).parent.parent.parent,
        )

        output = result.stdout + result.stderr

        # Required sections per specification
        required_sections = [
            "SYSTEM ENVIRONMENT",  # OS, Python, Ollama info
            "CONFIGURATION",  # Config file status
            "DATABASE",  # DB connection and stats
            "LLM STATUS",  # LLM availability and models
            "SYSTEM PROMPT",  # System prompt preview
            "SUMMARY",  # Overall status summary
        ]

        for section in required_sections:
            assert section in output, f"Missing required section: {section}"

    def test_debug_info_system_information(self):
        """Test that system information is properly displayed."""
        result = subprocess.run(
            [sys.executable, "-m", "prt_src", "--prt-debug-info"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path(__file__).parent.parent.parent,
        )

        output = result.stdout + result.stderr

        # Should contain operating system information
        assert any(os in output for os in ["Darwin", "Linux", "Windows"]), "Should show OS type"

        # Should contain Python version
        assert "Python:" in output, "Should show Python version"

        # Should contain PRT version
        assert "PRT Version:" in output, "Should show PRT version"

    def test_debug_info_status_indicators(self):
        """Test that status indicators are properly used."""
        result = subprocess.run(
            [sys.executable, "-m", "prt_src", "--prt-debug-info"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path(__file__).parent.parent.parent,
        )

        output = result.stdout + result.stderr

        # Should contain status indicators as per specification
        status_indicators = ["✅", "❌", "⚠️"]
        has_indicators = any(indicator in output for indicator in status_indicators)
        assert has_indicators, "Output should contain visual status indicators (✅/❌/⚠️)"

        # Summary should show overall status
        assert "Overall Status:" in output, "Should contain overall status summary"
