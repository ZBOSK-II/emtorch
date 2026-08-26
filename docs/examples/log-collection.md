<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# Tutorial: Data Collection with Log Matching

## Overview

This tutorial teaches you how to extract numerical metrics from command output using emtorch's logger matcher subtasks. You will learn how to use `logger-int-matcher` to capture integer values, `logger-float-matcher` to capture floating-point numbers, construct regular expressions with named capture groups (`(?P<value>...)`), reference other subtasks' output for matching, and collect multiple metrics from a single command's output. By the end of this guide you will be able to automatically extract performance measurements, sensor readings, and other numeric data from experiment logs — turning raw command output into structured, analysable results.

## Prerequisites

**Software:**
- Python 3.14 or later with emtorch installed
- A terminal environment
- Basic command-line skills (running commands, creating files)

**Knowledge:**
- Understanding of emtorch core concepts (cases, phases, subtasks) — complete the [Basic Experiment Tutorial](./basic-experiment.md) first if needed
- Familiarity with regular expressions (regex) — specifically named capture groups `(?P<name>...)`
- Understanding of JSON format for results

**Hardware:**
- Any machine capable of running emtorch (no special hardware required)

> **Regex Refresher — Named Capture Groups:**
> A named capture group in regex uses the syntax `(?P<name>pattern)` where `name` is the identifier for the captured value and `pattern` is the regex that matches it. For example, the pattern `Throughput: (?P<value>\d+\.\d+)` captures the number after "Throughput: " and labels it as `value`. The logger matcher subtasks specifically look for a group named `value` to extract the numeric data.

## Scenario

You are benchmarking a data processing pipeline and need to extract multiple performance metrics from its output. The pipeline produces log lines like:

```
Throughput: 1234.56 ops/sec
Latency: 42.3 ms
Packet Loss: 0.05%
Total Packets: 1048576
Errors: 3
```

Your goal is to automatically extract all these metrics across multiple test runs (cases) and collect them into structured JSON results for later analysis. Instead of manually copying numbers from logs, emtorch's logger matchers will do this for you.

## Step 1: Prepare the Project and Test Script

Create a project directory and a script that simulates a performance benchmark.

```bash
mkdir -p ~/emtorch-log-collection
cd ~/emtorch-log-collection
mkdir -p test_data
```

Create a simple benchmark script that produces realistic performance output:

```bash
cat > benchmark.sh << 'SCRIPT_EOF'
#!/bin/bash
# Simulated benchmark script
# Usage: benchmark.sh <data_file>
# Reads a parameter from the data file and generates performance metrics.

DATA_FILE="$1"

if [ ! -f "$DATA_FILE" ]; then
    echo "ERROR: Data file not found: $DATA_FILE"
    exit 1
fi

# Read the scaling factor from the data file
SCALE=$(cat "$DATA_FILE")

echo "=========================================="
echo "Performance Benchmark Report"
echo "=========================================="
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Data file: $DATA_FILE"
echo "Scale factor: $SCALE"
echo "------------------------------------------"

# Simulate metrics that vary based on the scale factor
THROUGHPUT=$(python3 -c "print(f'{$SCALE * 1000 + 200:.2f}')" 2>/dev/null || echo "$((SCALE * 1000 + 200)).00")
LATENCY=$(python3 -c "print(f'{$SCALE * 5 + 20:.1f}')" 2>/dev/null || echo "$((SCALE * 5 + 20)).0")
PACKET_LOSS=$(python3 -c "print(f'{$SCALE * 0.02 + 0.01:.2f}')" 2>/dev/null || echo "0.0$SCALE")
TOTAL_PACKETS=$((SCALE * 100000 + 50000))
ERRORS=$((SCALE * 2))

# Use Python for more accurate calculations if available
if command -v python3 &>/dev/null; then
    THROUGHPUT=$(python3 -c "print(f'{$SCALE * 1000 + 200:.2f}')")
    LATENCY=$(python3 -c "print(f'{$SCALE * 5 + 20:.1f}')")
    PACKET_LOSS=$(python3 -c "print(f'{$SCALE * 0.02 + 0.01:.2f}')")
fi

echo "Throughput: $THROUGHPUT ops/sec"
echo "Latency: $LATENCY ms"
echo "Packet Loss: $PACKET_LOSS%"
echo "Total Packets: $TOTAL_PACKETS"
echo "Errors: $ERRORS"
echo "------------------------------------------"
echo "Benchmark complete."
exit 0
SCRIPT_EOF

chmod +x benchmark.sh
```

