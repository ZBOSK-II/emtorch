<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# Tutorial: Remote Testing with SSH

## Overview

This tutorial teaches you how to use emtorch to test and interact with remote devices over SSH. You will learn how to configure SSH connections, execute commands on remote hosts using the `remote` subtask, upload experiment data with `sftp-put`, download results with `sftp-get`, handle timeouts gracefully, and manage connection errors. By the end of this guide you will be able to build experiments that span local and remote machines — a common requirement in embedded systems and IoT testing.

## Prerequisites

**Software:**
- Python 3.14 or later with emtorch installed
- SSH client installed (`ssh` command available in your terminal)
- Network connectivity to a remote host (real or simulated)

**Knowledge:**
- Familiarity with basic SSH concepts (host, username, password)
- Comfortable with command-line file operations
- Understanding of emtorch core concepts (cases, phases, subtasks) — complete the [Basic Experiment Tutorial](./basic-experiment.md) first if needed

**Hardware/Setup:**
- A remote machine with SSH server running (e.g., a Raspberry Pi, a cloud VM, or another machine on your LAN)
- OR a local SSH server for testing (`sudo systemctl start ssh` on Linux or use Docker)
- SSH login credentials (username and password) for that machine

> **Note:** This tutorial uses example addresses `192.168.1.100` for the remote host. Replace these with your actual remote host IP or hostname throughout the tutorial.

## Scenario

You are developing firmware for an embedded Linux device deployed in the field. You need a repeatable testing workflow that:

1. Uploads a test configuration file to the device via SFTP.
2. Executes a diagnostic script on the device over SSH.
3. Collects the resulting log file from the device via SFTP.
4. Verifies the device is still responsive after the test.

The experiment will run against multiple data files, each representing different test configurations, allowing you to test various scenarios in a single automated session.

## Step 1: Prepare Local Test Data

Create a project directory and prepare the files you will upload to the remote device.

```bash
mkdir -p ~/emtorch-remote-tutorial
cd ~/emtorch-remote-tutorial
mkdir -p config_data
```

Create three configuration files that represent different test parameters for the remote device.

**File `config_data/low_power.conf`:**

```
# Low power mode configuration
MODE=power_save
SAMPLE_INTERVAL=60
TX_POWER=10
LOG_LEVEL=INFO
```

**File `config_data/balanced.conf`:**

```
# Balanced mode configuration
MODE=balanced
SAMPLE_INTERVAL=30
TX_POWER=50
LOG_LEVEL=INFO
```

**File `config_data/high_perf.conf`:**

```
# High performance mode configuration
MODE=high_performance
SAMPLE_INTERVAL=5
TX_POWER=100
LOG_LEVEL=DEBUG
```

Create them from the command line:

```bash
cat > config_data/low_power.conf << 'EOF'
# Low power mode configuration
MODE=power_save
SAMPLE_INTERVAL=60
TX_POWER=10
LOG_LEVEL=INFO
EOF

cat > config_data/balanced.conf << 'EOF'
# Balanced mode configuration
MODE=balanced
SAMPLE_INTERVAL=30
TX_POWER=50
LOG_LEVEL=INFO
EOF

cat > config_data/high_perf.conf << 'EOF'
# High performance mode configuration
MODE=high_performance
SAMPLE_INTERVAL=5
TX_POWER=100
LOG_LEVEL=DEBUG
EOF
```

Also create a simple diagnostic script that will be uploaded and executed on the remote device:

```bash
cat > diagnostic.sh << 'EOF'
#!/bin/sh
# Remote diagnostic script
# Arguments: config file path and output log path

CONFIG_FILE="$1"
OUTPUT_LOG="$2"

echo "============================================"
echo "Remote Diagnostic Script"
echo "Host: $(hostname)"
echo "Date: $(date)"
echo "Config: $CONFIG_FILE"
echo "============================================"

# Load configuration
if [ -f "$CONFIG_FILE" ]; then
    echo "Loading configuration from $CONFIG_FILE..."
    source "$CONFIG_FILE"
    echo "MODE=$MODE"
    echo "SAMPLE_INTERVAL=$SAMPLE_INTERVAL"
    echo "TX_POWER=$TX_POWER"
    echo "LOG_LEVEL=$LOG_LEVEL"
else
    echo "ERROR: Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Simulate diagnostics
echo ""
echo "Running diagnostics..."
echo "CPU temperature: $(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo '42.5')°C"
echo "Memory available: $(free -m | awk '/Mem:/ {print $7}') MB"
echo "Uptime: $(uptime -p)"

# Write results to output log
{
    echo "TEST_RESULT=PASS"
    echo "MODE=$MODE"
    echo "TIMESTAMP=$(date +%s)"
    echo "DIAG_STATUS=completed"
} > "$OUTPUT_LOG"

echo ""
echo "Results written to $OUTPUT_LOG"
exit 0
EOF

chmod +x diagnostic.sh
```

