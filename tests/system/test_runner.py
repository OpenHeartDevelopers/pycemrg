# tests/system/test_runner.py

import pytest
import sys
import logging
from pathlib import Path

# The classes we are testing from our library
from pycemrg.system import CommandRunner, CommandExecutionError

# A simple, cross-platform Python script to use in our tests
# We can control its exit code, stdout, and stderr.
SCRIPT_TEMPLATE = """
import sys
from pathlib import Path

# Create a file if its path is provided
if "{file_to_create}":
    Path("{file_to_create}").touch()

# Write to stdout and stderr
sys.stdout.write("{stdout_msg}")
sys.stderr.write("{stderr_msg}")
sys.exit({exit_code})
"""

class TestCommandRunner:
    """Test suite for the CommandRunner class."""

    def test_run_success(self, tmp_path, caplog):
        """Verify a successful command execution and its stdout."""
        runner = CommandRunner()
        script = SCRIPT_TEMPLATE.format(
            file_to_create="", stdout_msg="Success!", stderr_msg="", exit_code=0
        )
        cmd = [sys.executable, "-c", script]

        with caplog.at_level(logging.INFO):
            stdout = runner.run(cmd)

        assert stdout == "Success!"
        assert f"Executing command: {' '.join(cmd)}" in caplog.text

    def test_run_success_with_output_validation(self, tmp_path):
        """Verify the check for expected_outputs passes when file is created."""
        runner = CommandRunner()
        output_file = tmp_path / "output.txt"
        script = SCRIPT_TEMPLATE.format(
            file_to_create=output_file, stdout_msg="", stderr_msg="", exit_code=0
        )
        cmd = [sys.executable, "-c", script]

        # This test passes if no exception is raised
        runner.run(cmd, expected_outputs=[output_file])
        assert output_file.exists()

    def test_run_fails_with_exception(self, tmp_path):
        """Verify a failing command raises CommandExecutionError."""
        runner = CommandRunner()
        script = SCRIPT_TEMPLATE.format(
            file_to_create="", stdout_msg="out", stderr_msg="Error 123", exit_code=123
        )
        cmd = [sys.executable, "-c", script]

        with pytest.raises(CommandExecutionError) as exc_info:
            runner.run(cmd)

        # Assert the exception object has the correct context
        assert exc_info.value.returncode == 123
        assert exc_info.value.stdout == "out"
        assert "Error 123" in exc_info.value.stderr
        assert "Command failed" in str(exc_info.value)

    def test_run_fails_with_ignored_error(self, tmp_path, caplog):
        """Verify that a matching ignored error prevents the exception."""
        runner = CommandRunner()
        script = SCRIPT_TEMPLATE.format(
            file_to_create="", stdout_msg="", stderr_msg="Benign error occurred.", exit_code=1
        )
        cmd = [sys.executable, "-c", script]
        
        with caplog.at_level(logging.WARNING):
            # This should NOT raise an exception
            runner.run(cmd, ignore_errors=["Benign error"])

        assert "contained an ignored error string" in caplog.text
        assert any(record.levelno == logging.WARNING for record in caplog.records)

    def test_run_fails_on_missing_output(self, tmp_path):
        """Verify a FileNotFoundError is raised if expected output is missing."""
        runner = CommandRunner()
        missing_file = tmp_path / "should_exist.txt"
        script = SCRIPT_TEMPLATE.format(
            file_to_create="", stdout_msg="", stderr_msg="", exit_code=0
        )
        cmd = [sys.executable, "-c", script]

        with pytest.raises(FileNotFoundError) as exc_info:
            runner.run(cmd, expected_outputs=[missing_file])
        
        assert str(missing_file) in str(exc_info.value)

    def test_run_with_path_objects_in_cmd(self, tmp_path):
        """Verify the command list can contain pathlib.Path objects."""
        runner = CommandRunner()
        test_file = tmp_path / "test.txt"
        # Using a real command here is fine because 'touch' is simple.
        # However, for consistency, we stick to the Python executable.
        script = f"from pathlib import Path; Path('{test_file}').touch()"
        
        # Pass the Path object directly in the command list
        cmd = [sys.executable, "-c", script]

        runner.run(cmd)
        assert test_file.exists()

    def test_run_with_custom_logger(self, caplog):
        """Verify that a custom logger can be injected and is used."""
        # Create a logger with a unique name
        custom_logger = logging.getLogger("MyCustomLogger")
        runner = CommandRunner(logger=custom_logger)
        
        cmd = [sys.executable, "-c", "print('hello')"]
        
        runner.run(cmd)
        
        # Check that the log records were emitted by our custom logger
        assert all(record.name == "MyCustomLogger" for record in caplog.records)