Create data files that control the benchmark parameters:

```bash
# Small workload
echo "1" > test_data/workload_small.txt

# Medium workload
echo "5" > test_data/workload_medium.txt

# Large workload
echo "10" > test_data/workload_large.txt
```

Test the script manually:

```bash
./benchmark.sh test_data/workload_small.txt
```

You should see output like:

```
==========================================
Performance Benchmark Report
==========================================
Date: 2026-06-15 10:30:00
Data file: test_data/workload_small.txt
Scale factor: 1
------------------------------------------
Throughput: 1200.00 ops/sec
Latency: 25.0 ms
Packet Loss: 0.03%
Total Packets: 150000
Errors: 2
------------------------------------------
Benchmark complete.
```

### What Happens

You have created a benchmark script that simulates performance testing. The data files contain a single number (a scale factor) that influences the metrics. By running this script with different data files, you generate different performance profiles. The emtorch experiment will execute this script for each case and then extract the metrics from the output using logger matchers.

## Step 2: Write the Logger Matcher Configuration

Create `log-collection.toml`:

```toml
# =============================================================================
# Log Collection Experiment Configuration
# =============================================================================
# This experiment runs a benchmark script and extracts numeric metrics from
# its output using logger-int-matcher and logger-float-matcher subtasks.
# =============================================================================

[delays]
between_cases = 0.5
before_actions = 0.5

# =============================================================================
# SETUPS PHASE
# =============================================================================

[[setups]]
type = "echo"
name = "announce_case"

[setups.args]
message = "=== Benchmark case $EMTORCH_CASE_ID — $EMTORCH_DATA_FILENAME ==="

# Display the scale factor from the data file
[[setups]]
type = "shell"
name = "show_scale_factor"

[setups.args]
cmd = "echo 'Scale factor:' && cat $EMTORCH_DATA_PATH"
timeout = 3

# =============================================================================
# ACTIONS PHASE
# =============================================================================
# Run the benchmark. Its output will be scanned by logger matchers in checks.

[[actions]]
type = "echo"
name = "starting_benchmark"

[actions.args]
message = "Running benchmark for case $EMTORCH_CASE_ID..."

[[actions]]
type = "shell"
name = "run_benchmark"

[actions.args]
cmd = "./benchmark.sh $EMTORCH_DATA_PATH"
timeout = 15

# =============================================================================
# CHECKS PHASE — Extract metrics using logger matchers
# =============================================================================
# Each logger matcher scans the output of the "run_benchmark" subtask and
# extracts a specific numeric value using a regex with a named capture group.

# --- Extract Throughput (float) ---
# Line format: "Throughput: 1234.56 ops/sec"
[[checks]]
type = "logger-float-matcher"
name = "extract_throughput"

[checks.args]
value = "throughput"
pattern = "Throughput: (?P<value>\\d+\\.\\d+)"
subtask = "run_benchmark"

# --- Extract Latency (float) ---
# Line format: "Latency: 42.3 ms"
[[checks]]
type = "logger-float-matcher"
name = "extract_latency"

[checks.args]
value = "latency_ms"
pattern = "Latency: (?P<value>\\d+\\.\\d+)"
subtask = "run_benchmark"

# --- Extract Packet Loss (float) ---
# Line format: "Packet Loss: 0.05%"
[[checks]]
type = "logger-float-matcher"
name = "extract_packet_loss"

[checks.args]
value = "packet_loss_pct"
pattern = "Packet Loss: (?P<value>\\d+\\.\\d+)"
subtask = "run_benchmark"

# --- Extract Total Packets (integer) ---
# Line format: "Total Packets: 150000"
[[checks]]
type = "logger-int-matcher"
name = "extract_total_packets"

[checks.args]
value = "total_packets"
pattern = "Total Packets: (?P<value>\\d+)"
subtask = "run_benchmark"

# --- Extract Errors (integer) ---
# Line format: "Errors: 3"
[[checks]]
type = "logger-int-matcher"
name = "extract_errors"

[checks.args]
value = "errors"
pattern = "Errors: (?P<value>\\d+)"
subtask = "run_benchmark"

# --- Summary of extracted values ---
[[checks]]
type = "echo"
name = "case_summary"

[checks.args]
message = "=== Case $EMTORCH_CASE_ID metrics extracted ==="
```