### What Happens

You now have three configuration files (`low_power.conf`, `balanced.conf`, `high_perf.conf`) representing different device operating modes, plus a `diagnostic.sh` script that will be uploaded to the remote host. Each configuration file will be treated as a separate case in the experiment.

## Step 2: Verify Remote Host Connectivity

Before building the experiment, verify you can reach your remote host via SSH:

```bash
ssh username@192.168.1.100
# Replace with your actual username and host
```

Confirm that:
- The SSH connection succeeds.
- You have write access to a directory on the remote host (e.g., `/tmp`).
- You can run simple commands like `whoami`, `uname -a`.

> **Note:** If you do not have a real remote host, you can install and test against localhost SSH:
> ```bash
> sudo apt-get install openssh-server   # Ubuntu/Debian
> sudo systemctl start ssh
> ssh localhost
> ```

## Step 3: Write the Remote Experiment Configuration

Create the file `remote-experiment.toml` in your project directory.

```toml
# =============================================================================
# Remote SSH/SFTP Experiment Configuration
# =============================================================================
# This experiment uploads configuration files to a remote device, runs a
# diagnostic script, downloads the results, and verifies connectivity.
# =============================================================================

# --- Connection Credentials ---
# Define the SSH connection parameters used throughout the experiment.
# Replace with your actual remote host details.
host = "192.168.1.100"
ssh_user = "pi"
ssh_pass = "raspberry"
ssh_port = 22

# --- Remote Paths ---
remote_work_dir = "/tmp/emtorch_test"
remote_config_path = "$remote_work_dir/$EMTORCH_DATA_FILENAME"
remote_script_path = "$remote_work_dir/diagnostic.sh"
remote_results_path = "$remote_work_dir/results_$EMTORCH_CASE_ID.log"

# --- Timing Configuration ---
[delays]
between_cases = 1.0        # Allow cleanup time between remote operations
before_actions = 2.0       # Extra time for SFTP transfers to stabilize

# =============================================================================
# SETUPS PHASE — Prepare remote environment
# =============================================================================

[[setups]]
type = "echo"
name = "setup_announce"

[setups.args]
message = "=== Remote Test Case $EMTORCH_CASE_ID — $EMTORCH_DATA_FILENAME ==="

# Create the remote working directory
[[setups]]
type = "remote"
name = "create_remote_dir"

[setups.args]
connection = { host = "$host", port = $ssh_port, username = "$ssh_user", password = "$ssh_pass" }
cmd = "mkdir -p $remote_work_dir"
timeout = 5

# Upload the diagnostic script to the remote host
[[setups]]
type = "sftp-put"
name = "upload_script"

[setups.args]
local_path = "./diagnostic.sh"
remote_path = "$remote_script_path"
connection = { host = "$host", port = $ssh_port, username = "$ssh_user", password = "$ssh_pass" }
timeout = 10

# Upload the configuration file for this case
[[setups]]
type = "sftp-put"
name = "upload_config"

[setups.args]
local_path = "$EMTORCH_DATA_PATH"
remote_path = "$remote_config_path"
connection = { host = "$host", port = $ssh_port, username = "$ssh_user", password = "$ssh_pass" }
timeout = 10

# Make the script executable on the remote host
[[setups]]
type = "remote"
name = "make_script_executable"

[setups.args]
connection = { host = "$host", port = $ssh_port, username = "$ssh_user", password = "$ssh_pass" }
cmd = "chmod +x $remote_script_path"
timeout = 5

# =============================================================================
# ACTIONS PHASE — Execute remote diagnostics
# =============================================================================

[[actions]]
type = "echo"
name = "action_announce"

[actions.args]
message = "Running remote diagnostics with $EMTORCH_DATA_FILENAME"

# Run the diagnostic script on the remote device
[[actions]]
type = "remote"
name = "run_diagnostics"

[actions.args]
connection = { host = "$host", port = $ssh_port, username = "$ssh_user", password = "$ssh_pass" }
cmd = "$remote_script_path $remote_config_path $remote_results_path"
timeout = 30

# =============================================================================
# CHECKS PHASE — Download results and verify
# =============================================================================

# Download the results file from the remote host
[[checks]]
type = "sftp-get"
name = "download_results"

[checks.args]
local_path = "./results/results_$EMTORCH_CASE_ID.log"
remote_path = "$remote_results_path"
connection = { host = "$host", port = $ssh_port, username = "$ssh_user", password = "$ssh_pass" }
timeout = 15

# Display the downloaded results
[[checks]]
type = "shell"
name = "display_results"

[checks.args]
cmd = "echo '=== Downloaded results for case $EMTORCH_CASE_ID ===' && cat ./results/results_$EMTORCH_CASE_ID.log"
timeout = 3

# Verify remote device is still responsive
[[checks]]
type = "remote"
name = "verify_device_alive"

[checks.args]
connection = { host = "$host", port = $ssh_port, username = "$ssh_user", password = "$ssh_pass" }
cmd = "echo 'Device responsive: $(hostname) uptime $(uptime -p)'"
timeout = 10

# Final completion message
[[checks]]
type = "echo"
name = "case_complete"

[checks.args]
message = "=== Remote test case $EMTORCH_CASE_ID complete ==="
```

