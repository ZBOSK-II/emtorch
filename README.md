Emtorch
_experiments orchestrator for embedded systems_
============================================================

When executing experiment/test on embedded environment
one often faces challenge of performing multiple tasks in
repeatable and observable manner, for example: reset board,
ensure embedded software booted, send trigger data using
selected link, monitor peripheral state to detect changes
in behaviour etc.

This is what Emtorch helps to orchestrate: it runs various
tools and scripts in specific manner, then gathers their
results for further inspections.

Installation
------------------------------------------------------------
Emtorch is available on PyPI, it is recommended to install
it in isolated environment, either by using Python `venv` or
tools like `pipx`.

``` shell
python -m venv .venv
source .venv/bin/activate
pip install emtorch
```

``` shell
pipx install emtorch
```

Usage
------------------------------------------------------------
To run experiments simply run:

``` shell
emtorch --config=experiment.json test1.bin test2.bin
```

For each specified data file steps from `experiment.json`
will be executed and gathered results stored in file named
`emtorch-CURRENTDATE.json`. Application will output logs
to the console and also store them in `.log` file next to
the `.json` results file. The prefix for output files can
be modified using `--output-prefix` command line switch.

See `default-config.json` in source directory for example
of experiment definition (this file can be safely used -
the "experiment" calls `cat` on each passed file).

To obtain complete command line switches documentation call
`emtorch --help`.


Experiment
------------------------------------------------------------
Each data file passed to the emtorch represents a single
Test Case. For each test case following experiment steps
will be performed:

 1. Setup tasks will be executed and their results stored.
 2. Monitoring tasks will be started.
 3. Case actions will be performed and their results stored.
 4. Monitoring tasks will finish, their results stored.
 5. Check tasks will be executed and their results stored.
 6. Go to 1 for next Test Case.

Configuration
------------------------------------------------------------
Experiment configuration is stored in JSON format.

See chapters below for list of all types of injectors, tasks
and monitors (with arguments).

Below is the `default-config.json` with comments:
``` json-with-comments
{
  "case": {                    // for each case
    "setups": [                // list of setups
      {
        "name": "setup",       // name used in results
        "type": "subprocess",  // type of setup tasks
        "args": {              // arguments for given type
          "cmd": [
            "echo",
            "SETUP"
          ],
          "finish": {
            "timeout": 0.5,
            "signal": "NONE"
          },
          "shell": false
        }
      },
      {                        // second setup
        "name": "ping",
        "type": "ping_alive",
        "args": {
          "host": "127.0.0.1",
          "timeout": 10,
          "interval": 1
        }
      }
    ],
    "monitoring": [],          // monitoring tasks
    "actions": [               // case actions (core of the experiment)
      {
        "name": "test",
        "type": "subprocess",
        "args": {
          "cmd": [
            "cat $EMTORCH_DATA_PATH"
          ],
          "shell": true,
          "finish": {
            "timeout": 0.5,
            "signal": "NONE"
          }
        }
      }
    ],
    "checks": [                // list of checks tasks
      {                        // same as setups
        "name": "ping",
        "type": "ping_stable",
        "args": {
          "host": "127.0.0.1",
          "count": 2,
          "interval": 1
        }
      },
      {
        "name": "teardown",
        "type": "subprocess",
        "args": {
          "cmd": [
            "echo",
            "TEARDOWN"
          ],
          "finish": {
            "timeout": 0.5,
            "signal": "NONE"
          },
          "shell": false
        }
      }
    ],
    "delays": {
      "between_cases": 0.2,    // delay between Test Cases
      "before_actions": 1      // delay after all setups
    }
  }
}
```

SubTasks
------------------------------------------------------------
Sub Tasks are tasks that for each case can be executed as
setups, checks, actions or monitors.

_Note_: failure of "setup" _does not_ interrupt the test
case execution - it is logged and stored in results, next
steps are still executed, to be analyzed later.

Monitors are tasks that their execution is started after
setups, then they are active during the actions and
finish before checks.

All Sub Tasks instances has to be named using key `name`.
Their type is selected using key `type`, with type-specific
arguments passed in key `args`. Arguments with default
values can be omitted from config.