### How Logger Matchers Work

The logger matcher subtasks (`logger-float-matcher` and `logger-int-matcher`) follow a three-step process:

1. **Reference a source subtask:** The `subtask` parameter names another subtask whose log output should be scanned. In this configuration, all matchers reference `"run_benchmark"`, the shell subtask that executed the benchmark script.

2. **Apply a regex pattern:** The `pattern` parameter is a regular expression with a named capture group `(?P<value>...)`. The matcher searches the entire log output for this pattern. Everything matched by `(?P<value>...)` is extracted as the numeric value.

3. **Store under a name:** The `value` parameter provides a name for the extracted metric. This name appears in the results JSON under the `values` dictionary.

> **Important — Regex Escaping in TOML:**
> Backslashes in TOML strings must be escaped. When writing regex patterns in TOML:
> - `\d` becomes `\\d`
> - `\.` becomes `\\.`
> - `\s` becomes `\\s`
>
> The pattern `Throughput: (?P<value>\d+\.\d+)` in TOML must be written as:
> ```
> pattern = "Throughput: (?P<value>\\d+\\.\\d+)"
> ```

**Pattern Breakdown for Each Metric:**

| Metric | Pattern | Matches |
|--------|---------|---------|
| Throughput | `Throughput: (?P<value>\\d+\\.\\d+)` | `1234.56` from `Throughput: 1234.56 ops/sec` |
| Latency | `Latency: (?P<value>\\d+\\.\\d+)` | `42.3` from `Latency: 42.3 ms` |
| Packet Loss | `Packet Loss: (?P<value>\\d+\\.\\d+)` | `0.05` from `Packet Loss: 0.05%` |
| Total Packets | `Total Packets: (?P<value>\\d+)` | `150000` from `Total Packets: 150000` |
| Errors | `Errors: (?P<value>\\d+)` | `3` from `Errors: 3` |

> **Key Concept — Multiple Matchers per Subtask:**
> Multiple logger matchers can reference the same source subtask. This allows you to extract several different metrics from a single command's output. The source subtask only needs to run once; each matcher independently scans its log output.

## Step 3: Run the Experiment

```bash
cd ~/emtorch-log-collection
python3 -m emtorch run test_data/workload_small.txt test_data/workload_medium.txt test_data/workload_large.txt -c log-collection.toml -l log_collection_
```

> **Note:** We use `-l` (output prefix for logs) instead of `-o` here. The `-o` flag writes result JSON files; the `-l` flag writes detailed log files. Check which flag your emtorch version supports:
> ```bash
> python3 -m emtorch run --help
> ```
> If `-o` is the standard output flag, use that instead.

```bash
python3 -m emtorch run test_data/workload_*.txt -c log-collection.toml -o log_collection_
```

### What Happens

For each case:

1. **Setups:** Announce the case and display the scale factor.
2. **Actions:** Run `benchmark.sh` with the case data file. The script outputs performance metrics to stdout.
3. **Checks:** Five logger matcher subtasks each scan the `run_benchmark` output log with their specific regex patterns:
   - `extract_throughput` finds the float after "Throughput: "
   - `extract_latency` finds the float after "Latency: "
   - `extract_packet_loss` finds the float after "Packet Loss: "
   - `extract_total_packets` finds the integer after "Total Packets: "
   - `extract_errors` finds the integer after "Errors: "

