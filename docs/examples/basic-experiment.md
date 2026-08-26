<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# Tutorial: Basic Experiment

## Overview

This tutorial walks you through creating and running your first emtorch experiment from scratch. You will learn how to set up test data files, write a complete TOML configuration using `echo`, `shell`, and `ping-alive` subtasks, execute the experiment against multiple test cases, and interpret the structured JSON results.

By the end of this guide you will understand the core emtorch concepts — cases, phases, subtasks, and template variables — well enough to design your own experiments.

## Prerequisites

**Software:**
- Python 3.14 or later installed on your system
- emtorch installed (`pip install emtorch` or installed from source)
- A terminal or command-line environment
- Basic familiarity with the command line (creating directories, running commands)

**Knowledge:**
- No prior emtorch experience needed
- Basic understanding of JSON (helpful for reading results)

**Hardware:**
- A machine with network access (needed for the `ping-alive` subtask)
- At least one of the target hosts you ping should be reachable (e.g., `127.0.0.1` always works)

## Scenario

You are an embedded systems researcher evaluating the behaviour of a network-connected device under different input conditions. Your goal is to:

1. Prepare multiple test input files representing different operating conditions.
2. Verify the device is reachable on the network before each test.
3. Process each input file through a shell command that simulates a measurement.
4. Log the progress of each test case.
5. Verify stable network connectivity after each test.

The experiment will run against three cases, each using a different input data file.

## Step 1: Create the Project Directory and Test Data

Create a dedicated directory for the experiment and generate three test data files that represent different measurement inputs.

```bash
mkdir -p ~/emtorch-basic-tutorial
cd ~/emtorch-basic-tutorial
mkdir -p test_data
```

Now create the three data files. Each contains a simulated sensor reading or device parameter.

**File `test_data/measurement_1.txt`:**

```
Sensor A reading: temperature=22.5, humidity=60, pressure=1013
Device status: OK
Network RSSI: -45 dBm
```

**File `test_data/measurement_2.txt`:**

```
Sensor A reading: temperature=35.0, humidity=85, pressure=998
Device status: WARNING - high temperature
Network RSSI: -72 dBm
```

**File `test_data/measurement_3.txt`:**

```
Sensor A reading: temperature=18.2, humidity=45, pressure=1021
Device status: OK
Network RSSI: -38 dBm
```

Create these files with the following commands:

```bash
cat > test_data/measurement_1.txt << 'EOF'
Sensor A reading: temperature=22.5, humidity=60, pressure=1013
Device status: OK
Network RSSI: -45 dBm
EOF

cat > test_data/measurement_2.txt << 'EOF'
Sensor A reading: temperature=35.0, humidity=85, pressure=998
Device status: WARNING - high temperature
Network RSSI: -72 dBm
EOF

cat > test_data/measurement_3.txt << 'EOF'
Sensor A reading: temperature=18.2, humidity=45, pressure=1021
Device status: OK
Network RSSI: -38 dBm
EOF
```

### What Happens

You have created a project folder with a `test_data/` subdirectory containing three plain-text input files. Each file represents a distinct set of conditions our experiment will process. In emtorch, each data file corresponds to one **case** — a single execution of the experiment configuration against that input.

> **Note:** Data files do not need to be text files. They can be binary blobs, CSV files, or any format your experiment commands can read. The file extension does not matter.

## Step 2: Write the Experiment Configuration

Create a file named `experiment-config.toml` in your project directory. This TOML file will define the complete experiment.

