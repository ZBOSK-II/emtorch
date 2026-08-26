<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# Subtasks Reference

Complete documentation for all 13 emtorch subtasks. Each subtask performs a specific operation within your experiment workflow.

## Quick Reference

### Local Operations
- **[echo](./echo.md)** — Print messages to logs
- **[shell](./shell.md)** — Execute shell commands
- **[exec](./exec.md)** — Run programs with arguments
- **[file-write](./file-write.md)** — Write content to files

### Remote Operations
- **[remote](./remote.md)** — Execute commands via SSH
- **[sftp-get](./sftp-get.md)** — Download files from remote hosts
- **[sftp-put](./sftp-put.md)** — Upload files to remote hosts

### Network Checks
- **[ping-alive](./ping-alive.md)** — Check connectivity with flood ping
- **[ping-stable](./ping-stable.md)** — Verify stable network response

### Data Collection
- **[logger-int-matcher](./logger-int-matcher.md)** — Extract integers from logs
- **[logger-float-matcher](./logger-float-matcher.md)** — Extract floats from logs

### Protocol Support
- **[coap-monitor](./coap-monitor.md)** — Monitor CoAP messages
- **[coap-send](./coap-send.md)** — Send CoAP messages

## Using Subtasks

### Basic Usage

Add a subtask to any phase in your configuration:

```toml
[[actions]]
type = "echo"
name = "my_echo"

[actions.args]
message = "Hello, World!"
```

### Understanding Results

Every subtask returns a result:

```json
{
  "status": "SUCCESS",
  "log": "Output from the subtask...\n"
}
```

**Status values:**
- **SUCCESS** — Operation completed successfully
- **FAILURE** — Operation failed (non-zero exit code)
- **ERROR** — Unexpected error occurred
- **TIMEOUT** — Operation exceeded timeout

### Timeouts

Most subtasks that perform external operations support timeout configuration:

```toml
[[actions]]
type = "shell"
name = "example"

[actions.args]
cmd = "sleep 10"
timeout = 5  # Timeout after 5 seconds
signal = "SIGTERM"  # Send SIGTERM when timeout occurs
```

### Signals

When a timeout occurs, you can specify a signal to send:

- `SIGTERM` — Graceful termination (default)
- `SIGKILL` — Force termination
- Other signal names (SIGHUP, SIGINT, etc.)

### Template Variables

All string values support template variables:

```toml
[[actions]]
type = "shell"
name = "process"

[actions.args]
cmd = "cat $EMTORCH_DATA_PATH"
```

Available variables:
- `$EMTORCH_CASE_ID` — Current case number
- `$EMTORCH_DATA_PATH` — Full path to data file
- `$EMTORCH_DATA_FILENAME` — Data filename only

## Subtask Categories

### Local Operations

Local subtasks execute on the same machine where emtorch runs.

**Use for:**
- Logging and monitoring
- Data processing
- File operations
- System commands

### Remote Operations

Remote subtasks connect to external hosts via SSH/SFTP.

**Prerequisites:**
- SSH connectivity to target host
- Valid credentials (password or key-based auth)
- Network reachability

**Use for:**
- Testing embedded devices
- Remote data collection
- Cross-device testing

### Network Checks

Network subtasks verify connectivity and reachability.

**Use for:**
- Precondition verification (setups)
- Post-experiment validation (checks)
- Network topology testing

### Data Collection

Logger matcher subtasks extract values from log output.

**Use for:**
- Collecting metrics from other subtasks
- Statistical analysis
- Performance measurement

### Protocol Support

Protocol subtasks interact with specific communication protocols.

**Current support:**
- CoAP (Constrained Application Protocol) for IoT devices

---

## Getting Help

To see documentation for a specific subtask from the command line:

```bash
python3 -m emtorch subtask <NAME>
```

Examples:

```bash
python3 -m emtorch subtask echo
python3 -m emtorch subtask shell
python3 -m emtorch subtask remote
```

To list all available subtasks:

```bash
python3 -m emtorch subtasks
```

---

## Choosing the Right Subtask

### I need to run a shell command

Use **[shell](./shell.md)** for shell commands, or **[exec](./exec.md)** for programs.

### I need to transfer files

Use **[sftp-get](./sftp-get.md)** to download, or **[sftp-put](./sftp-put.md)** to upload.

### I need to test network connectivity

Use **[ping-alive](./ping-alive.md)** for quick checks, or **[ping-stable](./ping-stable.md)** for verification.

### I need to run commands on a remote device

Use **[remote](./remote.md)** for SSH command execution.

### I need to extract values from logs

Use **[logger-int-matcher](./logger-int-matcher.md)** for integers, or **[logger-float-matcher](./logger-float-matcher.md)** for floating-point numbers.

### I need to test IoT devices

Use **[coap-monitor](./coap-monitor.md)** to listen for CoAP messages, or **[coap-send](./coap-send.md)** to send messages.

---

## Common Patterns

### Chain Multiple Operations

Execute operations in sequence by placing them in order:

```toml
[[actions]]
type = "shell"
name = "prepare"
[actions.args]
cmd = "mkdir -p /tmp/test"

[[actions]]
type = "shell"
name = "process"
[actions.args]
cmd = "echo test > /tmp/test/data.txt"

[[actions]]
type = "shell"
name = "verify"
[actions.args]
cmd = "cat /tmp/test/data.txt"
```

### Use Background Monitoring

Run monitoring while executing actions:

```toml
[[monitoring]]
type = "shell"
name = "monitor"
[monitoring.args]
cmd = "while true; do echo $(date); sleep 1; done"
timeout = 30
signal = "SIGTERM"

[[actions]]
type = "shell"
name = "do_work"
[actions.args]
cmd = "sleep 10"
```

### Extract Values from Output

Use logger matchers to collect numeric values:

```toml
[[actions]]
type = "shell"
name = "measure"
[actions.args]
cmd = "echo 'Performance: 42.5 ops/sec'"

[[checks]]
type = "logger-float-matcher"
name = "extract_performance"
[checks.args]
value = "performance"
pattern = "Performance: (?P<value>\\d+\\.\\d+)"
subtask = "measure"
```

---

Next steps:
- [Getting Started](../getting-started.md) — Run your first experiment
- [Configuration Guide](../configuration-guide.md) — Learn TOML syntax
- [Examples & Tutorials](../examples/index.md) — Practical examples