Each matcher stores its extracted value in the JSON result under the name given by its `value` parameter.

## Step 4: Examine the Results

```bash
cat log_collection_0.json
```

The JSON output includes extracted values in the `values` field of each logger matcher's result:

```json
{
  "case_id": "0",
  "data_path": "/home/user/emtorch-log-collection/test_data/workload_small.txt",
  "data_filename": "workload_small.txt",
  "results": {
    "setups": {
      "announce_case": {
        "status": "SUCCESS",
        "log": "=== Benchmark case 0 — workload_small.txt ===\n"
      },
      "show_scale_factor": {
        "status": "SUCCESS",
        "log": "Scale factor:\n1\n"
      }
    },
    "actions": {
      "starting_benchmark": {
        "status": "SUCCESS",
        "log": "Running benchmark for case 0...\n"
      },
      "run_benchmark": {
        "status": "SUCCESS",
        "log": "==========================================\nPerformance Benchmark Report\n==========================================\nDate: 2026-06-15 10:30:00\nData file: test_data/workload_small.txt\nScale factor: 1\n------------------------------------------\nThroughput: 1200.00 ops/sec\nLatency: 25.0 ms\nPacket Loss: 0.03%\nTotal Packets: 150000\nErrors: 2\n------------------------------------------\nBenchmark complete.\n"
      }
    },
    "checks": {
      "extract_throughput": {
        "status": "SUCCESS",
        "log": "",
        "values": {
          "throughput": 1200.0
        }
      },
      "extract_latency": {
        "status": "SUCCESS",
        "log": "",
        "values": {
          "latency_ms": 25.0
        }
      },
      "extract_packet_loss": {
        "status": "SUCCESS",
        "log": "",
        "values": {
          "packet_loss_pct": 0.03
        }
      },
      "extract_total_packets": {
        "status": "SUCCESS",
        "log": "",
        "values": {
          "total_packets": 150000
        }
      },
      "extract_errors": {
        "status": "SUCCESS",
        "log": "",
        "values": {
          "errors": 2
        }
      },
      "case_summary": {
        "status": "SUCCESS",
        "log": "=== Case 0 metrics extracted ===\n"
      }
    }
  }
}
```

### Where Extracted Values Appear

The extracted metrics are found in the `values` dictionary inside each logger matcher's result:

```json
"extract_throughput": {
    "status": "SUCCESS",
    "log": "",
    "values": {
        "throughput": 1200.0
    }
}
```

The `values` object uses the name you provided in the `value` parameter of the configuration:
- `value = "throughput"` → `"throughput": 1200.0`
- `value = "latency_ms"` → `"latency_ms": 25.0`
- `value = "packet_loss_pct"` → `"packet_loss_pct": 0.03`
- `value = "total_packets"` → `"total_packets": 150000`
- `value = "errors"` → `"errors": 2`

> **Note:** `logger-int-matcher` stores the value as an integer (no decimal point), while `logger-float-matcher` stores it as a float. This distinction matters if you are aggregating results across cases.

### Compare Across Cases

Now examine the other result files to see how metrics change with different scale factors:

```bash
echo "=== Case 0 (scale=1) ==="
python3 -c "import json; d=json.load(open('log_collection_0.json')); print(json.dumps({k: v.get('values', {}) for k,v in d['results']['checks'].items() if 'values' in v}, indent=2))"

echo "=== Case 1 (scale=5) ==="
python3 -c "import json; d=json.load(open('log_collection_1.json')); print(json.dumps({k: v.get('values', {}) for k,v in d['results']['checks'].items() if 'values' in v}, indent=2))"

echo "=== Case 2 (scale=10) ==="
python3 -c "import json; d=json.load(open('log_collection_2.json')); print(json.dumps({k: v.get('values', {}) for k,v in d['results']['checks'].items() if 'values' in v}, indent=2))"
```