```toml
# =============================================================================
# Experiment Configuration for Basic Sensor Data Processing
# =============================================================================
# This configuration demonstrates the four phases: setups, monitoring,
# actions, and checks. It processes each input data file through a
# simulation pipeline while verifying network connectivity.
# =============================================================================

# --- Timing Configuration ---
[delays]
between_cases = 0.5        # Pause 0.5 seconds between each case
before_actions = 1.0       # Wait 1 second before starting actions (gives
                           # monitoring time to initialize)

# =============================================================================
# SETUPS PHASE — Preparation before each case
# =============================================================================
# Subtasks in this phase run sequentially. They prepare the environment,
# verify preconditions, and log the start of each case.

[[setups]]
type = "echo"
name = "announce_case"

[setups.args]
message = "=== Starting case $EMTORCH_CASE_ID ($EMTORCH_DATA_FILENAME) ==="

[[setups]]
type = "ping-alive"
name = "check_device_online"

[setups.args]
host = "127.0.0.1"
timeout = 5
interval = 100

# =============================================================================
# MONITORING PHASE — Background observation
# =============================================================================
# Monitoring subtasks start before actions and run in the background.
# They stop automatically when the actions phase completes.

[[monitoring]]
type = "shell"
name = "background_logger"

[monitoring.args]
cmd = "while true; do echo \"[$(date '+%H:%M:%S')] Monitoring case $EMTORCH_CASE_ID...\"; sleep 1; done"
timeout = 15
signal = "SIGTERM"

# =============================================================================
# ACTIONS PHASE — Main experiment work
# =============================================================================
# These subtasks execute sequentially while monitoring runs in the background.

[[actions]]
type = "echo"
name = "begin_processing"

[actions.args]
message = "Processing $EMTORCH_DATA_FILENAME for case $EMTORCH_CASE_ID"

[[actions]]
type = "shell"
name = "read_and_analyze"

[actions.args]
cmd = "cat $EMTORCH_DATA_PATH | head -3"
timeout = 5

[[actions]]
type = "shell"
name = "extract_temperature"

[actions.args]
cmd = "grep -oP 'temperature=\\K[\\d.]+' $EMTORCH_DATA_PATH"
timeout = 3

[[actions]]
type = "shell"
name = "check_device_status"

[actions.args]
cmd = "grep 'Device status' $EMTORCH_DATA_PATH"
timeout = 3

# =============================================================================
# CHECKS PHASE — Verification and cleanup
# =============================================================================
# Runs after actions complete and monitoring has stopped.

[[checks]]
type = "echo"
name = "completion_message"

[checks.args]
message = "=== Case $EMTORCH_CASE_ID completed successfully ==="

[[checks]]
type = "ping-stable"
name = "verify_stable_connection"

[checks.args]
host = "127.0.0.1"
count = 3
interval = 200

[[checks]]
type = "echo"
name = "case_summary"

[checks.args]
message = "Finished case $EMTORCH_CASE_ID — data file: $EMTORCH_DATA_FILENAME"
```

### What Happens

The configuration defines four phases:

1. **Setups:** An `echo` subtask logs the start of each case, then `ping-alive` checks that `127.0.0.1` (localhost) is reachable. In a real scenario you would replace this with your device's IP address.

2. **Monitoring:** A `shell` subtask runs an infinite loop that prints a timestamped message every second. This demonstrates background monitoring — it logs activity throughout the actions phase. The `timeout = 15` limits how long it runs, and `signal = "SIGTERM"` tells emtorch how to stop it gracefully when actions finish.

3. **Actions:** Four subtasks process the data file:
   - `echo` announces what is about to happen.
   - `read_and_analyze` displays the first 3 lines of the data file.
   - `extract_temperature` uses `grep` to pull the temperature value from the file.
   - `check_device_status` extracts the device status line.

4. **Checks:** After actions complete, an `echo` confirms completion, `ping-stable` verifies the connection is still stable (3 pings, all must succeed), and a final `echo` provides a summary.

> **Key Concept — Template Variables:**
> Notice `$EMTORCH_CASE_ID`, `$EMTORCH_DATA_PATH`, and `$EMTORCH_DATA_FILENAME` used throughout. These are replaced at runtime with the actual case number and file paths. When case 1 runs with `measurement_2.txt`, `$EMTORCH_CASE_ID` becomes `1` and `$EMTORCH_DATA_FILENAME` becomes `measurement_2.txt`.

> **Key Concept — Phase Order:**
> The phases always execute in this order: Setups → Monitoring (starts) → Actions (runs while monitoring is active) → Monitoring (stops) → Checks.

## Step 3: Run the Experiment

Now execute the experiment against all three data files.

```bash
python3 -m emtorch run test_data/measurement_1.txt test_data/measurement_2.txt test_data/measurement_3.txt -c experiment-config.toml -o results_
```

