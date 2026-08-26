<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# Subtask: echo

## Description
Prints a provided message to the experiment log. This is the simplest subtask in emtorch, useful for annotating logs, displaying intermediate results, or debugging experiment workflows.

## Use Cases
- Logging progress messages during experiment phases
- Displaying parameter values or computed results
- Debugging and verifying experiment flow
- Adding human-readable annotations to log output
- Marking phase boundaries in the experiment timeline

## Configuration Arguments

### Required Arguments
- **message** ($-string): The message to write to the log. Supports template variables.

### Optional Arguments
None.

## Result
Always returns SUCCESS. The message is recorded in the subtask log output.

## Example Configuration

```toml
[[setups]]
type = "echo"
name = "greeting"

[setups.args]
message = "Starting experiment case $EMTORCH_CASE_ID"
```

```toml
[[actions]]
type = "echo"
name = "report_result"

[actions.args]
message = "Processing complete for $EMTORCH_DATA_FILENAME"
```

## Notes
- The message supports all standard template variables (`$EMTORCH_CASE_ID`, `$EMTORCH_DATA_PATH`, `$EMTORCH_DATA_FILENAME`).
- No result is returned beyond the SUCCESS status — this subtask is purely for logging and annotation.
- Useful as the first subtask in a phase to document what is about to happen.

## See Also
- [shell](./shell.md) — Execute shell commands that can also produce output
- [file-write](./file-write.md) — Write messages to files instead of logs