### Understanding the Configuration

**Connection Reuse via Template Variables:**
Notice how the SSH connection details (`host`, `ssh_user`, `ssh_pass`, `ssh_port`) are defined at the top level of the TOML file as plain keys. They are referenced in each subtask via template variables like `$host`, `$ssh_user`, `$ssh_pass`, `$ssh_port`. This avoids repeating credentials in every subtask block and makes the configuration easier to maintain.

> **Important:** Template variables in emtorch only resolve `$EMTORCH_*` variables automatically. The top-level keys shown here (`host`, `ssh_user`, etc.) are used as a convention for readability. In practice you should either:
> 1. Inline the connection object in each subtask (as shown above with `connection = { host = "$host", ... }` — note that template substitution happens on all string values, so the top-level keys are substituted if they are referenced in subtask arguments).
> 2. Define a single connection block and repeat it. (emtorch does not support TOML anchors like YAML.)

For this tutorial, the values are written inline in each subtask for clarity. In a real project, consider using environment variables or a separate credentials file.

**Remote Path Construction:**
The `remote_work_dir` defines a base directory on the remote device (`/tmp/emtorch_test`). Remote paths for the config file, script, and results are constructed from this base directory using template variables:
- `$remote_work_dir/$EMTORCH_DATA_FILENAME` — the uploaded configuration file
- `$remote_work_dir/diagnostic.sh` — the diagnostic script (same for all cases)
- `$remote_work_dir/results_$EMTORCH_CASE_ID.log` — the output log, unique per case

**Phases Breakdown:**

| Phase | Subtask | Purpose |
|-------|---------|---------|
| Setups | `setup_announce` | Log the start of this case |
| Setups | `create_remote_dir` | Ensure the remote working directory exists |
| Setups | `upload_script` | Transfer `diagnostic.sh` to the remote device |
| Setups | `upload_config` | Transfer the case-specific config file |
| Setups | `make_script_executable` | Set execute permissions on the remote script |
| Actions | `action_announce` | Log that actions are starting |
| Actions | `run_diagnostics` | Execute the diagnostic script on the remote device |
| Checks | `download_results` | Retrieve the results log from the remote device |
| Checks | `display_results` | Print the downloaded results locally |
| Checks | `verify_device_alive` | Confirm the device is still responsive |
| Checks | `case_complete` | Log completion |

## Step 4: Prepare Local Results Directory

The `download_results` subtask writes files to a `./results/` directory. Create it before running:

```bash
mkdir -p results
```