You can also use a shell glob to pass all files at once:

```bash
python3 -m emtorch run test_data/measurement_*.txt -c experiment-config.toml -o results_
```

### Understanding the Command

- `python3 -m emtorch run` — Invoke the emtorch `run` command.
- `test_data/measurement_*.txt` — Input data files; each becomes one case.
- `-c experiment-config.toml` — Path to the configuration file.
- `-o results_` — Output filename prefix. Results are written as `results_0.json`, `results_1.json`, `results_2.json`.

### What Happens

emtorch processes the command as follows:

1. Reads the configuration from `experiment-config.toml`.
2. Creates 3 cases — one per matching data file.
3. For each case (in order):
   - Executes the **setups** phase (announce, ping check).
   - Starts **monitoring** (background logger).
   - Waits `before_actions` seconds.
   - Executes **actions** (report, analyse, extract, check status).
   - Stops **monitoring**.
   - Executes **checks** (completion message, stable ping, summary).
   - Waits `between_cases` seconds (except before the first case).
   - Writes the case result to a JSON file.

## Step 4: Examine the Results

List the output files and inspect one of them.

```bash
ls -la results_*.json
cat results_0.json
```

You will see three JSON files. Here is what `results_0.json` (the first case) looks like:

```json
{
  "case_id": "0",
  "data_path": "/home/user/emtorch-basic-tutorial/test_data/measurement_1.txt",
  "data_filename": "measurement_1.txt",
  "results": {
    "setups": {
      "announce_case": {
        "status": "SUCCESS",
        "log": "=== Starting case 0 (measurement_1.txt) ===\n"
      },
      "check_device_online": {
        "status": "SUCCESS",
        "log": ""
      }
    },
    "monitoring": {
      "background_logger": {
        "status": "SUCCESS",
        "log": "[10:30:01] Monitoring case 0...\n[10:30:02] Monitoring case 0...\n"
      }
    },
    "actions": {
      "begin_processing": {
        "status": "SUCCESS",
        "log": "Processing measurement_1.txt for case 0\n"
      },
      "read_and_analyze": {
        "status": "SUCCESS",
        "log": "Sensor A reading: temperature=22.5, humidity=60, pressure=1013\nDevice status: OK\nNetwork RSSI: -45 dBm\n"
      },
      "extract_temperature": {
        "status": "SUCCESS",
        "log": "22.5\n"
      },
      "check_device_status": {
        "status": "SUCCESS",
        "log": "Device status: OK\n"
      }
    },
    "checks": {
      "completion_message": {
        "status": "SUCCESS",
        "log": "=== Case 0 completed successfully ===\n"
      },
      "verify_stable_connection": {
        "status": "SUCCESS",
        "log": ""
      },
      "case_summary": {
        "status": "SUCCESS",
        "log": "Finished case 0 — data file: measurement_1.txt\n"
      }
    }
  }
}
```

### Understanding the Result Structure

Each result JSON file contains:

| Field | Description |
|-------|-------------|
| `case_id` | The zero-based case number (0, 1, 2) |
| `data_path` | Absolute path to the input data file for this case |
| `data_filename` | Just the filename portion of the data path |
| `results` | Object containing four phase sections: `setups`, `monitoring`, `actions`, `checks` |

Inside each phase section, every subtask appears by its configured `name`. Each subtask result contains:

| Field | Description |
|-------|-------------|
| `status` | One of `SUCCESS`, `FAILURE`, `ERROR`, or `TIMEOUT` |
| `log` | The captured output (stdout/stderr) from the subtask |

> **Note:** In this experiment, all subtasks should report `SUCCESS`. If any report `FAILURE` or `TIMEOUT`, review the Troubleshooting section below.

Compare `results_0.json` with `results_1.json` and `results_2.json`. You will see different temperature values and device status lines corresponding to each input file.

## Step 5: Run with Different Options

### Repeat Cases Multiple Times

The `-r` (repeat) flag runs each case multiple times. This is useful for statistical measurements.

```bash
python3 -m emtorch run test_data/measurement_*.txt -c experiment-config.toml -o results_ -r 3
```

