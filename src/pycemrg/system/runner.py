# src/pycemrg/system/runner.py

import subprocess
import logging
from pathlib import Path
from typing import List, Union, Optional, Sequence

# A custom exception provides more context to the caller upon failure.
class CommandExecutionError(RuntimeError):
    """Custom exception for command execution failures."""
    def __init__(self, message, returncode, stdout, stderr):
        super().__init__(message)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

class CommandRunner:
    """
    A robust utility for running and logging external shell commands.
    
    This class provides a safe, consistent interface for executing system
    commands, capturing their output, and validating results.
    """
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initializes the CommandRunner.

        Args:
            logger (Optional[logging.Logger]): An existing logger instance.
                If None, a new logger for this module will be created.
                This allows the application to control logging policy.
        """
        self.logger = logger or logging.getLogger(__name__)

    def run(
        self,
        cmd: Sequence[Union[str, Path]],
        expected_outputs: Optional[Sequence[Path]] = None,
        cwd: Optional[Path] = None,
        ignore_errors: Optional[Sequence[str]] = None
    ) -> str:
        """
        Executes a command safely without using a shell.

        Args:
            cmd (Sequence[Union[str, Path]]): List of command parts. Each part
                is converted to a string (e.g., ['docker', 'run', Path('/tmp')]).
            expected_outputs (Optional[Sequence[Path]]): A sequence of Path
                objects that are expected to exist after a successful run.
            cwd (Optional[Path]): The working directory from which to run the command.
            ignore_errors (Optional[Sequence[str]]): A sequence of strings. If any of these
                strings are found in stderr, the error is logged as a warning
                but does not raise an exception.

        Returns:
            str: The captured stdout from the command.

        Raises:
            CommandExecutionError: If the command returns a non-zero exit code
                and the error is not in the `ignore_errors` list.
            FileNotFoundError: If the command completes successfully but an
                expected output file is missing.
        """
        # Convert all command parts to strings for subprocess
        cmd_str_list = [str(c) for c in cmd]
        cmd_log_str = " ".join(cmd_str_list)
        self.logger.info(f"Executing command: {cmd_log_str}")

        try:
            result = subprocess.run(
                cmd_str_list,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False  # We handle the return code manually for richer error handling
            )
        except Exception as e:
            self.logger.error(f"Failed to launch command: {cmd_log_str}", exc_info=True)
            raise e

        # Log stdout/stderr only if they contain content.
        if result.stdout:
            self.logger.debug(f"STDOUT:\n{result.stdout.strip()}")
        
        if result.stderr:
            self.logger.debug(f"STDERR:\n{result.stderr.strip()}")

        # Handle non-zero return codes
        if result.returncode != 0:
            stderr_msg = result.stderr.strip()
            
            is_benign = False
            if ignore_errors:
                for benign_msg in ignore_errors:
                    if benign_msg in stderr_msg:
                        self.logger.warning(
                            f"Command had a non-zero exit but contained an ignored "
                            f"error string ('{benign_msg}'). Treating as success."
                        )
                        is_benign = True
                        break
            
            if not is_benign:
                self.logger.error(
                    f"Command failed with exit code {result.returncode}.\n"
                    f"Command: {cmd_log_str}\n"
                    f"STDERR: {stderr_msg}"
                )
                raise CommandExecutionError(
                    message=f"Command failed: {cmd_log_str}",
                    returncode=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr
                )

        if expected_outputs:
            self._validate_outputs(expected_outputs)

        return result.stdout

    def _validate_outputs(self, expected_files: Sequence[Path]):
        """Checks for the existence of expected output files."""
        missing = [p for p in expected_files if not p.exists()]
        if missing:
            missing_str = ", ".join([str(p) for p in missing])
            self.logger.error(f"Validation failed. Missing expected outputs: {missing_str}")
            raise FileNotFoundError(f"Command finished but required outputs are missing: {missing_str}")
        
        self.logger.debug("All expected outputs found.")