## Step 5: Run the Experiment

Execute the experiment against all three configuration files:

```bash
mkdir -p results
python3 -m emtorch run config_data/low_power.conf config_data/balanced.conf config_data/high_perf.conf -c remote-experiment.toml -o remote_results_
```

Or using a glob:

```bash
python3 -m emtorch run config_data/*.conf -c remote-experiment.toml -o remote_results_
```

### What Happens

For each configuration file:

1. **Setups:** The remote `/tmp/emtorch_test/` directory is created. `diagnostic.sh` is uploaded (once; it is uploaded each case but overwrites the same remote file). The case-specific config file is uploaded to the remote device. The script is made executable.

2. **Actions:** The diagnostic script runs on the remote device, sourcing the uploaded config file and writing results to a log file named after the case ID.

3. **Checks:** The results log is downloaded to the local `./results/` directory. Its contents are displayed. A final remote command verifies the device is still responsive.

> **Key Concept — SFTP Upload Overwrites:**
> The `remote_path` for `upload_config` is `$remote_work_dir/$EMTORCH_DATA_FILENAME`. Since each config file has a unique filename (`low_power.conf`, `balanced.conf`, `high_perf.conf`), no collision occurs. The `upload_script` subtask always uploads to the same `remote_script_path`, so each case overwrites the previous one — which is fine since the script does not change between cases.

## Step 6: Examine the Results

```bash
ls -la remote_results_*.json
cat remote_results_0.json
```

The JSON output for each case will show the full sequence of operations. Here is an excerpt from `remote_results_0.json`:

```json
{
  "case_id": "0",
  "data_path": "/home/user/emtorch-remote-tutorial/config_data/low_power.conf",
  "data_filename": "low_power.conf",
  "results": {
    "setups": {
      "setup_announce": {
        "status": "SUCCESS",
        "log": "=== Remote Test Case 0 — low_power.conf ===\n"
      },
      "create_remote_dir": {
        "status": "SUCCESS",
        "log": ""
      },
      "upload_script": {
        "status": "SUCCESS",
        "log": ""
      },
      "upload_config": {
        "status": "SUCCESS",
        "log": ""
      },
      "make_script_executable": {
        "status": "SUCCESS",
        "log": ""
      }
    },
    "actions": {
      "action_announce": {
        "status": "SUCCESS",
        "log": "Running remote diagnostics with low_power.conf\n"
      },
      "run_diagnostics": {
        "status": "SUCCESS",
        "log": "============================================\nRemote Diagnostic Script\nHost: raspberrypi\nDate: Mon Jun 15 10:45:00 UTC 2026\nConfig: /tmp/emtorch_test/low_power.conf\n============================================\nLoading configuration from /tmp/emtorch_test/low_power.conf...\nMODE=power_save\nSAMPLE_INTERVAL=60\nTX_POWER=10\nLOG_LEVEL=INFO\nRunning diagnostics...\nCPU temperature: 42.5°C\nMemory available: 1824 MB\nUptime: up 3 hours, 15 minutes\nResults written to /tmp/emtorch_test/results_0.log\n"
      }
    },
    "checks": {
      "download_results": {
        "status": "SUCCESS",
        "log": ""
      },
      "display_results": {
        "status": "SUCCESS",
        "log": "=== Downloaded results for case 0 ===\nTEST_RESULT=PASS\nMODE=power_save\nTIMESTAMP=1731617100\nDIAG_STATUS=completed\n"
      },
      "verify_device_alive": {
        "status": "SUCCESS",
        "log": "Device responsive: raspberrypi up  up 3 hours, 15 minutes\n"
      },
      "case_complete": {
        "status": "SUCCESS",
        "log": "=== Remote test case 0 complete ===\n"
      }
    }
  }
}
```

Also check the downloaded result files:

```bash
cat results/results_0.log
cat results/results_1.log
cat results/results_2.log
```

These local files contain the diagnostic output generated remotely, now available on your local machine for further analysis.

## Step 7: Handling Timeouts and Errors

Remote operations are inherently less reliable than local ones. Networks lag, devices reboot, and connections drop. Here is how to handle these scenarios.

### Adjusting Timeouts

The default timeout for `remote` subtasks is 5 seconds. For long-running remote operations, increase this value:

```toml
[[actions]]
type = "remote"
name = "long_running_task"
[actions.args]
connection = { host = "192.168.1.100", username = "pi", password = "raspberry" }
cmd = "sleep 20 && echo done"
timeout = 30    # Must exceed the expected duration
```

If a `remote` subtask times out, its status becomes `TIMEOUT` and the experiment continues to the next subtask (unless you build dependency logic into your commands).

### Handling Connection Failures

When a remote host is unreachable, the `remote` subtask returns `ERROR`. You can plan for this by:

1. **Using `ping-alive` in setups** to pre-check connectivity before attempting SSH:

```toml
[[setups]]
type = "ping-alive"
name = "check_host_reachable"
[setups.args]
host = "192.168.1.100"
timeout = 5
interval = 100
```

2. **Separating critical and non-critical operations** — place essential remote operations in `setups` so the experiment stops early if the device is unreachable.

### SFTP Error Scenarios

The `sftp-put` and `sftp-get` subtasks can fail if:

- The remote path does not exist (SFTP does not create parent directories).
- Permissions are insufficient (use a writable directory like `/tmp`).
- Disk space on the remote host is exhausted.
- The connection drops mid-transfer.

Mitigations:

- Always create the remote directory in a prior `remote` subtask.
- Use short timeouts for small files, longer for large transfers.
- Verify file existence with a `remote` command after upload.

```toml
[[checks]]
type = "remote"
name = "verify_upload"
[checks.args]
connection = { host = "192.168.1.100", username = "pi", password = "raspberry" }
cmd = "ls -la $remote_config_path"
timeout = 5
```

### Simulating an Error for Testing

To see how emtorch handles failures, run the experiment with an unreachable host:

```toml
# Temporarily change to test error handling
host = "192.168.1.999"  # Non-existent host
```

The experiment will produce results showing `ERROR` or `TIMEOUT` statuses for the remote subtasks, while local subtasks (like `echo`) still succeed.

## Complete Configuration

Here is the complete `remote-experiment.toml` file:

```toml
[delays]
between_cases = 1.0
before_actions = 2.0

[[setups]]
type = "echo"
name = "setup_announce"
[setups.args]
message = "=== Remote Test Case $EMTORCH_CASE_ID — $EMTORCH_DATA_FILENAME ==="

[[setups]]
type = "remote"
name = "create_remote_dir"
[setups.args]
connection = { host = "192.168.1.100", port = 22, username = "pi", password = "raspberry" }
cmd = "mkdir -p /tmp/emtorch_test"
timeout = 5

[[setups]]
type = "sftp-put"
name = "upload_script"
[setups.args]
local_path = "./diagnostic.sh"
remote_path = "/tmp/emtorch_test/diagnostic.sh"
connection = { host = "192.168.1.100", port = 22, username = "pi", password = "raspberry" }
timeout = 10

[[setups]]
type = "sftp-put"
name = "upload_config"
[setups.args]
local_path = "$EMTORCH_DATA_PATH"
remote_path = "/tmp/emtorch_test/$EMTORCH_DATA_FILENAME"
connection = { host = "192.168.1.100", port = 22, username = "pi", password = "raspberry" }
timeout = 10

[[setups]]
type = "remote"
name = "make_script_executable"
[setups.args]
connection = { host = "192.168.1.100", port = 22, username = "pi", password = "raspberry" }
cmd = "chmod +x /tmp/emtorch_test/diagnostic.sh"
timeout = 5

[[actions]]
type = "echo"
name = "action_announce"
[actions.args]
message = "Running remote diagnostics with $EMTORCH_DATA_FILENAME"

[[actions]]
type = "remote"
name = "run_diagnostics"
[actions.args]
connection = { host = "192.168.1.100", port = 22, username = "pi", password = "raspberry" }
cmd = "/tmp/emtorch_test/diagnostic.sh /tmp/emtorch_test/$EMTORCH_DATA_FILENAME /tmp/emtorch_test/results_$EMTORCH_CASE_ID.log"
timeout = 30

[[checks]]
type = "sftp-get"
name = "download_results"
[checks.args]
local_path = "./results/results_$EMTORCH_CASE_ID.log"
remote_path = "/tmp/emtorch_test/results_$EMTORCH_CASE_ID.log"
connection = { host = "192.168.1.100", port = 22, username = "pi", password = "raspberry" }
timeout = 15

[[checks]]
type = "shell"
name = "display_results"
[checks.args]
cmd = "echo '=== Downloaded results for case $EMTORCH_CASE_ID ===' && cat ./results/results_$EMTORCH_CASE_ID.log"
timeout = 3

[[checks]]
type = "remote"
name = "verify_device_alive"
[checks.args]
connection = { host = "192.168.1.100", port = 22, username = "pi", password = "raspberry" }
cmd = "echo 'Device responsive: $(hostname) uptime $(uptime -p)'"
timeout = 10

[[checks]]
type = "echo"
name = "case_complete"
[checks.args]
message = "=== Remote test case $EMTORCH_CASE_ID complete ==="
```

