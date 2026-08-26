<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# Getting Started

Learn how to install emtorch and run your first experiment.

## Installation

### Requirements

- **Python**: 3.14 or later (check with `python3 --version`)
- **pip**: Python package manager

### Install as a Package

The simplest way to get started:

```bash
pip install emtorch
```

Then run emtorch as a module:

```bash
python3 -m emtorch --version
```

### Install from Source (Development)

If you want to modify emtorch or develop custom subtasks:

```bash
git clone https://github.com/ZBOSK-II/emtorch.git
cd emtorch
pip install poetry
poetry install
```

Then run using:

```bash
python3 -m emtorch --version
```

## Your First Experiment

Let's create and run a simple experiment that reads data from a test file.

### Step 1: Create Test Data

Create a simple test data file:

```bash
mkdir -p test_data
echo "Hello from case 1" > test_data/input_1.txt
echo "Hello from case 2" > test_data/input_2.txt
```

### Step 2: Create a Configuration File

Create a file named `simple-config.toml` with a basic experiment configuration:

```toml
# Delays between operations
[delays]
between_cases = 0.1
before_actions = 0.5

# Setups: prepare the environment
[[setups]]
type = "echo"
name = "starting"

[setups.args]
message = "Starting experiment for case $EMTORCH_CASE_ID"

# Actions: main experiment
[[actions]]
type = "shell"
name = "read_input"

[actions.args]
cmd = "cat $EMTORCH_DATA_PATH"

# Checks: verification
[[checks]]
type = "echo"
name = "finished"

[checks.args]
message = "Case $EMTORCH_CASE_ID completed"
```

### Step 3: Run the Experiment

Execute the experiment against your test data:

```bash
python3 -m emtorch run test_data/input_*.txt -c simple-config.toml -o results_
```

This will:
1. Create 2 cases (one for each input file)
2. For each case:
   - Print "Starting experiment..." (setup)
   - Read and print the input file (action)
   - Print "Case X completed" (check)
3. Generate output files with prefix `results_`

### Step 4: View Results

Check the output files:

```bash
ls -la results_*
cat results_0.json
```

You'll see structured JSON output with:
- Case information (ID, input file)
- Subtask results for each phase
- Execution timestamps

## Understanding the Output

A typical result file looks like:

```json
{
  "case_id": "0",
  "data_path": "test_data/input_1.txt",
  "data_filename": "input_1.txt",
  "results": {
    "setups": {
      "starting": {
        "status": "SUCCESS",
        "log": "Starting experiment for case 0\n"
      }
    },
    "monitoring": {},
    "actions": {
      "read_input": {
        "status": "SUCCESS",
        "log": "Hello from case 1\n"
      }
    },
    "checks": {
      "finished": {
        "status": "SUCCESS",
        "log": "Case 0 completed\n"
      }
    }
  }
}
```

## Using Template Variables

emtorch supports template variables in your configuration that are replaced at runtime:

| Variable | Value | Example |
|----------|-------|---------|
| `$EMTORCH_CASE_ID` | Numeric case identifier (0, 1, 2, ...) | `"Case $EMTORCH_CASE_ID started"` |
| `$EMTORCH_DATA_PATH` | Full path to the data file | `"cat $EMTORCH_DATA_PATH"` |
| `$EMTORCH_DATA_FILENAME` | Just the filename (no path) | `"Processing $EMTORCH_DATA_FILENAME"` |

## Next Steps

Now that you understand the basics, explore:

1. **[Core Concepts](./core-concepts.md)** — Understand experiments, cases, and phases in detail
2. **[Configuration Guide](./configuration-guide.md)** — Learn advanced configuration options
3. **[Subtasks Reference](./subtasks/index.md)** — Explore all available subtasks
4. **[Examples & Tutorials](./examples/index.md)** — See practical examples for different use cases

## Common Commands

### See all available subtasks

```bash
python3 -m emtorch subtasks
```

### Get help for a specific subtask

```bash
python3 -m emtorch subtask shell
```

### Run with multiple data files

```bash
python3 -m emtorch run data1.bin data2.bin data3.bin -c config.toml
```

### Run with output prefix and repeats

```bash
python3 -m emtorch run test_data/* -c config.toml -o results_ -r 2
```

This runs each case twice (2 repeats).

### See version

```bash
python3 -m emtorch --version
```

## Troubleshooting

### Python version error

If you see "Python 3.14 or later required":

```bash
python3.14 -m emtorch --version
```

Or check your Python version:

```bash
python3 --version
```

### Configuration file not found

Make sure the TOML file path is correct:

```bash
python3 -m emtorch run data.txt -c ./path/to/config.toml
```

### Data files not found

Use absolute paths or verify the files exist:

```bash
ls -la test_data/input_*.txt
python3 -m emtorch run $(pwd)/test_data/input_*.txt -c config.toml
```

For more troubleshooting tips, see the [Troubleshooting](./troubleshooting.md) guide.
