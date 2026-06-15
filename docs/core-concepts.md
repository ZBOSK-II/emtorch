<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# Core Concepts

Understand the fundamental building blocks of emtorch: experiments, cases, subtasks, phases, and templates.

## Experiments

An **experiment** is a complete test scenario defined in a TOML configuration file. It specifies:

- **What operations to perform** (subtasks)
- **How to organize those operations** (phases: setups, monitoring, actions, checks)
- **How long to wait** between operations (delays)
- **What configuration parameters** each operation needs

An experiment is designed to be executed repeatedly against multiple test cases with different input data.

### Example Experiment Structure

```toml
[delays]
between_cases = 0.2
before_actions = 1.0

[[setups]]
type = "ping-alive"
name = "check_network"
[setups.args]
host = "192.168.1.1"
timeout = 5
interval = 1

[[actions]]
type = "shell"
name = "test_command"
[actions.args]
cmd = "echo $EMTORCH_CASE_ID > /tmp/test.txt"

[[checks]]
type = "echo"
name = "finish"
[checks.args]
message = "Case complete"
```

## Cases

A **case** is a single execution of an experiment against one test data file. When you run:

```bash
python3 -m emtorch run data1.bin data2.bin data3.bin -c config.toml
```

You create **3 cases**: one for each data file.

### Case Lifecycle

Each case goes through:

1. **Initialization** — The data file path is recorded
2. **Setups** — Pre-case preparation
3. **Monitoring** — Background monitoring (concurrent with actions)
4. **Actions** — Main experiment logic
5. **Checks** — Post-case verification
6. **Delay** — Wait before starting the next case

### Case Identifiers

Cases are numbered starting from 0:
- First data file = Case 0
- Second data file = Case 1
- etc.

You can reference the case ID in your configuration using the `$EMTORCH_CASE_ID` template variable.

### Case Data

Each case has:

- **case_id**: Numeric identifier (0, 1, 2, ...)
- **data_path**: Absolute path to the input data file
- **data_filename**: Just the filename without the path

All three values are available in your configuration through template variables.

## Phases

An experiment is organized into **four sequential phases**. Each phase contains subtasks that are executed in a specific order and concurrency mode.

### 1. Setups

**When**: First, before anything else in the case
**Execution**: Sequential (one after another)
**Purpose**: Prepare the environment, check preconditions, initialize

Common setup subtasks:
- `echo` — Log a message
- `ping-alive` — Verify network is reachable
- `remote` — Connect to a remote device

```toml
[[setups]]
type = "echo"
name = "log_case_start"
[setups.args]
message = "Starting case $EMTORCH_CASE_ID"

[[setups]]
type = "ping-alive"
name = "check_network"
[setups.args]
host = "192.168.1.100"
timeout = 5
interval = 1
```

### 2. Monitoring

**When**: After setups, concurrent with actions and checks
**Execution**: Concurrent (runs in background)
**Purpose**: Collect data, observe behavior, record logs

Monitoring subtasks run in the background while actions execute. They:
- Start before actions begin
- Run in parallel with actions
- Stop after actions complete
- Can extract and return collected values

Common monitoring subtasks:
- `shell` — Run a background process
- `coap-monitor` — Listen for CoAP messages

```toml
[[monitoring]]
type = "shell"
name = "background_monitor"
[monitoring.args]
cmd = "while true; do echo $(date); sleep 1; done"
timeout = 30
signal = "SIGTERM"
```

### 3. Actions

**When**: During monitoring phase, after a delay
**Execution**: Sequential (one after another)
**Purpose**: Perform the main experiment operations

Actions are the core of your experiment. They execute while monitoring is active (in background).

Common action subtasks:
- `shell` — Execute a command
- `exec` — Run a program
- `remote` — Execute on remote host
- `sftp-put` / `sftp-get` — Transfer files
- `coap-send` — Send CoAP messages

```toml
[[actions]]
type = "shell"
name = "run_test"
[actions.args]
cmd = "cat $EMTORCH_DATA_PATH"
timeout = 10

[[actions]]
type = "shell"
name = "process_data"
[actions.args]
cmd = "wc -l $EMTORCH_DATA_PATH"
```

### 4. Checks

**When**: After actions and monitoring stop
**Execution**: Sequential (one after another)
**Purpose**: Verify results, cleanup, post-analysis

Checks run after actions are complete and all monitoring has stopped.

Common check subtasks:
- `ping-stable` — Verify stable network response
- `echo` — Log completion
- `file-write` — Record results
- `logger-int-matcher` — Extract values from logs

```toml
[[checks]]
type = "ping-stable"
name = "verify_network"
[checks.args]
host = "192.168.1.100"
count = 3
interval = 1

[[checks]]
type = "echo"
name = "case_complete"
[checks.args]
message = "Case $EMTORCH_CASE_ID verification complete"
```

## Subtasks

A **subtask** is a reusable building block that performs a specific operation. emtorch provides 13 built-in subtasks organized into categories:

### Local Operations

- **echo** — Print messages to logs
- **shell** — Execute shell commands
- **exec** — Run programs with arguments
- **file-write** — Write content to files