## Running the Tutorial

```bash
# 1. Create project structure
mkdir -p ~/emtorch-remote-tutorial/config_data
mkdir -p ~/emtorch-remote-tutorial/results
cd ~/emtorch-remote-tutorial

# 2. Create configuration files
cat > config_data/low_power.conf << 'EOF'
MODE=power_save
SAMPLE_INTERVAL=60
TX_POWER=10
LOG_LEVEL=INFO
EOF

cat > config_data/balanced.conf << 'EOF'
MODE=balanced
SAMPLE_INTERVAL=30
TX_POWER=50
LOG_LEVEL=INFO
EOF

cat > config_data/high_perf.conf << 'EOF'
MODE=high_performance
SAMPLE_INTERVAL=5
TX_POWER=100
LOG_LEVEL=DEBUG
EOF

# 3. Create diagnostic script
cat > diagnostic.sh << 'SCRIPT_EOF'
#!/bin/sh
CONFIG_FILE="$1"
OUTPUT_LOG="$2"
echo "Remote Diagnostic Script"
echo "Host: $(hostname)"
echo "Config: $CONFIG_FILE"
source "$CONFIG_FILE" 2>/dev/null || echo "Using defaults"
echo "MODE=${MODE:-unknown}"
{
    echo "TEST_RESULT=PASS"
    echo "MODE=${MODE:-unknown}"
    echo "TIMESTAMP=$(date +%s)"
    echo "DIAG_STATUS=completed"
} > "$OUTPUT_LOG"
echo "Results written to $OUTPUT_LOG"
exit 0
SCRIPT_EOF
chmod +x diagnostic.sh

# 4. Save the configuration (from Complete Configuration section) as remote-experiment.toml
#    IMPORTANT: Replace 192.168.1.100, pi, raspberry with your actual remote host details

# 5. Run the experiment
python3 -m emtorch run config_data/*.conf -c remote-experiment.toml -o remote_results_

# 6. View results
cat remote_results_0.json
cat results/results_0.log
```

## Expected Output

When the experiment runs successfully, you will see console output similar to:

```
[INFO] Loaded configuration from remote-experiment.toml
[INFO] Created 3 cases
[INFO] Starting case 0 (low_power.conf)
[INFO] Setups phase: SUCCESS
[INFO] Actions phase: SUCCESS
[INFO] Checks phase: SUCCESS
[INFO] Case 0 complete: SUCCESS
[INFO] Starting case 1 (balanced.conf)
[INFO] Setups phase: SUCCESS
[INFO] Actions phase: SUCCESS
[INFO] Checks phase: SUCCESS
[INFO] Case 1 complete: SUCCESS
[INFO] Starting case 2 (high_perf.conf)
[INFO] Setups phase: SUCCESS
[INFO] Actions phase: SUCCESS
[INFO] Checks phase: SUCCESS
[INFO] Case 2 complete: SUCCESS
[INFO] All cases complete. 3/3 succeeded.
[INFO] Results written to remote_results_*.json
```

The local `./results/` directory will contain three files with the diagnostic output from the remote device:

```
$ cat results/results_0.log
TEST_RESULT=PASS
MODE=power_save
TIMESTAMP=1731617100
DIAG_STATUS=completed
```

## Troubleshooting

### "Connection refused" or "Connection timed out"

**Causes:** Remote host is unreachable, SSH server is not running, or firewall is blocking port 22.

