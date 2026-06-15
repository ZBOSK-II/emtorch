<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# Subtask: logger-float-matcher

## Description
Scans the log output of another subtask for a floating-point value extracted using a regular expression. The regex must contain a named capture group `(?P<value>...)` that identifies the float to capture. This subtask is used to collect decimal numerical metrics from command output for analysis or validation.

## Use Cases
- Extracting floating-point performance metrics (throughput, latency, etc.)
- Collecting decimal sensor readings (temperature, voltage, pressure)
- Parsing measurement results with fractional values
- Validating that measured values fall within expected tolerance ranges
- Gathering statistical data (averages, percentages) across experiment cases

## Configuration Arguments

### Required Arguments
- **value** (string): Name to assign to the extracted value for storage and reference.
- **pattern** (string): Regular expression containing a named capture group `(?P<value>...)` that matches the float to extract. For example: `latency=(?P<value>\d+\.\d+)`.
- **subtask** (string): Name of the subtask whose log output should be scanned. This must match the `name` of another subtask defined in the same experiment.

### Optional Arguments
None.

## Result
Returns SUCCESS if the pattern is found and the float value is successfully extracted. Returns FAILURE if the pattern is not found in the log or the captured value cannot be parsed as a float.

## Example Configuration

```toml
[[actions]]
type = "shell"
name = "measure_latency"

[actions.args]
cmd = "echo 'Latency: 12.5 ms Loss: 0.3%'"
timeout = 5

[[checks]]
type = "logger-float-matcher"
name = "extract_latency"

[checks.args]
value = "latency_ms"
pattern = "Latency: (?P<value>\\d+\\.\\d+)"
subtask = "measure_latency"
```

```toml
[[checks]]
type = "logger-float-matcher"
name = "extract_loss"

[checks.args]
value = "packet_loss_pct"
pattern = "Loss: (?P<value>\\d+\\.\\d+)"
subtask = "measure_latency"
```

## Notes
- The regular expression must include exactly one named group: `(?P<value>...)`.
- In TOML configuration, backslashes in regex patterns must be escaped (e.g., `\\d` instead of `\d`, `\\.` instead of `\.`).
- The `subtask` reference must point to a subtask that has already executed in the same experiment phase.
- Use `logger-int-matcher` for extracting integer values.
- The extracted value is stored and can be used for conditional logic or reporting in subsequent phases.
- Multiple logger matchers can reference the same subtask to extract different values from its output.

## See Also
- [logger-int-matcher](./logger-int-matcher.md) — Extract integer values from logs
- [shell](./shell.md) — Generate output to be scanned by logger matchers