This runs each of the 3 data files 3 times, producing 9 result files (results_0.json through results_8.json). Cases 0–2 are the first run, 3–5 the second, 6–8 the third.

### Run a Single Case for Testing

When developing a configuration, test with a single file first:

```bash
python3 -m emtorch run test_data/measurement_1.txt -c experiment-config.toml
```

Without the `-o` flag, output goes to `stdout` so you can verify behaviour immediately.

## Complete Configuration

For reference, here is the complete `experiment-config.toml` file used in this tutorial:

```toml
[delays]
between_cases = 0.5
before_actions = 1.0

[[setups]]
type = "echo"
name = "announce_case"
[setups.args]
message = "=== Starting case $EMTORCH_CASE_ID ($EMTORCH_DATA_FILENAME) ==="

[[setups]]
type = "ping-alive"
name = "check_device_online"
[setups.args]
host = "127.0.0.1"
timeout = 5
interval = 100

[[monitoring]]
type = "shell"
name = "background_logger"
[monitoring.args]
cmd = "while true; do echo \"[$(date '+%H:%M:%S')] Monitoring case $EMTORCH_CASE_ID...\"; sleep 1; done"
timeout = 15
signal = "SIGTERM"

[[actions]]
type = "echo"
name = "begin_processing"
[actions.args]
message = "Processing $EMTORCH_DATA_FILENAME for case $EMTORCH_CASE_ID"

[[actions]]
type = "shell"
name = "read_and_analyze"
[actions.args]
cmd = "cat $EMTORCH_DATA_PATH | head -3"
timeout = 5

[[actions]]
type = "shell"
name = "extract_temperature"
[actions.args]
cmd = "grep -oP 'temperature=\\K[\\d.]+' $EMTORCH_DATA_PATH"
timeout = 3

[[actions]]
type = "shell"
name = "check_device_status"
[actions.args]
cmd = "grep 'Device status' $EMTORCH_DATA_PATH"
timeout = 3

[[checks]]
type = "echo"
name = "completion_message"
[checks.args]
message = "=== Case $EMTORCH_CASE_ID completed successfully ==="

[[checks]]
type = "ping-stable"
name = "verify_stable_connection"
[checks.args]
host = "127.0.0.1"
count = 3
interval = 200

[[checks]]
type = "echo"
name = "case_summary"
[checks.args]
message = "Finished case $EMTORCH_CASE_ID — data file: $EMTORCH_DATA_FILENAME"
```

## Running the Tutorial

```bash
# 1. Create the project and data files
mkdir -p ~/emtorch-basic-tutorial/test_data
cd ~/emtorch-basic-tutorial

cat > test_data/measurement_1.txt << 'EOF'
Sensor A reading: temperature=22.5, humidity=60, pressure=1013
Device status: OK
Network RSSI: -45 dBm
EOF

cat > test_data/measurement_2.txt << 'EOF'
Sensor A reading: temperature=35.0, humidity=85, pressure=998
Device status: WARNING - high temperature
Network RSSI: -72 dBm
EOF

cat > test_data/measurement_3.txt << 'EOF'
Sensor A reading: temperature=18.2, humidity=45, pressure=1021
Device status: OK
Network RSSI: -38 dBm
EOF

# 2. Create the configuration file (use the Complete Configuration above
#    and save as experiment-config.toml)

# 3. Run the experiment
python3 -m emtorch run test_data/measurement_*.txt -c experiment-config.toml -o results_

# 4. View results
cat results_0.json
cat results_1.json
cat results_2.json
```

## Expected Output

The emtorch command will produce console output showing progress:

```
[INFO] Loaded configuration from experiment-config.toml
[INFO] Created 3 cases
[INFO] Starting case 0 (measurement_1.txt)
[INFO] Setups phase: SUCCESS
[INFO] Actions phase: SUCCESS
[INFO] Checks phase: SUCCESS
[INFO] Case 0 complete: SUCCESS
[INFO] Starting case 1 (measurement_2.txt)
[INFO] Setups phase: SUCCESS
[INFO] Actions phase: SUCCESS
[INFO] Checks phase: SUCCESS
[INFO] Case 1 complete: SUCCESS
[INFO] Starting case 2 (measurement_3.txt)
[INFO] Setups phase: SUCCESS
[INFO] Actions phase: SUCCESS
[INFO] Checks phase: SUCCESS
[INFO] Case 2 complete: SUCCESS
[INFO] All cases complete. 3/3 succeeded.
[INFO] Results written to results_*.json
```