### Remote Operations

- **remote** — SSH command execution
- **sftp-get** — Download files via SFTP
- **sftp-put** — Upload files via SFTP

### Network Checks

- **ping-alive** — Check connectivity with flood ping
- **ping-stable** — Verify stable network response

### Data Collection

- **logger-int-matcher** — Extract integers from logs
- **logger-float-matcher** — Extract floats from logs

### Protocol Support

- **coap-monitor** — Monitor CoAP messages
- **coap-send** — Send CoAP messages

See the [Subtasks Reference](./subtasks/index.md) for detailed documentation on each subtask.

### Subtask Results

Every subtask returns a **result** indicating whether it succeeded:

```json
{
  "status": "SUCCESS",
  "log": "Output from the subtask...\n"
}
```

**Possible status values:**
- **SUCCESS** — Operation completed successfully
- **FAILURE** — Operation failed (e.g., command returned non-zero exit code)
- **ERROR** — Unexpected error occurred
- **TIMEOUT** — Operation exceeded the timeout limit

## Templates

Template variables allow you to insert dynamic values into your configuration. They use the `$VARIABLE_NAME` syntax.

### Available Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `$EMTORCH_CASE_ID` | Numeric case identifier | `Case $EMTORCH_CASE_ID started` |
| `$EMTORCH_DATA_PATH` | Full absolute path to data file | `cat $EMTORCH_DATA_PATH` |
| `$EMTORCH_DATA_FILENAME` | Filename without directory path | `Processing $EMTORCH_DATA_FILENAME` |

### Template Usage Examples

**Using case ID in a message:**
```toml
[[setups]]
type = "echo"
name = "log_case"
[setups.args]
message = "Running case $EMTORCH_CASE_ID"
```

**Using data path in a command:**
```toml
[[actions]]
type = "shell"
name = "process"
[actions.args]
cmd = "wc -l $EMTORCH_DATA_PATH"
```

**Using filename for output:**
```toml
[[actions]]
type = "file-write"
name = "record"
[actions.args]
path = "/tmp/case_$EMTORCH_CASE_ID.txt"
contents = "Processing $EMTORCH_DATA_FILENAME"
```

### How Templates Work

At runtime, emtorch replaces:
- `$EMTORCH_CASE_ID` with the numeric case ID (0, 1, 2, ...)
- `$EMTORCH_DATA_PATH` with the full path to the current data file
- `$EMTORCH_DATA_FILENAME` with just the filename

This replacement happens in **all string values** in your configuration.

## Delays

Delays control timing between operations.

### Types of Delays

**between_cases** — Wait between cases (in seconds)
- Allows time for cleanup between test cases
- Skipped before the first case
- Default: 0.2 seconds

**before_actions** — Wait before starting actions (in seconds)
- Allows monitoring to start before actions begin
- Happens inside the monitoring phase
- Default: 1.0 seconds

### Configuration

```toml
[delays]
between_cases = 0.5    # 500ms delay between each case
before_actions = 1.0   # 1 second before actions start
```

## Results

When an experiment completes, emtorch generates a JSON result file for each case containing:

### Result Structure

```json
{
  "case_id": "0",
  "data_path": "/absolute/path/to/data_file.bin",
  "data_filename": "data_file.bin",
  "results": {
    "setups": {
      "subtask_name": {
        "status": "SUCCESS",
        "log": "Output from subtask...\n"
      }
    },
    "monitoring": {
      "subtask_name": {
        "status": "SUCCESS",
        "log": "...",
        "values": {
          "collected_value": 42.5
        }
      }
    },
    "actions": {
      "subtask_name": {
        "status": "SUCCESS",
        "log": "Output...\n"
      }
    },
    "checks": {
      "subtask_name": {
        "status": "SUCCESS",
        "log": "...\n"
      }
    }
  }
}
```

### Understanding Results

- **case_id** — Which case this result is from (0, 1, 2, ...)
- **data_path** — Full path to the input data file
- **data_filename** — Just the filename
- **results** — All subtask results organized by phase
  - Each subtask has:
    - `status` — SUCCESS, FAILURE, ERROR, or TIMEOUT
    - `log` — Output captured from the subtask
    - `values` — Optional collected values (from logger-matchers)

## Execution Flow Summary

Here's how emtorch executes a complete experiment:

```
Load Configuration (TOML)
        ↓
Create Cases from data files
        ↓
For each case:
  ├─ Execute Setups (sequential)
  ├─ Start Monitoring (concurrent)
  ├─ Delay before_actions
  ├─ Execute Actions (sequential)
  ├─ Stop Monitoring
  ├─ Execute Checks (sequential)
  ├─ Delay between_cases (for next case)
  └─ Write Results to JSON
        ↓
All cases complete
```

---

Now that you understand the core concepts, explore:
- [Configuration Guide](./configuration-guide.md) — Learn TOML syntax and structure
- [Subtasks Reference](./subtasks/index.md) — Detailed documentation for each subtask
- [Examples & Tutorials](./examples/index.md) — Practical examples for different scenarios