You should see the metrics scaling with the input:

| Metric | Case 0 (scale=1) | Case 1 (scale=5) | Case 2 (scale=10) |
|--------|------------------|------------------|-------------------|
| throughput | 1200.0 | 5200.0 | 10200.0 |
| latency_ms | 25.0 | 45.0 | 70.0 |
| packet_loss_pct | 0.03 | 0.11 | 0.21 |
| total_packets | 150000 | 550000 | 1050000 |
| errors | 2 | 10 | 20 |

## Step 5: Advanced Patterns — Multiple Matchers on Different Subtasks

You can also extract values from subtasks other than the main action. For example, you might want to extract metrics from setup or verification commands as well.

Here is an extended configuration that extracts values from both the setup and action phases:

```toml
# =============================================================================
# Advanced Log Collection — Multiple Source Subtasks
# =============================================================================

[delays]
between_cases = 0.5
before_actions = 0.5

[[setups]]
type = "echo"
name = "start"
[setups.args]
message = "Case $EMTORCH_CASE_ID starting"

# A setup command that generates parseable output
[[setups]]
type = "shell"
name = "check_system"
[setups.args]
cmd = "echo 'CPU Cores: 8' && echo 'Memory: 16384 MB' && echo 'Disk Free: 500000 MB'"
timeout = 3

[[actions]]
type = "echo"
name = "starting_benchmark"
[setups.args]
message = "Running benchmark for case $EMTORCH_CASE_ID..."

[[actions]]
type = "shell"
name = "run_benchmark"
[actions.args]
cmd = "./benchmark.sh $EMTORCH_DATA_PATH"
timeout = 15

# --- Extract from the "check_system" subtask (setups phase) ---
[[checks]]
type = "logger-int-matcher"
name = "extract_cpu_cores"
[checks.args]
value = "cpu_cores"
pattern = "CPU Cores: (?P<value>\\d+)"
subtask = "check_system"

[[checks]]
type = "logger-int-matcher"
name = "extract_memory"
[checks.args]
value = "memory_mb"
pattern = "Memory: (?P<value>\\d+)"
subtask = "check_system"

# --- Extract from the "run_benchmark" subtask (actions phase) ---
[[checks]]
type = "logger-float-matcher"
name = "extract_throughput"
[checks.args]
value = "throughput"
pattern = "Throughput: (?P<value>\\d+\\.\\d+)"
subtask = "run_benchmark"

[[checks]]
type = "logger-float-matcher"
name = "extract_latency"
[checks.args]
value = "latency_ms"
pattern = "Latency: (?P<value>\\d+\\.\\d+)"
subtask = "run_benchmark"

[[checks]]
type = "logger-int-matcher"
name = "extract_errors"
[checks.args]
value = "errors"
pattern = "Errors: (?P<value>\\d+)"
subtask = "run_benchmark"

[[checks]]
type = "echo"
name = "done"
[checks.args]
message = "Case $EMTORCH_CASE_ID complete"
```

This configuration demonstrates that logger matchers can reference any subtask from any earlier phase — not just the most recent action. The `subtask` field simply points to the name of the subtask whose log you want to scan.

## Step 6: Aggregating Results Across Cases

After collecting metrics from multiple cases, you can aggregate them using a simple Python script:

```python
#!/usr/bin/env python3
# aggregate_results.py — Aggregate logger matcher values across all result files
import json
import glob
import sys

def aggregate(prefix="log_collection_"):
    files = sorted(glob.glob(f"{prefix}*.json"))
    if not files:
        print(f"No result files found with prefix '{prefix}'")
        return

    all_values = []

    for fname in files:
        with open(fname) as f:
            data = json.load(f)

        case_values = {"case_id": data["case_id"], "data_file": data["data_filename"]}

        # Extract all values from logger matcher results
        for phase in ["setups", "monitoring", "actions", "checks"]:
            for subtask_name, subtask_result in data["results"].get(phase, {}).items():
                if "values" in subtask_result:
                    for key, val in subtask_result["values"].items():
                        case_values[key] = val

        all_values.append(case_values)

    # Print as table
    if all_values:
        keys = list(all_values[0].keys())
        header = " | ".join(f"{k:>15}" for k in keys)
        sep = "-+-".join("-" * 15 for _ in keys)
        print(header)
        print(sep)
        for entry in all_values:
            row = " | ".join(f"{str(entry.get(k, '')):>15}" for k in keys)
            print(row)

        # Compute averages for numeric fields
        numeric_keys = [k for k in keys if k not in ("case_id", "data_file")]
        print("\n--- Averages ---")
        for k in numeric_keys:
            vals = [e[k] for e in all_values if k in e and isinstance(e[k], (int, float))]
            if vals:
                avg = sum(vals) / len(vals)
                print(f"  {k:>20}: {avg:.2f} (min={min(vals)}, max={max(vals)})")

if __name__ == "__main__":
    prefix = sys.argv[1] if len(sys.argv) > 1 else "log_collection_"
    aggregate(prefix)
```

Run the aggregation script:

```bash
python3 aggregate_results.py log_collection_
```

Output:

```
       case_id |       data_file |      throughput |      latency_ms |  packet_loss_pct |  total_packets |         errors
---------------+-----------------+-----------------+-----------------+------------------+----------------+-----------------
              0 | workload_small.txt |         1200.0 |            25.0 |             0.03 |         150000 |               2
              1 | workload_medium.txt |         5200.0 |            45.0 |             0.11 |         550000 |              10
              2 | workload_large.txt |        10200.0 |            70.0 |             0.21 |        1050000 |              20

--- Averages ---
           throughput: 5533.33 (min=1200.0, max=10200.0)
           latency_ms: 46.67 (min=25.0, max=70.0)
       packet_loss_pct: 0.12 (min=0.03, max=0.21)
        total_packets: 583333.33 (min=150000, max=1050000)
               errors: 10.67 (min=2, max=20)
```

This script demonstrates how emtorch's structured JSON output — with cleanly extracted values — enables straightforward post-processing and analysis.

## Regex Patterns for Common Log Formats

Here are useful regex patterns for extracting values from common log formats:

| Log Format | Pattern (TOML-escaped) | Matcher Type |
|------------|------------------------|--------------|
| `Time: 42.5 ms` | `Time: (?P<value>\\d+\\.\\d+)` | float |
| `Count: 1000 packets` | `Count: (?P<value>\\d+)` | int |
| `temperature=22.5C` | `temperature=(?P<value>\\d+\\.\\d+)` | float |
| `rssi: -45 dBm` | `rssi: (?P<value>-?\\d+)` | int |
| `ratio: 0.95` | `ratio: (?P<value>\\d+\\.\\d+)` | float |
| `voltage=3.3V` | `voltage=(?P<value>\\d+\\.\\d+)` | float |
| `Errors: 0/100` | `Errors: (?P<value>\\d+)/` | int |
| `[42.5] measurement` | `\\[(?P<value>\\d+\\.\\d+)\\]` | float |
| `cpu=75%` | `cpu=(?P<value>\\d+)` | int |
| `speed 1234.56MHz` | `speed (?P<value>\\d+\\.\\d+)` | float |

## Complete Configuration

Here is the complete `log-collection.toml` file:

```toml
[delays]
between_cases = 0.5
before_actions = 0.5

[[setups]]
type = "echo"
name = "announce_case"
[setups.args]
message = "=== Benchmark case $EMTORCH_CASE_ID — $EMTORCH_DATA_FILENAME ==="

[[setups]]
type = "shell"
name = "show_scale_factor"
[setups.args]
cmd = "echo 'Scale factor:' && cat $EMTORCH_DATA_PATH"
timeout = 3

[[actions]]
type = "echo"
name = "starting_benchmark"
[actions.args]
message = "Running benchmark for case $EMTORCH_CASE_ID..."

[[actions]]
type = "shell"
name = "run_benchmark"
[actions.args]
cmd = "./benchmark.sh $EMTORCH_DATA_PATH"
timeout = 15

[[checks]]
type = "logger-float-matcher"
name = "extract_throughput"
[checks.args]
value = "throughput"
pattern = "Throughput: (?P<value>\\d+\\.\\d+)"
subtask = "run_benchmark"

[[checks]]
type = "logger-float-matcher"
name = "extract_latency"
[checks.args]
value = "latency_ms"
pattern = "Latency: (?P<value>\\d+\\.\\d+)"
subtask = "run_benchmark"

[[checks]]
type = "logger-float-matcher"
name = "extract_packet_loss"
[checks.args]
value = "packet_loss_pct"
pattern = "Packet Loss: (?P<value>\\d+\\.\\d+)"
subtask = "run_benchmark"

[[checks]]
type = "logger-int-matcher"
name = "extract_total_packets"
[checks.args]
value = "total_packets"
pattern = "Total Packets: (?P<value>\\d+)"
subtask = "run_benchmark"

[[checks]]
type = "logger-int-matcher"
name = "extract_errors"
[checks.args]
value = "errors"
pattern = "Errors: (?P<value>\\d+)"
subtask = "run_benchmark"

[[checks]]
type = "echo"
name = "case_summary"
[checks.args]
message = "=== Case $EMTORCH_CASE_ID metrics extracted ==="
```

## Running the Tutorial

```bash
# 1. Create project structure
mkdir -p ~/emtorch-log-collection/test_data
cd ~/emtorch-log-collection

# 2. Create benchmark script
cat > benchmark.sh << 'SCRIPT_EOF'
#!/bin/bash
DATA_FILE="$1"
SCALE=$(cat "$DATA_FILE")
if command -v python3 &>/dev/null; then
    THROUGHPUT=$(python3 -c "print(f'{float($SCALE) * 1000 + 200:.2f}')")
    LATENCY=$(python3 -c "print(f'{float($SCALE) * 5 + 20:.1f}')")
    PACKET_LOSS=$(python3 -c "print(f'{float($SCALE) * 0.02 + 0.01:.2f}')")
fi
TOTAL_PACKETS=$((SCALE * 100000 + 50000))
ERRORS=$((SCALE * 2))
echo "Throughput: $THROUGHPUT ops/sec"
echo "Latency: $LATENCY ms"
echo "Packet Loss: $PACKET_LOSS%"
echo "Total Packets: $TOTAL_PACKETS"
echo "Errors: $ERRORS"
exit 0
SCRIPT_EOF
chmod +x benchmark.sh

# 3. Create data files
echo "1" > test_data/workload_small.txt
echo "5" > test_data/workload_medium.txt
echo "10" > test_data/workload_large.txt

# 4. Save the configuration as log-collection.toml (from Complete Configuration)

# 5. Run the experiment
python3 -m emtorch run test_data/workload_*.txt -c log-collection.toml -o log_collection_

# 6. View results
cat log_collection_0.json
cat log_collection_1.json
cat log_collection_2.json

# 7. (Optional) Aggregate results
python3 aggregate_results.py log_collection_
```

## Expected Output

Console output showing progress:

```
[INFO] Loaded configuration from log-collection.toml
[INFO] Created 3 cases
[INFO] Starting case 0 (workload_small.txt)
[INFO] Setups phase: SUCCESS
[INFO] Actions phase: SUCCESS
[INFO] Checks phase: SUCCESS
[INFO] Case 0 complete: SUCCESS
[INFO] Starting case 1 (workload_medium.txt)
[INFO] Setups phase: SUCCESS
[INFO] Actions phase: SUCCESS
[INFO] Checks phase: SUCCESS
[INFO] Case 1 complete: SUCCESS
[INFO] Starting case 2 (workload_large.txt)
[INFO] Setups phase: SUCCESS
[INFO] Actions phase: SUCCESS
[INFO] Checks phase: SUCCESS
[INFO] Case 2 complete: SUCCESS
[INFO] All cases complete. 3/3 succeeded.
[INFO] Results written to log_collection_*.json
```