Available task types:
 * `subprocess` - execute script and capture its exit code.
   Arguments:
    - `cmd` - (list of $-strings) command to be executed
    - `shell` - (boolean) true when shell should be used to
      interpret the command
    - `finish` - configuration of finishing the task:
      - `signal` - (string) signal name to be sent to the
        task, useful when in monitoring (can be `NONE`)
      - `timeout` - (float) time to wait for command to
        finish (starts after signal is sent)
 * `ping_stable` - pings a target number of times, expects
   all pings to reply.
   Arguments:
     - `host` - (string) host to be checked
     - `count` - (integer) number of pings to sent
     - `interval` - (integer) interval between pings
 * `ping_alive` - pings a target and expects first response
   Arguments:
     - `host` - (string) host to be checked
     - `timeout` - (float) timeout to wait for response
     - `interval` - (integer) interval between pings
 * `remote` - executes command over SSH and captures its
   exit code. Host key must be in 'known hosts' file.
   Arguments:
     - `connection` - dictionary containing:
       - `host` - (string) SSH host name
       - `port`- (integer) SSH port (default: 22)
       - `username` - (string) user name
       - `password` - (string) user's password
     - `command` - (string) command to be executed
     - `start_key` - (string) string expected in the output
       of the executed command for the command to be
       considered "started successfully"
     - `start_timeout` - (float) timeout for the start of
       the command
    - `finish` - configuration of finishing the task:
      - `signal` - (string) signal name to be sent to the
        task, useful when in monitoring (can be `NONE`)
      - `timeout` - (float) time to wait for command to
        finish (starts after signal is sent)
 * `sftp-upload` - uploads file using SFTP
   Arguments:
     - `connection` - dictionary containing:
       - `host` - (string) SSH host name
       - `port`- (integer) SSH port (default: 22)
       - `username` - (string) user name
       - `password` - (string) user's password
     - `local_path` - ($-string) path to a local file to
       upload
     - `remote_path` - ($-string) path to a remote file
       (target)
     - `timeout` - (float) number of seconds to complete
       the transfer
 * `sftp-downnload` - downloads file using SFTP
   Arguments:
     - `connection` - dictionary containing:
       - `host` - (string) SSH host name
       - `port`- (integer) SSH port (default: 22)
       - `username` - (string) user name
       - `password` - (string) user's password
     - `remote_path` - ($-string) path to a remote file to
        download
     - `local_path` - ($-string) path to a local file to
        store (target)
     - `timeout` - (float) number of seconds to complete
       the transfer
 * `coap_monitor` - listens for CoAP responses
   Arguments:
    - `target` - dictionary containing `host` and `port` of
      the target
    - `response_timeout` - (float) timeout to wait for CoAP
      response after sending any data
      (useful only when used as Injector)
    - `observation_timeout` - (float) additional time for
      detecting any unexpected messages when monitoring
      finishes
  * `coap_send` - sends data provided in argument to the
    program call as CoAP message and checks system response.
    Arguments:
      - `monitor` - (string) name of the `coap_monitor`
        instance used to send the message.
  * `logger-int-matcher` - scans logs for a pattern and
    stores it as integer value (monitoring subtask only).
    Arguments:
      - `value` - (string) name for the value to store
      - `pattern` - (string) regular expression containing named
         group `value` used to extract the value
         (e.g. `prefix=(?P<value>\\d+)`)
      - `subtask` - (string) subtask which logs should be
         scanned
  * `logger-float-matcher` - scans logs for a pattern and
    stores it as real value (monitoring subtask only).
    Arguments:
      - `value` - (string) name for the value to store
      - `pattern` - (string) regular expression containing named
         group `value` used to extract the value
         (e.g. `prefix=(?P<value>\\d+.\\d+)`)
      - `subtask` - (string) subtask which logs should be
         scanned
    Arguments:
      - `path` - ($-string) path to file to write to
      - `append` - (boolean) if true appends to an existing
         file, overwrites otherwise (default: false)
      - `lines` - ($-string array) lines to write to a file
      - `encoding` - (string) file encoding (default: utf-8)
      - `timeout` - (float) time required to write to the
         file in seconds (default: 5)
  * `file-write` - writes to a file
    Arguments:
      - `path` - ($-string) path to the file to save
      - `append` - (boolean) if true appends to file,
        overwrites otherwise (default: false)
      - `lines` - (list of $-strings) lines to write to the
        target file
      - `encoding` - (string) encoding of the file (default:
         utf-8)

$-strings in arguments allow for interpolation of `$KEYWORD`
inside passed string. Both `$KEYWORD` and `${KEYWORD}` are
supported. Use `$$` to escape `$` character.

Keywords available in $-strings:
 * `EMTORCH_CASE_ID` - unique identifier of the current case
 * `EMTORCH_DATA_PATH` - path to the case data
 * `EMTORCH_DATA_FILENAME` - file name of the case data