The three JSON result files will reside in the current directory. Each contains the structured output shown in Step 4.

## Troubleshooting

### "No such file or directory" for data files

Make sure you are in the correct directory and the data files exist:

```bash
pwd
ls test_data/
```

If needed, use absolute paths:

```bash
python3 -m emtorch run ~/emtorch-basic-tutorial/test_data/*.txt -c ~/emtorch-basic-tutorial/experiment-config.toml
```

### Configuration parse error

Verify the TOML file is well-formed. Common mistakes include:

- Missing quotes around string values
- Using `#` inside a string (TOML treats `#` as a comment)
- Forgetting the `[setups.args]` section header
- Using tabs instead of spaces in significant places

Use a TOML validator or check with:

```bash
python3 -c "import tomllib; tomllib.load(open('experiment-config.toml', 'rb'))"
```

### ping-alive or ping-stable returns FAILURE

If the ping subtasks fail:

1. Verify you can ping the target manually: `ping -c 1 127.0.0.1`
2. Check that `127.0.0.1` is correct for your use case — it is the loopback address and should always work on any machine.
3. For a real device, replace with the actual IP address.
4. You might need `CAP_NET_RAW` or root privileges for flood ping. On some systems, use a longer `interval` value (milliseconds).

### Subtask status is TIMEOUT

Increase the `timeout` value for that subtask in the configuration. The default timeout for `shell` is 1 second, so commands that take longer will time out:

```toml
[actions.args]
cmd = "sleep 3 && echo done"
timeout = 5   # Must be > 3 seconds
```

### Monitoring subtask output is empty

If the monitoring shell loop fails to start, check that the `cmd` does not contain syntax errors. Test the command directly in your shell first.

### Results show FAILURE for a subtask

Check the `log` field in the JSON output for error details. For example, if `grep` finds no match, it returns exit code 1 (FAILURE). Adjust your command or the data file content.

### Output files overwritten each run

The `-o` prefix creates files named `{prefix}{case_id}.json`. If you run twice with the same prefix, files from the first run are overwritten. Use unique prefixes for each run:

```bash
python3 -m emtorch run test_data/*.txt -c config.toml -o run1_
python3 -m emtorch run test_data/*.txt -c config.toml -o run2_
```

## Next Steps

Now that you have completed your first emtorch experiment, you are ready to explore more advanced features:

| Topic | Resource |
|-------|----------|
| **Detailed concepts** | [Core Concepts](../core-concepts.md) |
| **Configuration reference** | [Configuration Guide](../configuration-guide.md) |
| **All subtask documentation** | [Subtasks Reference](../subtasks/index.md) |
| **Remote device testing** | [Remote Testing with SSH](./remote-testing.md) |
| **IoT/CoAP monitoring** | [CoAP Device Monitoring](./coap-monitoring.md) |
| **Data extraction** | [Data Collection with Log Matching](./log-collection.md) |

## Key Takeaways

- **Experiments are defined in TOML configuration files** organized into four phases: setups, monitoring, actions, and checks.
- **Each input data file becomes a case.** Cases are numbered from 0 and processed sequentially.
- **Template variables** (`$EMTORCH_CASE_ID`, `$EMTORCH_DATA_PATH`, `$EMTORCH_DATA_FILENAME`) let you write configurations that adapt dynamically to each case.
- **Results are written as structured JSON**, one file per case, with status and log output for every subtask.
- **Phase order is fixed:** setups → monitoring starts → actions → monitoring stops → checks.
- **Monitoring runs in the background** while actions execute, allowing concurrent observation.
- **Start simple** — test with a single data file before scaling up to many cases.
- **Always check the JSON results** to understand what each subtask produced.
