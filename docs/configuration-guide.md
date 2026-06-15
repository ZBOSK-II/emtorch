<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# Configuration Guide

Learn how to write TOML configuration files for emtorch experiments.

## Overview

emtorch experiments are defined using TOML configuration files. A configuration specifies:

- **Delays** — How long to wait between operations
- **Setups** — Pre-case preparation subtasks
- **Monitoring** — Background monitoring subtasks
- **Actions** — Main experiment operations
- **Checks** — Post-case verification subtasks

## Basic Structure

A minimal configuration file requires at least one phase (setups, actions, or checks):

```toml
[[actions]]
type = "echo"
name = "hello"

[actions.args]
message = "Hello, World!"
```

A typical configuration includes multiple phases:

```toml
[delays]
between_cases = 0.2
before_actions = 1.0

[[setups]]
type = "echo"
name = "start"
[setups.args]
message = "Case $EMTORCH_CASE_ID starting"

[[actions]]
type = "shell"
name = "run_test"
[actions.args]
cmd = "echo Processing $EMTORCH_DATA_FILENAME"

[[checks]]
type = "echo"
name = "end"
[checks.args]
message = "Case complete"
```

## Delays Section

The optional `[delays]` section controls timing:

```toml
[delays]
between_cases = 0.2      # Wait 200ms between cases
before_actions = 1.0     # Wait 1 second before starting actions
```

### Between Cases

**Key:** `between_cases`
**Type:** Float (seconds)
**Default:** 0.2
**When:** Executed after checks complete, before next case starts
**Note:** Skipped before the first case

Use this to:
- Allow time for device cleanup
- Reset state between test cases
- Avoid race conditions

### Before Actions

**Key:** `before_actions`
**Type:** Float (seconds)
**Default:** 1.0
**When:** After monitoring starts, before actions begin
**Note:** Occurs inside the monitoring phase

Use this to:
- Give monitoring time to stabilize
- Wait for background processes to initialize
- Synchronize with slow devices

## Phase Sections

Each phase is an array of subtasks. Use the `[[section_name]]` syntax:

```toml
[[setups]]
type = "subtask_name"
name = "instance_name"

[setups.args]
# subtask-specific arguments
param1 = "value"
param2 = 42
```

### Phase Types

- **`[[setups]]`** — Pre-case setup (sequential execution)
- **`[[monitoring]]`** — Background monitoring (concurrent with actions)
- **`[[actions]]`** — Main experiment operations (sequential execution)
- **`[[checks]]`** — Post-case verification (sequential execution)

## Subtask Configuration

Each subtask in a phase requires:

### Required Fields

**`type`** — The subtask name (string)

Must match one of the registered subtask names. Get the list with:

```bash
python3 -m emtorch subtasks
```

**`name`** — Instance name (string)

A unique identifier for this subtask instance in your configuration. Used in results and logs.

```toml
[[actions]]
type = "shell"
name = "verify_data"  # This name appears in results JSON
```

### Optional: Arguments Block

Some subtasks require arguments. Use the `[section.args]` syntax:

```toml
[[actions]]
type = "shell"
name = "run_command"

[actions.args]
cmd = "echo test"
timeout = 5
signal = "SIGTERM"
```

**When arguments are required:**
- Subtasks like `shell`, `exec`, `remote` require command arguments
- Subtasks like `echo` require a message
- Subtasks like `ping-alive` require host configuration

**When arguments are optional:**
- Some subtasks have default values
- Default timeouts are usually 1.0 seconds
- Signal is optional (defaults to SIGTERM)

To see required and optional arguments for a subtask:

```bash
python3 -m emtorch subtask shell
python3 -m emtorch subtask ping-alive
python3 -m emtorch subtask echo
```

## Template Variables

Use dynamic values in your configuration with template variables:

| Variable | Value |
|----------|-------|
| `$EMTORCH_CASE_ID` | Numeric case ID (0, 1, 2, ...) |
| `$EMTORCH_DATA_PATH` | Full path to data file |
| `$EMTORCH_DATA_FILENAME` | Just the filename |

### Examples

**Reference case ID:**
```toml
[[actions]]
type = "echo"
name = "log_case"

[actions.args]
message = "Processing case $EMTORCH_CASE_ID"
```

**Use data file path:**
```toml
[[actions]]
type = "shell"
name = "read_file"

[actions.args]
cmd = "cat $EMTORCH_DATA_PATH"
```

**Output with filename:**
```toml
[[actions]]
type = "file-write"
name = "copy_filename"

[actions.args]
path = "/tmp/case_$EMTORCH_CASE_ID.txt"
contents = "Processing $EMTORCH_DATA_FILENAME"
```

Template variables are replaced at runtime before executing subtasks.

## Complete Example Configuration

Here's a realistic configuration demonstrating all features:

