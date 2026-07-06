Emtorch
_experiments orchestrator for embedded systems_
============================================================

When executing experiments or tests on embedded environments,
one often faces the challenge of performing multiple tasks in a
repeatable and observable manner. For example: reset board,
ensure embedded software booted, send trigger data using a
selected link, monitor peripheral state to detect changes in
behaviour, etc.

This is what **emtorch** helps to orchestrate: it runs various
tools and scripts in a specific manner, then gathers their
results for further inspection.

**emtorch** (previously known as **emfuzzer**, renamed in v2.0.0)
is developed at the Warsaw University of Technology and licensed
under the MIT License.

Installation
------------------------------------------------------------
Emtorch requires **Python 3.14 or later** and is available on PyPI.
It is recommended to install it in an isolated environment using
Python `venv`, `pipx`, or `uv`.

**Using venv:**
``` shell
python -m venv .venv
source .venv/bin/activate
pip install emtorch
```

**Using pipx:**
``` shell
pipx install emtorch
```

**Using uv:**
``` shell
uv tool install emtorch
```

Usage
------------------------------------------------------------
To run experiments, use the `run` subcommand:

``` shell
emtorch run --config=experiment.toml test1.bin test2.bin
```

For each specified data file, steps from `experiment.toml`
will be executed and gathered results stored in a file named
`emtorch-CURRENTDATE.json`. Application logs are output to
the console and also stored in a `.log` file next to the
`.json` results file. The prefix for output files can be
modified using the `--output-prefix` option.

See `default-config.toml` in the source directory for a
comprehensive example of experiment definition (this file can
be safely used - the experiment calls `cat` on each passed
file).

To obtain complete command line documentation, call:
``` shell
emtorch --help
emtorch run --help
```

Additional options include:
- `--repeats N` - repeat each test case N times
- `--repeat-mode {aabb,abab}` - control repetition order

Quick Start
------------------------------------------------------------
Create a simple test data file:
``` shell
echo "Hello from test case" > test_data.txt
```

Create a minimal configuration file (`config.toml`):
``` toml
[delays]
between_cases = 0.2
before_actions = 0.0

[[actions]]
type = "shell"
name = "read_data"

[actions.args]
cmd = "cat $EMTORCH_DATA_PATH"
```

Run your first experiment:
``` shell
emtorch run test_data.txt --config config.toml
```

This will execute the configuration against the test data and
output results in JSON format.

For a comprehensive configuration example, see `default-config.toml`
in the repository. 

Experiment Lifecycle
------------------------------------------------------------
Each data file passed to emtorch represents a single Test Case.
For each test case, the following experiment steps are performed:

1. **Setup tasks** are executed sequentially and their results stored.
2. **Monitoring tasks** are started (run concurrently in background).
3. Delay before actions (if configured).
4. **Case actions** are performed sequentially and their results stored.
5. **Monitoring tasks** finish when actions complete, results stored.
6. **Check tasks** are executed sequentially and their results stored.
7. Delay between cases (if more test cases remain).
8. Go to step 1 for the next Test Case.

Note: Failure of setup tasks does not interrupt test case execution -
it is logged and stored in results, and subsequent steps are still
executed for later analysis.

Configuration
------------------------------------------------------------
Experiment configuration is stored in **TOML format**.

The configuration file defines four types of subtasks:
- **setups** - pre-case configuration tasks (sequential)
- **monitoring** - background observation tasks (concurrent)
- **actions** - main experiment operations (sequential)
- **checks** - post-case verification tasks (sequential)

Example configuration structure:
``` toml
[delays]
between_cases = 0.2
before_actions = 1.0

[[setups]]
type = "ping-alive"
name = "check_host"

[setups.args]
host = "192.168.1.100"
timeout = 10
interval = 1

[[actions]]
type = "shell"
name = "run_test"

[actions.delays]
before = 0.5
after = 0.1

[actions.args]
cmd = "cat $EMTORCH_DATA_PATH"

[[checks]]
type = "ping-stable"
name = "verify_host"

[checks.args]
host = "192.168.1.100"
count = 3
interval = 1
```

Template Variables
------------------------------------------------------------
Configuration values support **$-string interpolation** using
template variables. Both `$KEYWORD` and `${KEYWORD}` syntax
are supported. Use `$$` to escape the `$` character.

Available template variables:
- `$EMTORCH_CASE_ID` - unique identifier of the current case
- `$EMTORCH_DATA_PATH` - full path to the case data file
- `$EMTORCH_DATA_FILENAME` - filename only of the case data

Additional variables can be introduced using `--map` argument.

Example usage:
``` toml
[[actions]]
type = "shell"
name = "process"

[actions.args]
cmd = "process_data --input $EMTORCH_DATA_PATH --id $EMTORCH_CASE_ID"
```

SubTasks
------------------------------------------------------------
Subtasks are the building blocks of experiments. Each subtask
has a type, name, and type-specific arguments.

**Available subtask types:**

| Subtask | Purpose |
|---------|---------|
| `echo` | Print messages to logs |
| `exec` | Execute programs with arguments |
| `shell` | Execute shell commands |
| `remote` | Execute commands on remote hosts via SSH |
| `ping-alive` | Check network connectivity (flood ping until first response) |
| `ping-stable` | Verify stable network response (all pings must succeed) |
| `sftp-get` | Download files from remote hosts |
| `sftp-put` | Upload files to remote hosts |
| `file-write` | Write content to local files |
| `logger-int-matcher` | Extract integer values from logs using regex |
| `logger-float-matcher` | Extract float values from logs using regex |
| `coap-monitor` | Monitor CoAP protocol messages |
| `coap-send` | Send CoAP protocol messages |

**For detailed subtask documentation:**
- Run `emtorch subtasks` to list all available subtasks
- Run `emtorch subtask <NAME>` to see documentation for a specific subtask


Results
------------------------------------------------------------

Results include:
  * log file containing all messages captured during the experiment
  * JSON file with experiment summary

JSON file has following items:
 * info - general experiment information, including used emtorch version, configuration etc.
 * subtask - information on all subtasks, their names and possible results
 * values - list of values that can be captured during the experiment
 * cases - results of each tests case, including results of all subtasks and captured values.


Exporting values
------------------------------------------------------------

Results can contain "values" captured during the experiment (e.g. by using sub-task
`logger-int-matcher` ). To extract those into more portable format use `values` command.

For example:

``` shell
$ emtorch values emtorch-20260706-114255.json --format=text --include .\*abc
+------------+-----------+-------------+
|    Case    | Iteration | counter-abc |
+------------+-----------+-------------+
| data-1.elf |     1     |   6413174   |
| data-1.elf |     2     |   6413134   |
| data-1.elf |     3     |   6413193   |
| data-1.elf |     4     |   6413100   |
| data-1.elf |     5     |   6413099   |
+------------+-----------+-------------+
```

Project Information
------------------------------------------------------------
- **License:** MIT License
- **Institution:** Warsaw University of Technology
- **GitHub:** https://github.com/ZBOSK-II/emtorch
- **Changelog:** https://github.com/ZBOSK-II/emtorch/blob/master/CHANGELOG.md
- **Previous name:** emfuzzer (renamed in v2.0.0)
