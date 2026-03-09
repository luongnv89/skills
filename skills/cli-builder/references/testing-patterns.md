# CLI Testing Patterns

Testing patterns for CLI tools across languages. Every CLI built with the cli-builder skill should have tests covering these categories.

## General Principles

1. **Test output**: verify stdout contains expected text
2. **Test exit codes**: 0 for success, non-zero for errors
3. **Test stderr**: error messages go to stderr, not stdout
4. **Test help text**: `--help` produces useful output and exits 0
5. **Test edge cases**: missing args, invalid options, empty input

## Exit Code Conventions

| Code | Meaning | When to use |
|------|---------|-------------|
| 0 | Success | Command completed normally |
| 1 | Runtime error | Unexpected failure during execution |
| 2 | Usage error | Invalid arguments, missing required options |
| 3 | Input error | Invalid input data (bad file, malformed JSON) |
| 130 | Interrupted | User pressed Ctrl+C (128 + SIGINT=2) |

## Test Categories

### Unit Tests
Test individual command handler functions in isolation (no subprocess, no I/O).

### Integration Tests
Run the CLI as a subprocess and verify stdout, stderr, and exit code.

### Help/Usage Tests
Verify `--help` at every command level produces correct output.

---

## Python (click)

### Unit tests with CliRunner

```python
# tests/test_cli.py
from click.testing import CliRunner
from mytool.cli import cli

def test_greet():
    runner = CliRunner()
    result = runner.invoke(cli, ["greet", "World"])
    assert result.exit_code == 0
    assert "Hello, World!" in result.output

def test_greet_custom_greeting():
    runner = CliRunner()
    result = runner.invoke(cli, ["greet", "--greeting", "Hi", "World"])
    assert result.exit_code == 0
    assert "Hi, World!" in result.output

def test_greet_missing_name():
    runner = CliRunner()
    result = runner.invoke(cli, ["greet"])
    assert result.exit_code != 0
    assert "Missing argument" in result.output

def test_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output

def test_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
```

### Integration tests with subprocess

```python
# tests/test_cli_integration.py
import subprocess
import sys

def run_cli(*args):
    result = subprocess.run(
        [sys.executable, "-m", "mytool", *args],
        capture_output=True, text=True
    )
    return result

def test_greet_subprocess():
    result = run_cli("greet", "World")
    assert result.returncode == 0
    assert "Hello, World!" in result.stdout

def test_invalid_command_subprocess():
    result = run_cli("nonexistent")
    assert result.returncode != 0
    assert result.stderr  # error message present

def test_help_subprocess():
    result = run_cli("--help")
    assert result.returncode == 0
    assert "Usage:" in result.stdout
```

### Python (argparse)

Same subprocess pattern. For unit tests, call the handler functions directly:

```python
def test_greet_handler():
    from mytool.cli import handle_greet
    # Test the function directly, not through argparse
    output = handle_greet(name="World", greeting="Hello")
    assert output == "Hello, World!"
```

---

## JavaScript / TypeScript (commander)

### Unit tests with Jest

```javascript
// tests/cli.test.js
const { execFileSync } = require("child_process");
const path = require("path");

const CLI = path.resolve(__dirname, "../src/cli.js");

function runCli(...args) {
  try {
    const stdout = execFileSync("node", [CLI, ...args], {
      encoding: "utf-8",
      timeout: 5000,
    });
    return { stdout, exitCode: 0 };
  } catch (err) {
    return {
      stdout: err.stdout || "",
      stderr: err.stderr || "",
      exitCode: err.status,
    };
  }
}

test("greet outputs greeting", () => {
  const { stdout, exitCode } = runCli("greet", "World");
  expect(exitCode).toBe(0);
  expect(stdout).toContain("Hello, World!");
});

test("greet with custom greeting", () => {
  const { stdout, exitCode } = runCli("greet", "World", "-g", "Hi");
  expect(exitCode).toBe(0);
  expect(stdout).toContain("Hi, World!");
});

test("help flag works", () => {
  const { stdout, exitCode } = runCli("--help");
  expect(exitCode).toBe(0);
  expect(stdout).toContain("Usage:");
});

test("version flag works", () => {
  const { stdout, exitCode } = runCli("--version");
  expect(exitCode).toBe(0);
});

test("unknown command fails", () => {
  const { exitCode, stderr } = runCli("nonexistent");
  expect(exitCode).not.toBe(0);
});
```

### With execa (modern alternative)

```javascript
// tests/cli.test.js
const { execa } = require("execa");

async function runCli(...args) {
  try {
    const result = await execa("node", ["src/cli.js", ...args]);
    return { stdout: result.stdout, exitCode: 0 };
  } catch (err) {
    return { stdout: err.stdout, stderr: err.stderr, exitCode: err.exitCode };
  }
}

test("greet outputs greeting", async () => {
  const { stdout, exitCode } = await runCli("greet", "World");
  expect(exitCode).toBe(0);
  expect(stdout).toContain("Hello, World!");
});
```

---

## Go (cobra)

### Unit tests with cobra's built-in test support

