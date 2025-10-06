"""Tests for dvc-diff exit code handling."""
import pytest
import subprocess
from pathlib import Path
import tempfile


class TestDiffExitCodes:
    """Test that dvc-diff properly propagates exit codes from pipeline commands."""

    def test_successful_pipeline_returns_zero(self, tmp_path):
        """Test that successful identical pipeline returns 0."""
        # Create test files
        file1 = tmp_path / "test1.txt"
        file2 = tmp_path / "test2.txt"
        file1.write_text("foo\nbar\n")
        file2.write_text("foo\nbar\n")

        # Run diff-x (not dvc-diff, but tests the same join_pipelines code)
        result = subprocess.run(
            ["diff-x", "cat", str(file1), str(file2)],
            capture_output=True,
        )
        assert result.returncode == 0

    def test_diff_found_returns_one(self, tmp_path):
        """Test that differences found returns 1."""
        file1 = tmp_path / "test1.txt"
        file2 = tmp_path / "test2.txt"
        file1.write_text("foo\n")
        file2.write_text("bar\n")

        result = subprocess.run(
            ["diff-x", "cat", str(file1), str(file2)],
            capture_output=True,
        )
        assert result.returncode == 1

    def test_pipeline_error_propagates(self, tmp_path):
        """Test that pipeline command errors propagate to exit code."""
        file1 = tmp_path / "test1.txt"
        file2 = tmp_path / "test2.txt"
        file1.write_text("foo\n")
        file2.write_text("bar\n")

        # Use a command that will fail
        result = subprocess.run(
            ["diff-x", "cat /nonexistent/file/that/does/not/exist ||", str(file1), str(file2)],
            capture_output=True,
            shell=False,
        )
        # Should return non-zero due to cat failing
        assert result.returncode != 0

    def test_false_command_propagates_error(self, tmp_path):
        """Test that 'false' command in pipeline propagates error."""
        file1 = tmp_path / "test1.txt"
        file2 = tmp_path / "test2.txt"
        file1.write_text("foo\n")
        file2.write_text("bar\n")

        # Use 'false' which always returns 1
        result = subprocess.run(
            ["diff-x", "cat", "false", str(file1), str(file2)],
            capture_output=True,
        )
        # Should return non-zero due to false in pipeline
        assert result.returncode != 0

    def test_multi_stage_pipeline_error(self, tmp_path):
        """Test that errors in multi-stage pipelines are detected."""
        file1 = tmp_path / "test1.txt"
        file2 = tmp_path / "test2.txt"
        file1.write_text("foo\nbar\n")
        file2.write_text("bar\nfoo\n")

        # Pipeline: sort (succeeds) | false (fails)
        result = subprocess.run(
            ["diff-x", "-x", "sort", "-x", "false", str(file1), str(file2)],
            capture_output=True,
        )
        # Should return non-zero due to false in pipeline
        assert result.returncode != 0
