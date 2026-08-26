<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# Subtask: exec

## Description
Executes a specified program as a subprocess with given arguments and captures its output. Unlike the `shell` subtask, this runs the program directly without shell interpretation, providing more control over argument passing and avoiding shell injection concerns.

## Use Cases
- Running compiled binaries and executables
- Calling Python scripts or other interpreters with precise arguments
- Executing programs where shell interpolation of arguments is undesirable
- Running tools that require specific argument ordering
- Invoking command-line tools with complex argument lists

## Configuration Arguments

### Required Arguments
- **program** ($-string): Path or name of the program to execute.
- **args** (list of $-string): List of arguments to pass to the program.

### Optional Arguments
- **timeout** (float, default 1.0): Maximum execution time in seconds before the process is terminated.
- **signal** (string, optional): Signal name (e.g., `SIGTERM`, `SIGKILL`) to send to the process if timeout occurs or at the end of monitoring.

## Result
Returns SUCCESS if the program exits with code 0, FAILURE if non-zero. Returns ERROR on unexpected errors (e.g., program not found). Returns TIMEOUT if execution exceeds the specified timeout.

## Example Configuration

```toml
[[actions]]
type = "exec"
name = "run_analysis"

[actions.args]
program = "python3"
args = ["analysis.py", "--input", "$EMTORCH_DATA_PATH", "--verbose"]
timeout = 30
signal = "SIGTERM"
```

```toml
[[actions]]
type = "exec"
name = "compile_firmware"

[actions.args]
program = "make"
args = ["-j4", "build"]
timeout = 120
```

## Notes
- The program is executed directly via `subprocess.Popen` — no shell is spawned.
- Each argument is passed as a separate element in the list; no shell quoting or escaping is needed.
- Use the `shell` subtask instead if you need shell features like pipes, redirection, or variable expansion.
- Template variables in arguments are expanded before execution.
- Default timeout is short (1 second) — adjust it appropriately for your program's expected runtime.

## See Also
- [shell](./shell.md) — Run commands with shell interpretation (pipes, redirection, etc.)
- [remote](./remote.md) — Execute programs on remote hosts via SSH
