<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# Examples & Tutorials

Practical step-by-step guides for common emtorch use cases.

## Available Tutorials

### [Basic Experiment Tutorial](./basic-experiment.md)

**Level:** Beginner  
**Time:** 10-15 minutes

Learn the fundamentals:
- Create test data files
- Write a simple TOML configuration
- Run your first experiment
- Understand the results

**What you'll build:**
An experiment that reads data files, processes them, and verifies the setup.

**Topics covered:**
- Configuration structure
- Setups and checks phases
- Template variables
- Result interpretation

---

### [Remote Testing with SSH](./remote-testing.md)

**Level:** Intermediate  
**Time:** 20-30 minutes

Test devices over SSH:
- Configure SSH connections
- Execute commands on remote devices
- Transfer files with SFTP
- Handle timeouts and errors

**What you'll build:**
An experiment that connects to a remote device, runs diagnostic commands, and collects results.

**Prerequisites:**
- SSH access to a remote machine
- Network connectivity

**Topics covered:**
- SSH connection configuration
- remote, sftp-get, and sftp-put subtasks
- Timeout handling
- Remote error handling

---

### [CoAP Device Monitoring](./coap-monitoring.md)

**Level:** Advanced  
**Time:** 30-45 minutes

Monitor IoT devices using CoAP protocol:
- Set up CoAP monitoring in background
- Send CoAP messages from actions
- Capture and analyze responses
- Multiple simultaneous protocols

**What you'll build:**
An experiment that monitors CoAP traffic while sending test messages to an IoT device.

**Prerequisites:**
- Understanding of CoAP protocol basics
- CoAP-enabled test device or simulator

**Topics covered:**
- coap-monitor and coap-send subtasks
- Background monitoring
- Protocol message handling
- Device communication patterns

---

### [Data Collection with Log Matching](./log-collection.md)

**Level:** Intermediate  
**Time:** 15-25 minutes

Extract values from command output:
- Use logger matchers to parse logs
- Extract numeric metrics
- Build data collection pipelines
- Statistical analysis preparation

**What you'll build:**
An experiment that runs performance tests and automatically extracts key metrics.

**Prerequisites:**
- Understanding of regular expressions
- Familiarity with command output formats

**Topics covered:**
- logger-int-matcher and logger-float-matcher
- Regex patterns with named groups
- Value extraction workflows
- Result collection and analysis

---

## Choosing a Tutorial

### I'm new to emtorch

Start with [Basic Experiment Tutorial](./basic-experiment.md). It covers the fundamentals you need.

### I need to test remote devices

Follow [Remote Testing with SSH](./remote-testing.md). Learn SSH configuration and file transfer.

### I work with IoT devices

Check out [CoAP Device Monitoring](./coap-monitoring.md). Understand protocol integration.

### I need to collect metrics

Read [Data Collection with Log Matching](./log-collection.md). Learn value extraction and analysis.

---

## General Tips

### Test Before Full Run

Always test your configuration with a single data file before running the full test suite:

```bash
# Test configuration
python3 -m emtorch run test_data/single_case.bin -c config.toml

# If successful, run full suite
python3 -m emtorch run test_data/*.bin -c config.toml -o results_
```

### Use Appropriate Timeouts

Set timeouts based on expected operation duration:

```toml
[actions.args]
timeout = 2    # Quick operation
timeout = 30   # Long operation
timeout = 120  # Very slow operation
```

### Leverage Template Variables

Always use template variables instead of hardcoding paths:

```toml
# Good - works for all cases
cmd = "cat $EMTORCH_DATA_PATH"

# Bad - only works for specific files
cmd = "cat /path/to/data.bin"
```

### Organize Configuration Logically

Group related subtasks together:

```toml
# All setups
[[setups]]
...
[[setups]]
...

# All monitoring
[[monitoring]]
...

# All actions
[[actions]]
...

# All checks
[[checks]]
...
```

### Use Descriptive Names

Make subtask names self-documenting:

```toml
[[actions]]
type = "shell"
name = "verify_file_exists"  # Clear purpose

# vs

name = "run1"  # Unclear
```

---

## Common Patterns

### Chain Operations

Execute related commands in sequence:

```toml
[[actions]]
type = "shell"
name = "prepare"
[actions.args]
cmd = "mkdir -p /tmp/work"

[[actions]]
type = "shell"
name = "process"
[actions.args]
cmd = "cat $EMTORCH_DATA_PATH > /tmp/work/data.txt"

[[actions]]
type = "shell"
name = "verify"
[actions.args]
cmd = "wc -l /tmp/work/data.txt"
```

### Background Monitoring

Run continuous monitoring while actions execute:

```toml
[[monitoring]]
type = "shell"
name = "continuous_log"
[monitoring.args]
cmd = "while true; do echo $(date) >> /tmp/monitor.log; sleep 1; done"
timeout = 60
signal = "SIGTERM"

[[actions]]
type = "shell"
name = "main_test"
[actions.args]
cmd = "sleep 10; echo done"
```

### Extract Metrics

Collect performance metrics from command output:

```toml
[[actions]]
type = "shell"
name = "benchmark"
[actions.args]
cmd = "echo 'Throughput: 1234.5 ops/sec'; sleep 1"

[[checks]]
type = "logger-float-matcher"
name = "get_throughput"
[checks.args]
value = "throughput"
pattern = "Throughput: (?P<value>\\d+\\.\\d+)"
subtask = "benchmark"
```

### Verify Preconditions

Test prerequisites in setups phase:

```toml
[[setups]]
type = "ping-alive"
name = "check_network"
[setups.args]
host = "192.168.1.1"
timeout = 5
interval = 1

[[setups]]
type = "echo"
name = "announce"
[setups.args]
message = "Preconditions verified, starting case $EMTORCH_CASE_ID"
```

---

## Getting Help

- **Confused about a subtask?** See [Subtasks Reference](../subtasks/index.md)
- **Need configuration syntax help?** Check [Configuration Guide](../configuration-guide.md)
- **Having issues?** Visit [Troubleshooting](../troubleshooting.md)
- **Get builtin help:** `python3 -m emtorch subtask <NAME>`

---

**Ready to start?** Pick a tutorial from above and follow along!