**Solutions:**
- Verify the host is reachable: `ping 192.168.1.100`
- Check SSH port is open: `nc -zv 192.168.1.100 22`
- Confirm SSH server is running on the remote host: `sudo systemctl status ssh`
- Verify credentials and host address in the configuration

### "Authentication failed"

**Causes:** Incorrect username or password.

**Solutions:**
- Double-check credentials in the `connection` object.
- Test with `ssh user@host` manually to confirm the password works.
- If using key-based authentication, ensure the correct key is loaded in your SSH agent. (emtorch's `remote` subtask currently supports password-based authentication.)

### "File not found" on SFTP operations

**Causes:** Remote directory does not exist, or the source file is missing.

**Solutions:**
- Ensure the remote directory is created before the SFTP transfer (use `mkdir -p` in a `remote` subtask in `setups`).
- Verify the local path exists before uploading.
- For `sftp-get`, confirm the remote file was created by the previous command.

```bash
# Test the full remote workflow manually:
ssh pi@192.168.1.100 "mkdir -p /tmp/emtorch_test"
scp diagnostic.sh pi@192.168.1.100:/tmp/emtorch_test/
ssh pi@192.168.1.100 "chmod +x /tmp/emtorch_test/diagnostic.sh"
ssh pi@192.168.1.100 "/tmp/emtorch_test/diagnostic.sh /tmp/emtorch_test/test.conf /tmp/emtorch_test/output.log"
scp pi@192.168.1.100:/tmp/emtorch_test/output.log .
```

### Remote command returns non-zero exit code

If your remote script fails, the `remote` subtask returns `FAILURE`. Check the `log` field in the JSON result for the error message.

Common causes:
- Missing dependencies on the remote host (e.g., `free` command not available).
- Syntax errors in the remote script.
- Permission issues executing the script.

### SFTP transfer is slow or times out

- Increase the `timeout` value for the SFTP subtask.
- Check network bandwidth and latency between local and remote hosts.
- For large files, consider compressing them before transfer.

### Template variables not expanding in remote commands

Template variables are only expanded in subtask argument values, not inside the remote shell command string itself. If you need to pass case-specific data to a remote command, pass it as a shell argument:

```toml
# Correct: pass as argument
cmd = "/tmp/script.sh /tmp/data_$EMTORCH_CASE_ID.txt"

# Incorrect: embedded in the middle of a string that is not a path
cmd = "echo The current case is $EMTORCH_CASE_ID"
```

The second example *will* work because the entire `cmd` string undergoes template substitution before being sent to the remote host. Both approaches are valid.

## Next Steps

Now that you can test remote devices, explore these advanced topics:

| Topic | Resource |
|-------|----------|
| **Remote connectivity checks** | [ping-alive subtask](../subtasks/ping-alive.md) |
| **Stable connection verification** | [ping-stable subtask](../subtasks/ping-stable.md) |
| **SFTP upload documentation** | [sftp-put subtask](../subtasks/sftp-put.md) |
| **SFTP download documentation** | [sftp-get subtask](../subtasks/sftp-get.md) |
| **Remote command execution** | [remote subtask](../subtasks/remote.md) |
| **IoT device monitoring** | [CoAP Device Monitoring](./coap-monitoring.md) |
| **Data extraction from logs** | [Data Collection with Log Matching](./log-collection.md) |

## Key Takeaways

- **The `remote` subtask executes shell commands on a remote host via SSH.** Provide connection details (host, username, password) and a command string.
- **`sftp-put` and `sftp-get` transfer files to and from remote hosts.** Always ensure the target directory exists on the receiving end before transferring.
- **Set appropriate timeouts for remote operations.** Network latency means remote subtasks need longer timeouts than local ones — start with 10–30 seconds.
- **Use template variables** like `$EMTORCH_DATA_PATH` and `$EMTORCH_DATA_FILENAME` to make remote paths dynamic per case.
- **Verify remote connectivity first** with a `ping-alive` or simple `remote` command in the setups phase.
- **Handle errors gracefully** by checking result statuses and planning for timeouts in your experiment logic.
- **Test manually first** — always verify the SSH/SFTP workflow manually before encoding it in an emtorch configuration.
