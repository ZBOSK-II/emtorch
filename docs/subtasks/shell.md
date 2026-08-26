<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# Subtask: shell

## Description
Executes a system shell command and captures its output. The command is run through `sh -c`, providing full shell capabilities including pipes, redirection, and command chaining. Waits for command completion or specified timeout.

## Use Cases
- Running system utilities and scripts
- Processing data files with shell tools (grep, awk, sed, etc.)
- Executing test commands and checking their output
- Monitoring system state (CPU, memory, disk usage)
- Chaining multiple commands with pipes and operators
- Creating or manipulating files and directories

## Configuration Arguments

### Required Arguments
- **cmd** ($-string): Shell command to execute.

### Optional Arguments
- **timeout** (float, default 1.0): Maximum execution time in seconds.
- **signal** (string, optional): Signal name to send if timeout occurs (e.g., `SIGTERM`, `SIGKILL`).

## Result
Returns SUCCESS if command exits with code 0, FAILURE if non-zero, ERROR on unexpected errors, TIMEOUT if execution exceeds timeout.

## Example Configuration

```toml
[[actions]]
type = "shell"
name = "process_data"

[actions.args]
cmd = "cat $EMTORCH_DATA_PATH | wc -l"
timeout = 10
```

```toml
[[checks]]
type = "shell"
name = "verify_output"

[checks.args]
cmd = "test -f /tmp/output.txt && grep -q 'SUCCESS' /tmp/output.txt"
timeout = 5
```

## Notes
- Command runs with shell interpretation (`sh -c`), so shell syntax (pipes, `&&`, `||`, redirection) works as expected.
- Output is captured in the subtask log for inspection or subsequent matching.
- Supports template variables in the command string.
- Default timeout is 1 second — increase for commands that take longer to execute.
- For running programs directly without shell features, use the `exec` subtask instead.

## See Also
- [exec](./exec.md) — Run programs directly without shell interpretation
- [remote](./remote.md) — Run shell commands on remote hosts via SSH
- [logger-int-matcher](./logger-int-matcher.md) — Extract integer values from shell output
- [logger-float-matcher](./logger-float-matcher.md) — Extract float values from shell output