```toml
# Timing configuration
[delays]
between_cases = 0.5
before_actions = 1.0

# === SETUP PHASE ===
# Verify preconditions before starting the experiment

[[setups]]
type = "echo"
name = "announce_case"

[setups.args]
message = "=== Starting case $EMTORCH_CASE_ID ==="

[[setups]]
type = "ping-alive"
name = "verify_network"

[setups.args]
host = "192.168.1.1"
timeout = 10
interval = 1

# === MONITORING PHASE ===
# Run background monitoring while actions execute

[[monitoring]]
type = "shell"
name = "background_logger"

[monitoring.args]
cmd = "while true; do echo $(date '+%Y-%m-%d %H:%M:%S') >> /tmp/monitor.log; sleep 1; done"
timeout = 30
signal = "SIGTERM"

# === ACTIONS PHASE ===
# Main experiment activities

[[actions]]
type = "echo"
name = "log_test_start"

[actions.args]
message = "Test starting for $EMTORCH_DATA_FILENAME"

[[actions]]
type = "shell"
name = "process_data"

[actions.args]
cmd = "cat $EMTORCH_DATA_PATH | wc -l"
timeout = 10

[[actions]]
type = "shell"
name = "run_analysis"

[actions.args]
cmd = "md5sum $EMTORCH_DATA_PATH"

# === CHECKS PHASE ===
# Verification and cleanup

[[checks]]
type = "ping-stable"
name = "verify_connectivity"

[checks.args]
host = "192.168.1.1"
count = 3
interval = 1

[[checks]]
type = "echo"
name = "complete"

[checks.args]
message = "=== Case $EMTORCH_CASE_ID complete ==="
```

## TOML Syntax Reference

### String Values

Use quotes for string values:

```toml
[section.args]
message = "Hello, World!"
cmd = "echo test"
name = "my_file.txt"
```

### Numbers

Integer and float values don't need quotes:

```toml
[section.args]
timeout = 10        # integer
interval = 1.5      # float
count = 0
```

### Boolean Values

```toml
[section.args]
append = true
recursive = false
```

### Arrays

Use square brackets for arrays:

```toml
[section.args]
args = ["arg1", "arg2", "arg3"]
hosts = ["192.168.1.1", "192.168.1.2"]
```

### Comments

Lines starting with `#` are comments:

```toml
# This is a comment
[[actions]]
type = "echo"
# Another comment
name = "test"
```

## Best Practices

### 1. Naming Conventions

Use consistent, descriptive names:

```toml
[[setups]]
type = "echo"
name = "setup_start"  # Good: describes what it does

name = "s1"           # Bad: unclear purpose
```

### 2. Organize by Phase

Group all subtasks of the same phase together, in execution order:

```toml
# All setups together
[[setups]]
...

[[setups]]
...

# Then all monitoring
[[monitoring]]
...

# Then all actions
[[actions]]
...
```

### 3. Use Template Variables

Instead of hardcoding paths, use template variables:

```toml
# Good
cmd = "cat $EMTORCH_DATA_PATH"

# Problematic
cmd = "cat /path/to/data_file"  # Changes for each case!
```

### 4. Set Appropriate Timeouts

Adjust timeouts based on expected operation duration:

```toml
[[actions]]
type = "shell"
name = "quick_check"
[actions.args]
cmd = "ls"
timeout = 2  # Quick command

---

[[actions]]
type = "shell"
name = "slow_process"
[actions.args]
cmd = "find / -name '*.txt'"
timeout = 60  # Slow command needs more time
```

### 5. Use Signal for Long-Running Processes

When processes need termination, specify a signal:

```toml
[[monitoring]]
type = "shell"
name = "long_monitor"

[monitoring.args]
cmd = "sleep 1000"
timeout = 30
signal = "SIGKILL"  # Force termination if needed
```

### 6. Validate Configuration

Before running full experiments, test with one data file:

```bash
# Test configuration
python3 -m emtorch run test_single.bin -c config.toml

# If successful, run full suite
python3 -m emtorch run data/*.bin -c config.toml -o results_
```

## Common Configuration Patterns

### Simple Echo Test

```toml
[[actions]]
type = "echo"
name = "test"

[actions.args]
message = "Test message"
```

### Shell Command Execution

```toml
[[actions]]
type = "shell"
name = "run_cmd"

[actions.args]
cmd = "echo $EMTORCH_CASE_ID"
timeout = 5
```

### Process with Monitoring

```toml
[[monitoring]]
type = "shell"
name = "monitor"

[monitoring.args]
cmd = "while true; do date; sleep 1; done"
timeout = 10
signal = "SIGTERM"

[[actions]]
type = "shell"
name = "do_work"

[actions.args]
cmd = "sleep 5"
```

### File Operations

```toml
[[actions]]
type = "file-write"
name = "save_result"

[actions.args]
path = "/tmp/case_$EMTORCH_CASE_ID.txt"
contents = "Results for case $EMTORCH_CASE_ID"
append = false
```

### Remote SSH Execution

```toml
[[actions]]
type = "remote"
name = "run_remote"

[actions.args]
connection = {host = "example.com", username = "user", password = "pass"}
cmd = "whoami"
timeout = 5
```

## Troubleshooting

### "Invalid TOML syntax"

Check:
- All strings are quoted
- Sections use `[[name]]` for arrays
- Numbers and booleans are unquoted

### "Unknown subtask"

Verify the subtask name:

```bash
python3 -m emtorch subtasks
```

### "Missing required argument"

Check the subtask documentation:

```bash
python3 -m emtorch subtask shell
```

### "Connection failed"

For remote/SFTP subtasks, verify:
- Host is reachable
- Username and password are correct
- SSH access is permitted

---

Next: [Subtasks Reference](./subtasks/index.md) — Complete documentation for each subtask
