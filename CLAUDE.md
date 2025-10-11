# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`dvc-utils` is a Python CLI tool for diffing DVC-tracked files between commits or against the worktree. It can optionally pipe file contents through other commands before diffing (e.g., `parquet2json`, `gunzip`, etc.), enabling semantic diffs of binary or compressed formats.

Core functionality: Compare DVC-tracked files at different Git commits by resolving their MD5 hashes from `.dvc` files, looking up cached content in the DVC cache, and piping through optional preprocessing commands before diffing.

## Build & Development Commands

This project uses `uv` for dependency management:

```bash
# Initialize project (first time setup)
uv init

# Install dependencies
uv sync

# Install with test dependencies
uv sync --extra test

# Run tests
pytest

# Run tests (with activated venv)
source .venv/bin/activate
pytest

# Build the package
uv build

# Install in development mode
pip install -e .
```

## Testing

Tests are in `tests/` directory. The test suite uses a DVC-tracked test data repository at `test/data` (submodule of [ryan-williams/dvc-helpers@test]).

Key test commands:
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_diff_exit_codes.py

# Run tests with verbose output (already configured in pytest.ini)
pytest -v
```

The test data directory requires DVC pull:
```bash
cd test/data
dvc pull -r s3 -R -A
```

## Architecture

### Core Module Structure

- **`src/dvc_utils/cli.py`**: Minimal Click group definition (entry point)
- **`src/dvc_utils/main.py`**: Main entry point that invokes the CLI
- **`src/dvc_utils/diff.py`**: Core `dvc-diff` command implementation
  - Parses refspecs (e.g., `HEAD^..HEAD` or single commit)
  - Resolves DVC-tracked file paths to cache paths via MD5 lookups
  - Handles both individual files and DVC-tracked directories
  - Uses `dffs.join_pipelines` to run preprocessing commands on both sides of diff
- **`src/dvc_utils/path.py`**: DVC path resolution utilities
  - `dvc_paths()`: Normalizes path/dvc_path pairs
  - `dvc_md5()`: Extracts MD5 from `.dvc` file at specific Git ref
  - `dvc_cache_path()`: Resolves MD5 to actual cache file path
  - `dvc_cache_dir()`: Finds DVC cache directory (respects `DVC_UTILS_CACHE_DIR` env var)
- **`src/dvc_utils/sync.py`**: Incomplete `pull-x` command (not currently functional)

### Key Dependencies

- **`dffs`**: Provides `join_pipelines()` for executing parallel command pipelines and diffing their outputs
- **`utz`**: Utility library with subprocess wrappers (`utz.process`), error printing (`err`), and file hashing
- **`click`**: CLI framework
- **`pyyaml`**: For parsing `.dvc` YAML files

### How DVC Diffing Works

1. Parse the path argument to get both the data path and `.dvc` file path
2. For each side of the diff (before/after commits):
   - Use `git show <ref>:<path>.dvc` to get the DVC file content at that ref
   - Parse the YAML to extract the MD5 hash
   - Construct cache path: `<cache_dir>/files/md5/<first_2_chars>/<remaining_chars>`
3. If preprocessing commands are specified (e.g., `dvc-diff wc -l foo.dvc`):
   - Use `dffs.join_pipelines()` to run commands on both cache files and diff the outputs
4. Otherwise, run `diff` directly on the two cache files

### DVC Directory Handling

For DVC-tracked directories (`.dvc` files with multiple entries), the tool:
- Parses the directory's `.dvc` file JSON structure
- Compares MD5 hashes for each file in the directory
- Outputs changes as: `filename: <old_md5> -> <new_md5>`

### Exit Code Behavior

The tool propagates exit codes correctly:
- `0`: No differences found
- `1`: Differences found (standard `diff` behavior)
- `>1`: Error in preprocessing pipeline or diff execution

## Entry Points

Defined in `pyproject.toml`:
- `dvc-utils`: Main entry point (currently just invokes CLI group)
- `dvc-diff`: Direct entry to diff command

## Environment Variables

- `DVC_UTILS_CACHE_DIR`: Override DVC cache directory location (relative to git root)
- `SHELL`: Used as default shell for executing preprocessing commands
- `BMDF_WORKDIR`: Used in CI for running README example verification from subdirectory

## CI/CD Notes

- Uses GitHub Actions (`.github/workflows/ci.yml`)
- Tests run on every push/PR to main
- Releases to PyPI on version tags (`v**`)
- README examples are verified using `bmdf` (bash-markdown-fence) in the `test/data` directory
- Requires `parquet2json` (Rust tool) for Parquet-related examples
- AWS credentials needed for DVC remote access in tests
