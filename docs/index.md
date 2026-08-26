<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# emtorch Documentation

Welcome to the emtorch documentation. **emtorch** (Experiments Orchestrator for Embedded Systems) is a powerful CLI tool for orchestrating automated experiments on embedded devices.

## What is emtorch?

emtorch is a Python-based orchestration framework designed for researchers and engineers working with embedded systems. It allows you to:

- **Define complex experiment workflows** using simple TOML configuration files
- **Execute experiments consistently** across multiple test cases
- **Monitor and collect data** from embedded devices in real-time
- **Automate embedded system testing** with SSH, SFTP, and CoAP support
- **Generate structured JSON results** for easy analysis and post-processing

Previously known as **emfuzzer** (renamed in v2.0.0), emtorch is developed at the Warsaw University of Technology and licensed under the MIT License.

## Key Features

- **Plugin-based subtasks**: Extensible architecture with 13 built-in subtasks for common operations
- **Async-native execution**: All operations use asyncio for efficient parallel processing
- **Flexible phases**: Organize experiments into setups, monitoring, actions, and checks
- **Template variables**: Use dynamic values like case IDs and data paths in configurations
- **Remote connectivity**: SSH and SFTP support for testing on remote machines
- **Protocol support**: Built-in CoAP monitoring and messaging
- **Data collection**: Extract values from logs using regex patterns

## Quick Start

### Installation

Requires Python 3.14+

```bash
pip install emtorch
```

Or run as a module:

```bash
python3 -m emtorch --help
```

### Your First Experiment

Create a test data file:

```bash
echo "Hello from test case 1" > test_data_1.txt
```

Create a simple configuration file (`config.toml`):

```toml
[delays]
between_cases = 0.2

[[actions]]
type = "shell"
name = "read_data"

[actions.args]
cmd = "cat $EMTORCH_DATA_PATH"
```

Run your first experiment:

```bash
python3 -m emtorch run test_data_1.txt -c config.toml
```

This will execute your configuration against the test data and output results in JSON format.

## Documentation Guide

### For Users

- **[Getting Started](./getting-started.md)** — Installation, first experiment, and next steps
- **[Core Concepts](./core-concepts.md)** — Understand experiments, cases, subtasks, and phases
- **[CLI Reference](./cli-reference.md)** — All commands and command-line options
- **[Configuration Guide](./configuration-guide.md)** — TOML syntax, structure, and best practices
- **[Subtasks Reference](./subtasks/index.md)** — Complete documentation for all 13 subtasks
- **[Examples & Tutorials](./examples/index.md)** — Practical examples and step-by-step guides
- **[Troubleshooting](./troubleshooting.md)** — Common issues and solutions

### For Developers

- **[Developer Guide](./developer-guide.md)** — Creating custom subtasks and extending emtorch

## Available Subtasks

emtorch provides 13 built-in subtasks for common operations:

| Subtask | Purpose |
|---------|---------|
| **echo** | Print messages to logs |
| **exec** | Execute programs with arguments |
| **shell** | Execute shell commands |
| **remote** | Execute commands on remote hosts via SSH |
| **ping-alive** | Check network connectivity (flood ping) |
| **ping-stable** | Verify stable network response |
| **sftp-get** | Download files from remote hosts |
| **sftp-put** | Upload files to remote hosts |
| **file-write** | Write content to local files |
| **logger-int-matcher** | Extract integer values from logs |
| **logger-float-matcher** | Extract float values from logs |
| **coap-monitor** | Monitor CoAP protocol messages |
| **coap-send** | Send CoAP protocol messages |

See the [Subtasks Reference](./subtasks/index.md) for detailed documentation on each subtask.

## Experiment Lifecycle

Every experiment follows a structured execution flow:

```
┌─────────────────────────────────────────────────────────────────┐
│ For each test case:                                             │
│                                                                 │
│ 1. Execute Setups (sequential)                                  │
│    └─ Pre-case configuration (e.g., echo, ping-alive)           │
│                                                                 │
│ 2. Start Monitoring (concurrent)                                │
│    ├─ Monitor runs in background                                │
│    ├─ Delay before actions                                      │
│    ├─ Execute Actions (sequential)                              │
│    │  └─ Main experiment activities                             │
│    └─ Stop monitoring when actions complete                     │ 
│                                                                 │
│ 3. Execute Checks (sequential)                                  │
│    └─ Post-case verification (e.g., ping-stable, cleanup)       │
│                                                                 │
│ 4. Delay between cases (for next case)                          │
└─────────────────────────────────────────────────────────────────┘
```

## Requirements

- **Python**: 3.14 or later
- **Operating System**: Linux, macOS, or Windows (with WSL for some features)
- **Build Tools**: Poetry for development installation

## License

emtorch is licensed under the MIT License. See the LICENSE.txt file in the repository for full details.

## Getting Help

- Check the [Troubleshooting](./troubleshooting.md) section for common issues
- Review [Examples & Tutorials](./examples/index.md) for practical guidance
- See [Subtasks Reference](./subtasks/index.md) for specific subtask documentation
- Run `python3 -m emtorch subtask <NAME>` to see built-in subtask documentation

---

**Ready to get started?** Head to the [Getting Started](./getting-started.md) guide!