Each result JSON file contains the extracted values in the `values` dictionary of each logger matcher's result, as shown in Step 4.

## Troubleshooting

### Logger matcher returns FAILURE

The matcher could not find the pattern in the target subtask's log output.

**Common causes:**
- The regex pattern does not match the actual output.
- The `subtask` name is incorrect (must match exactly).
- The source subtask failed or produced no output.
- Backslashes are not properly escaped in TOML.

**Solutions:**
- Check the source subtask's `log` field in the JSON result to see the actual output.
- Test your regex pattern with the actual output using `python3 -c "import re; print(re.search(r'YOUR_PATTERN', 'YOUR_TEXT'))"`.
- Verify the `subtask` value matches the `name` of the target subtask exactly (case-sensitive).
- Ensure backslashes are doubled in TOML: `\d` → `\\d`, `\.` → `\\.`.

```bash
# Quick regex test
python3 -c "
import re
pattern = r'Throughput: (?P<value>\d+\.\d+)'
text = 'Throughput: 1234.56 ops/sec'
match = re.search(pattern, text)
if match:
    print(f'Found: {match.group(\"value\")}')
else:
    print('No match')
"
```

### Integer matcher captures a float or vice versa

- `logger-int-matcher` requires the captured value to be parseable as an integer. If the regex captures `42.5`, it will fail.
- `logger-float-matcher` accepts both integers and floats. Use `logger-int-matcher` when you specifically need an integer type.

### Pattern matches but value is wrong

The regex captures an unexpected portion of the text.

**Solutions:**
- Make the pattern more specific. Instead of `(?P<value>\\d+)`, use `"Latency: (?P<value>\\d+\\.\\d+)"`.
- Anchor the pattern with surrounding context.
- Use word boundaries or ensure the pattern captures only the intended number.

### Multiple matches found in the same log

Logger matchers capture the **first** match of the pattern in the log. If a subtask's output contains multiple matching lines, only the first is extracted.

**Solutions:**
- Make the pattern specific enough to match only the desired line.
- If you need multiple values from different lines, use separate matchers with distinct patterns.

### Subtask referenced by matcher does not exist

If the `subtask` name does not match any defined subtask, the matcher returns ERROR.

**Solutions:**
- Check for typos in the `name` field of the source subtask and the `subtask` field of the matcher.
- Ensure the source subtask is defined in the same configuration file.

## Next Steps

Now that you can extract numeric metrics from logs, explore these advanced topics:

| Topic | Resource |
|-------|----------|
| **Integer matcher details** | [logger-int-matcher subtask](../subtasks/logger-int-matcher.md) |
| **Float matcher details** | [logger-float-matcher subtask](../subtasks/logger-float-matcher.md) |
| **Shell command execution** | [shell subtask](../subtasks/shell.md) |
| **Combining with remote testing** | [Remote Testing with SSH](./remote-testing.md) |
| **Combining with CoAP monitoring** | [CoAP Device Monitoring](./coap-monitoring.md) |
| **Result interpretation** | [Core Concepts - Results](../core-concepts.md#results) |

## Key Takeaways

- **Logger matchers extract numeric values from subtask output** using regex patterns with named capture groups. `logger-float-matcher` extracts floats; `logger-int-matcher` extracts integers.
- **The `subtask` field references the source** whose log output is scanned. Multiple matchers can reference the same source subtask.
- **The `value` field names the extracted metric** and appears as the key in the `values` dictionary of the JSON result.
- **Regex patterns in TOML require escaped backslashes** — `\d` becomes `\\d`, `\.` becomes `\\.`.
- **Patterns must include exactly one named group** `(?P<value>...)` which identifies what to capture.
- **Extracted values appear in the JSON `values` object**, separate from the `log` output, making them easy to access programmatically.
- **Logger matchers run in the checks phase** (or any phase after their source subtask), scanning logs that were already captured.
- **Post-processing is straightforward** — write a simple script to aggregate extracted values across cases for statistical analysis.
