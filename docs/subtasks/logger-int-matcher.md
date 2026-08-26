<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# Subtask: logger-int-matcher

## Description
Scans the log output of another subtask for an integer value extracted using a regular expression. The regex must contain a named capture group `(?P<value>...)` that identifies the integer to capture. This subtask is used to collect numerical metrics from command output for analysis or validation.

## Use Cases
- Extracting integer performance metrics (packet counts, byte sizes, etc.)
- Collecting numeric status codes from command output
- Parsing sensor readings reported as integers (e.g., RSSI values, counters)
- Validating that measured values fall within expected ranges
- Gathering statistical data across multiple experiment cases

## Configuration Arguments

### Required Arguments
- **value** (string): Name to assign to the extracted value for storage and reference. This name can be used in other parts of the experiment configuration.
- **pattern** (string): Regular expression containing a named capture group `(?P<value>...)` that matches the integer to extract. For example: `count=(?P<value>\d+)`.
- **subtask** (string): Name of the subtask whose log output should be scanned. This must match the `name` of another subtask defined in the same experiment.

### Optional Arguments
None.

## Result
Returns SUCCESS if the pattern is found and the integer value is successfully extracted. Returns FAILURE if the pattern is not found in the log or the captured value cannot be parsed as an integer.

## Example Configuration

```toml
[[actions]]
type = "shell"
name = "check_network"

[actions.args]
cmd = "echo 'RX packets: 42 dropped: 0'"
timeout = 5

[[checks]]
type = "logger-int-matcher"
name = "extract_rx_packets"

[checks.args]
value = "rx_packets"
pattern = "RX packets: (?P<value>\\d+)"
subtask = "check_network"
```

## Notes
- The regular expression must include exactly one named group: `(?P<value>...)`.
- In TOML configuration, backslashes in regex patterns must be escaped (`\\d` instead of `\d`).
- The `subtask` reference must point to a subtask that has already executed in the same experiment phase.
- Use `logger-float-matcher` for extracting floating-point numbers.
- The extracted value is stored and can be used for conditional logic or reporting in subsequent phases.

## See Also
- [logger-float-matcher](./logger-float-matcher.md) — Extract floating-point values from logs
- [shell](./shell.md) — Generate output to be scanned by logger matchers