```go
// cmd/root_test.go
package cmd

import (
	"bytes"
	"strings"
	"testing"
)

func executeCommand(args ...string) (string, error) {
	buf := new(bytes.Buffer)
	rootCmd.SetOut(buf)
	rootCmd.SetErr(buf)
	rootCmd.SetArgs(args)
	err := rootCmd.Execute()
	return buf.String(), err
}

func TestGreet(t *testing.T) {
	output, err := executeCommand("greet", "World")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !strings.Contains(output, "Hello, World!") {
		t.Errorf("expected greeting, got: %s", output)
	}
}

func TestGreetCustomGreeting(t *testing.T) {
	output, err := executeCommand("greet", "World", "--greeting", "Hi")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !strings.Contains(output, "Hi, World!") {
		t.Errorf("expected custom greeting, got: %s", output)
	}
}

func TestHelp(t *testing.T) {
	output, err := executeCommand("--help")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !strings.Contains(output, "Usage:") {
		t.Errorf("expected usage info, got: %s", output)
	}
}
```

### Integration tests with os/exec

```go
// cmd/integration_test.go
package cmd_test

import (
	"os/exec"
	"strings"
	"testing"
)

func TestGreetIntegration(t *testing.T) {
	cmd := exec.Command("go", "run", ".", "greet", "World")
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("command failed: %v\noutput: %s", err, output)
	}
	if !strings.Contains(string(output), "Hello, World!") {
		t.Errorf("expected greeting, got: %s", output)
	}
}

func TestInvalidCommand(t *testing.T) {
	cmd := exec.Command("go", "run", ".", "nonexistent")
	err := cmd.Run()
	if err == nil {
		t.Error("expected error for invalid command")
	}
}
```

---

## Rust (clap)

### Unit tests with assert_cmd and predicates

```toml
# Cargo.toml
[dev-dependencies]
assert_cmd = "2"
predicates = "3"
```

```rust
// tests/cli.rs
use assert_cmd::Command;
use predicates::prelude::*;

#[test]
fn test_greet() {
    Command::cargo_bin("mytool")
        .unwrap()
        .args(["greet", "World"])
        .assert()
        .success()
        .stdout(predicate::str::contains("Hello, World!"));
}

#[test]
fn test_greet_custom_greeting() {
    Command::cargo_bin("mytool")
        .unwrap()
        .args(["greet", "World", "--greeting", "Hi"])
        .assert()
        .success()
        .stdout(predicate::str::contains("Hi, World!"));
}

#[test]
fn test_greet_missing_name() {
    Command::cargo_bin("mytool")
        .unwrap()
        .args(["greet"])
        .assert()
        .failure()
        .stderr(predicate::str::contains("required"));
}

#[test]
fn test_help() {
    Command::cargo_bin("mytool")
        .unwrap()
        .arg("--help")
        .assert()
        .success()
        .stdout(predicate::str::contains("Usage:"));
}

#[test]
fn test_version() {
    Command::cargo_bin("mytool")
        .unwrap()
        .arg("--version")
        .assert()
        .success();
}
```

### Inline unit tests

```rust
// src/main.rs (at the bottom)
#[cfg(test)]
mod tests {
    use super::*;
    use clap::Parser;

    #[test]
    fn test_cli_parse_greet() {
        let cli = Cli::parse_from(["mytool", "greet", "World"]);
        match cli.command {
            Commands::Greet { name, greeting } => {
                assert_eq!(name, "World");
                assert_eq!(greeting, "Hello");
            }
        }
    }

    #[test]
    fn test_cli_parse_verbose() {
        let cli = Cli::parse_from(["mytool", "--verbose", "greet", "World"]);
        assert!(cli.verbose);
    }
}
```

---

## Common Patterns (all languages)

### Testing stdin input

```python
# Python
def test_stdin_input():
    runner = CliRunner()
    result = runner.invoke(cli, ["process"], input="line1\nline2\n")
    assert result.exit_code == 0
```

```javascript
// JavaScript
test("reads from stdin", () => {
  const result = execSync('echo "hello" | node src/cli.js process', {
    encoding: "utf-8",
  });
  expect(result).toContain("hello");
});
```

```go
// Go
func TestStdinInput(t *testing.T) {
    cmd := exec.Command("go", "run", ".", "process")
    cmd.Stdin = strings.NewReader("line1\nline2\n")
    output, err := cmd.Output()
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
    if !strings.Contains(string(output), "line1") {
        t.Errorf("expected stdin content, got: %s", output)
    }
}
```

### Testing JSON output

```python
# Python
import json

def test_json_output():
    runner = CliRunner()
    result = runner.invoke(cli, ["list", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
```

```javascript
// JavaScript
test("json output is valid", () => {
  const { stdout } = runCli("list", "--format", "json");
  const data = JSON.parse(stdout);
  expect(Array.isArray(data)).toBe(true);
});
```

### Testing error output goes to stderr

```python
# Python
def test_error_to_stderr():
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(cli, ["invalid-input"])
    assert result.exit_code != 0
    assert result.stderr  # error is on stderr
    assert not result.output  # stdout is clean
```

```go
// Go
func TestErrorToStderr(t *testing.T) {
    cmd := exec.Command("go", "run", ".", "invalid")
    var stderr bytes.Buffer
    cmd.Stderr = &stderr
    err := cmd.Run()
    if err == nil {
        t.Error("expected error")
    }
    if stderr.Len() == 0 {
        t.Error("expected error message on stderr")
    }
}
```
