<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# CLI Reference

Complete reference for all emtorch command-line commands and options.

## Overview

emtorch is invoked as a Python module:

```bash
python3 -m emtorch [COMMAND] [OPTIONS] [ARGUMENTS]
```

## Available Commands

- `run` — Execute an experiment against test data
- `subtasks` — List all available subtasks
- `subtask` — Show detailed documentation for a specific subtask

## Global Options

### `--version`

Display the emtorch version and exit.

```bash
python3 -m emtorch --version
```

**Output example:**
```
emtorch 2.1.0
```

---

## `run` Command

Execute an experiment using a TOML configuration file against one or more test data files.

### Syntax

```bash
python3 -m emtorch run <DATA_FILES>... [OPTIONS]
```

### Arguments

#### `<DATA_FILES>...` (Required)

One or more paths to data files to use as test cases. Each file creates one case.

**Supports glob patterns:**

```bash
# Multiple specific files
python3 -m emtorch run data1.bin data2.bin data3.bin -c config.toml

# Glob pattern
python3 -m emtorch run test_data/*.bin -c config.toml

# Shell expansion
python3 -m emtorch run test_data/case_{1..5}.bin -c config.toml
```

### Options

#### `-c` / `--config` (Required)

Path to the TOML configuration file defining the experiment.

```bash
python3 -m emtorch run data.bin -c config.toml
python3 -m emtorch run data.bin --config /path/to/experiment.toml
```

**Configuration file requirements:**
- Valid TOML syntax
- Must define phases (setups, actions, checks, or combinations)
- Can optionally define delays and monitoring phases

#### `-o` / `--output-prefix` (Optional)

Prefix for output JSON result files. Default is `emtorch_`

```bash
python3 -m emtorch run data.bin -c config.toml -o results_
python3 -m emtorch run data.bin -c config.toml --output-prefix experiment_
```

**Output files generated:**
- `{prefix}0.json` — Results for case 0
- `{prefix}1.json` — Results for case 1
- etc.

If you run with `-o results_`, the files will be:
- `results_0.json`
- `results_1.json`
- `results_2.json`
- etc.

#### `-r` / `--repeats` (Optional)

Number of times to repeat the experiment for each data file. Default is 1 (run once).

```bash
# Run each case twice
python3 -m emtorch run data.bin -c config.toml -r 2

# Run each case 5 times
python3 -m emtorch run data.bin -c config.toml --repeats 5
```

**How repeats work:**
- With `-r 2` and 3 data files, you get 6 total cases (3 files × 2 repeats)
- Results are output as sequential case IDs (0, 1, 2, 3, 4, 5)

#### `--repeat-mode` (Optional)

How to organize repeats. Options: `by_file` (default) or `all_at_once`

```bash
# Default: complete all repeats for one file, then move to next
python3 -m emtorch run data1.bin data2.bin -c config.toml -r 2 --repeat-mode by_file

# Alternative: do one repeat of all files, then next repeat of all files
python3 -m emtorch run data1.bin data2.bin -c config.toml -r 2 --repeat-mode all_at_once
```

**Execution order with `-r 2` and files [data1.bin, data2.bin]:**

`by_file` (default):
1. Case 0: repeat 1 of data1.bin
2. Case 1: repeat 2 of data1.bin
3. Case 2: repeat 1 of data2.bin
4. Case 3: repeat 2 of data2.bin

`all_at_once`:
1. Case 0: repeat 1 of data1.bin
2. Case 1: repeat 1 of data2.bin
3. Case 2: repeat 2 of data1.bin
4. Case 3: repeat 2 of data2.bin

### Examples

#### Basic Usage

```bash
python3 -m emtorch run test.bin -c config.toml
```

Runs one case with default output prefix `emtorch_`, creates `emtorch_0.json`

#### Multiple Data Files

```bash
python3 -m emtorch run data/*.bin -c config.toml -o results_
```

Runs one case per file with output prefix `results_`

#### Multiple Repeats

```bash
python3 -m emtorch run test.bin -c config.toml -r 3 -o results_
```

Runs 3 cases (same data file, 3 times) with output prefix `results_`

#### Complex Setup

```bash
python3 -m emtorch run test_data/embedded_*.bin -c experiments/network_test.toml -o network_run_ -r 2
```

- Runs all `embedded_*.bin` files
- Each file runs 2 times
- Configuration from `experiments/network_test.toml`
- Results have prefix `network_run_`

---

## `subtasks` Command

List all available subtasks registered in emtorch.

### Syntax

```bash
python3 -m emtorch subtasks
```

### Output

Shows a list of all available subtasks:

```
Available subtasks:
- coap-monitor
- coap-send
- echo
- exec
- file-write
- logger-float-matcher
- logger-int-matcher
- ping-alive
- ping-stable
- remote
- sftp-get
- sftp-put
- shell
```

---

## `subtask` Command

Show detailed documentation for a specific subtask, including its arguments and defaults.

### Syntax

```bash
python3 -m emtorch subtask <SUBTASK_NAME>
```

### Arguments

#### `<SUBTASK_NAME>` (Required)

Name of the subtask to document. Must be one of the names from `emtorch subtasks`

### Examples

```bash
python3 -m emtorch subtask echo
```

**Output:**
```
echo
====

Basic echo command, prints to log a provided message.


Arguments
---------
  message                  - ($-string) message to write to log
```

```bash
python3 -m emtorch subtask shell
```

**Output:**
```
shell
=====

Executes a system shell command.

Arguments
---------
  cmd                      - ($-string) command to execute
  timeout                  - (float) operation timeout in seconds [default: 1.0]
  signal                   - (str) optional signal to send if timeout [default: None]
```

```bash
python3 -m emtorch subtask remote
```

Shows detailed information about the `remote` subtask including connection options.

---

## Help

Get general help information:

```bash
python3 -m emtorch --help
python3 -m emtorch run --help
```

---

## Exit Codes

emtorch exits with:

- `0` — Success (all cases executed, individual case failures don't affect exit code)
- `1` — Error (configuration error, missing file, invalid arguments, etc.)

**Note:** Individual case failures (when a subtask returns FAILURE) don't cause non-zero exit code. Check the output JSON to determine case success/failure.

---

## Output Format

By default, emtorch outputs JSON result files. See [Core Concepts - Results](./core-concepts.md#results) for the JSON structure.

### Filename Convention

Output files follow the pattern: `{prefix}{case_id}.json`

Examples with `-o results_`:
- `results_0.json`
- `results_1.json`
- `results_2.json`

---

## Common Patterns

### Run with many data files and save results

```bash
mkdir -p results
python3 -m emtorch run data/*.bin -c config.toml -o results/test_
```

### Run with repeats for statistical analysis

```bash
python3 -m emtorch run critical_test.bin -c config.toml -r 10 -o stats_run_
```

### Run multiple experiment variations

```bash
# Experiment A
python3 -m emtorch run data/*.bin -c exp_a.toml -o exp_a_

# Experiment B
python3 -m emtorch run data/*.bin -c exp_b.toml -o exp_b_
```

### Test configuration before full run

```bash
# Test with one file
python3 -m emtorch run data/test_single.bin -c config.toml

# Then run full suite
python3 -m emtorch run data/*.bin -c config.toml -o results_
```

---

For detailed information on creating configurations, see [Configuration Guide](./configuration-guide.md).

For subtask-specific documentation, see [Subtasks Reference](./subtasks/index.md).
