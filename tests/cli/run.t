Experiment execution, using configuration with environment independent subtasks only.

  $ printf 'count=7 size=1\n' > a.bin
  $ printf 'count=13 size=2\n' > b.bin
  $ strip_ts() { sed -E 's/^[0-9-]+ [0-9:,]+ //' "$@"; }

Successful run - console shows progress and summary, results and log are stored with
the output prefix and the current date.

  $ emtorch run --config "$TESTDIR/experiment.toml" --output-prefix out a.bin b.bin > console.txt 2>&1
  $ strip_ts console.txt
  \[    INFO\]\(\s+root\)<-+>: Started instance \(.+\) (re)
  [    INFO](      emtorch.experiment)<------------------------>: Progress [1/2] - a.bin
  [    INFO](            emtorch.case)<------------------------>: Starting case a.bin
  [    INFO](        emtorch.subtasks)<------------------------>: Executing setups
  [    INFO](        emtorch.subtasks)<------------------------>: Finished setups
  [    INFO](        emtorch.subtasks)<------------------------>: Starting monitoring
  [    INFO](        emtorch.subtasks)<------------------------>: Executing actions
  [    INFO](        emtorch.subtasks)<------------------------>: Finished actions
  [    INFO](        emtorch.subtasks)<------------------------>: Finished monitoring
  [    INFO](        emtorch.subtasks)<------------------------>: Executing checks
  [    INFO](        emtorch.subtasks)<------------------------>: Finished checks
  [    INFO](            emtorch.case)<------------------------>: Finished case a.bin
  [    INFO](      emtorch.experiment)<------------------------>: Progress [2/2] - b.bin
  [    INFO](            emtorch.case)<------------------------>: Starting case b.bin
  [    INFO](        emtorch.subtasks)<------------------------>: Executing setups
  [    INFO](        emtorch.subtasks)<------------------------>: Finished setups
  [    INFO](        emtorch.subtasks)<------------------------>: Starting monitoring
  [    INFO](        emtorch.subtasks)<------------------------>: Executing actions
  [    INFO](        emtorch.subtasks)<------------------------>: Finished actions
  [    INFO](        emtorch.subtasks)<------------------------>: Finished monitoring
  [    INFO](        emtorch.subtasks)<------------------------>: Executing checks
  [    INFO](        emtorch.subtasks)<------------------------>: Finished checks
  [    INFO](            emtorch.case)<------------------------>: Finished case b.bin
  [    INFO](                    root)<------------------------>: Results:
  setups.setup:
  \tsuccess: 2 (esc)
  \tfailure: 0 (esc)
  \terror: 0 (esc)
  \ttimeout: 0 (esc)
  monitoring.count:
  \tsuccess: 2 (esc)
  \tfailure: 0 (esc)
  \terror: 0 (esc)
  \ttimeout: 0 (esc)
  monitoring.size:
  \tsuccess: 2 (esc)
  \tfailure: 0 (esc)
  \terror: 0 (esc)
  \ttimeout: 0 (esc)
  actions.process:
  \tsuccess: 2 (esc)
  \tfailure: 0 (esc)
  \terror: 0 (esc)
  \ttimeout: 0 (esc)
  checks.report:
  \tsuccess: 2 (esc)
  \tfailure: 0 (esc)
  \terror: 0 (esc)
  \ttimeout: 0 (esc)
  
  Processed cases: 2
  Failed subtasks: 0
  

  $ ls
  a.bin
  b.bin
  console.txt
  out-????????-??????.json (glob)
  out-????????-??????.log (glob)
  report.txt

  $ cat report.txt
  a.bin done
  b.bin done

Subtask output is stored in the log only.

  $ grep -h STDOUT out-*.log | strip_ts
  [    INFO](        emtorch.subtasks)<            setups.setup>: STDOUT - b'SETUP a.bin hello'
  [    INFO](        emtorch.subtasks)<         actions.process>: STDOUT - b'count=7 size=1'
  [    INFO](        emtorch.subtasks)<            setups.setup>: STDOUT - b'SETUP b.bin hello'
  [    INFO](        emtorch.subtasks)<         actions.process>: STDOUT - b'count=13 size=2'

Mapping and configuration override - exit code is the number of failed subtasks.

  $ emtorch run --config "$TESTDIR/experiment.toml" --output-prefix override --map GREETING=hi --override 'actions[0].args.cmd=exit 3' a.bin > /dev/null 2>&1
  [3]

  $ grep -h STDOUT override-*.log | strip_ts
  [    INFO](        emtorch.subtasks)<            setups.setup>: STDOUT - b'SETUP a.bin hi'

Repeating cases.

  $ emtorch run --config "$TESTDIR/experiment.toml" --output-prefix aabb --repeats 2 a.bin b.bin 2>&1 | grep Progress | strip_ts
  [    INFO](      emtorch.experiment)<------------------------>: Progress [1/4] - a.bin[1]
  [    INFO](      emtorch.experiment)<------------------------>: Progress [2/4] - a.bin[2]
  [    INFO](      emtorch.experiment)<------------------------>: Progress [3/4] - b.bin[1]
  [    INFO](      emtorch.experiment)<------------------------>: Progress [4/4] - b.bin[2]

  $ emtorch run --config "$TESTDIR/experiment.toml" --output-prefix abab --repeats 2 --repeat-mode abab a.bin b.bin 2>&1 | grep Progress | strip_ts
  [    INFO](      emtorch.experiment)<------------------------>: Progress [1/4] - a.bin[1]
  [    INFO](      emtorch.experiment)<------------------------>: Progress [2/4] - b.bin[1]
  [    INFO](      emtorch.experiment)<------------------------>: Progress [3/4] - a.bin[2]
  [    INFO](      emtorch.experiment)<------------------------>: Progress [4/4] - b.bin[2]

Invalid arguments.

  $ emtorch run --config "$TESTDIR/experiment.toml" missing.bin
  usage: emtorch run [-h] [--output-prefix OUTPUT_PREFIX] [--config CONFIG]
                     [--repeats REPEATS] [--repeat-mode {aabb,abab}]
                     [--map KEY=VALUE] [--override path.to.key=value]
                     [--verbose | --no-verbose]
                     data [data ...]
  emtorch run: error: Specified path is not a file: missing.bin
  [2]

  $ emtorch run --config "$TESTDIR/experiment.toml" a.bin a.bin
  usage: emtorch run [-h] [--output-prefix OUTPUT_PREFIX] [--config CONFIG]
                     [--repeats REPEATS] [--repeat-mode {aabb,abab}]
                     [--map KEY=VALUE] [--override path.to.key=value]
                     [--verbose | --no-verbose]
                     data [data ...]
  emtorch run: error: Non-unique file names as inputs - results would be inconsistent
  [2]

  $ emtorch run --config "$TESTDIR/experiment.toml" --repeats 0 a.bin
  usage: emtorch run [-h] [--output-prefix OUTPUT_PREFIX] [--config CONFIG]
                     [--repeats REPEATS] [--repeat-mode {aabb,abab}]
                     [--map KEY=VALUE] [--override path.to.key=value]
                     [--verbose | --no-verbose]
                     data [data ...]
  emtorch run: error: --repeats must be >= 1
  [2]

  $ emtorch run --config "$TESTDIR/experiment.toml" --override invalid a.bin
  usage: emtorch run [-h] [--output-prefix OUTPUT_PREFIX] [--config CONFIG]
                     [--repeats REPEATS] [--repeat-mode {aabb,abab}]
                     [--map KEY=VALUE] [--override path.to.key=value]
                     [--verbose | --no-verbose]
                     data [data ...]
  emtorch run: error: argument --override: Expected format KEY=VALUE
  [2]

  $ emtorch run --config missing.toml a.bin
  .* Started instance \(.+\) (re)
  ERROR: [Errno 2] No such file or directory: 'missing.toml' [FileNotFoundError]
  [255]
