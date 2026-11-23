Reaction to subtask failures, configured with `on_failure`.

  $ touch a.bin b.bin c.bin
  $ run() {
  >   prefix=$1; shift
  >   emtorch run --config "$TESTDIR/on-failure.toml" --output-prefix "$prefix" "$@" > /dev/null 2>&1
  >   grep -hE 'Progress|Starting [a-z]+\.|Skipping|failed with|ended early' "$prefix"-*.log | sed -E 's/^[0-9-]+ [0-9:,]+ //'
  > }

By default the experiment proceeds.

  $ run proceed a.bin
  [    INFO](      emtorch.experiment)<------------------------>: Progress [1/1] - a.bin
  [    INFO](        emtorch.subtasks)<            setups.setup>: Starting setups.setup
  [    INFO](        emtorch.subtasks)<         actions.failing>: Starting actions.failing
  [    INFO](        emtorch.subtasks)<            actions.next>: Starting actions.next
  [    INFO](        emtorch.subtasks)<             checks.once>: Starting checks.once

The rest of the phase is skipped, following phases are executed.

  $ run phase --override actions.failing.on_failure=skip-phase a.bin
  [    INFO](      emtorch.experiment)<------------------------>: Progress [1/1] - a.bin
  [    INFO](        emtorch.subtasks)<            setups.setup>: Starting setups.setup
  [    INFO](        emtorch.subtasks)<         actions.failing>: Starting actions.failing
  [ WARNING](        emtorch.subtasks)<         actions.failing>: actions.failing failed with 'failure', skip-phase
  [    INFO](        emtorch.subtasks)<            actions.next>: Skipping actions.next due to an earlier failure
  [    INFO](        emtorch.subtasks)<             checks.once>: Starting checks.once

The rest of the case is skipped, without consuming `when = "once"` of skipped subtasks.

  $ run case --override actions.failing.on_failure=skip-case \
  >   --override 'actions.failing.cmd=test $EMTORCH_DATA_FILENAME != a.bin' a.bin b.bin
  [    INFO](      emtorch.experiment)<------------------------>: Progress [1/2] - a.bin
  [    INFO](        emtorch.subtasks)<            setups.setup>: Starting setups.setup
  [    INFO](        emtorch.subtasks)<         actions.failing>: Starting actions.failing
  [ WARNING](        emtorch.subtasks)<         actions.failing>: actions.failing failed with 'failure', skip-case
  [    INFO](        emtorch.subtasks)<            actions.next>: Skipping actions.next due to an earlier failure
  [    INFO](        emtorch.subtasks)<             checks.once>: Skipping checks.once due to an earlier failure
  [    INFO](      emtorch.experiment)<------------------------>: Progress [2/2] - b.bin
  [    INFO](        emtorch.subtasks)<            setups.setup>: Starting setups.setup
  [    INFO](        emtorch.subtasks)<         actions.failing>: Starting actions.failing
  [    INFO](        emtorch.subtasks)<            actions.next>: Starting actions.next
  [    INFO](        emtorch.subtasks)<             checks.once>: Starting checks.once

No more cases are executed.

  $ run end --override actions.failing.on_failure=end-experiment a.bin b.bin c.bin
  [    INFO](      emtorch.experiment)<------------------------>: Progress [1/3] - a.bin
  [    INFO](        emtorch.subtasks)<            setups.setup>: Starting setups.setup
  [    INFO](        emtorch.subtasks)<         actions.failing>: Starting actions.failing
  [ WARNING](        emtorch.subtasks)<         actions.failing>: actions.failing failed with 'failure', end-experiment
  [    INFO](        emtorch.subtasks)<            actions.next>: Skipping actions.next due to an earlier failure
  [    INFO](        emtorch.subtasks)<             checks.once>: Skipping checks.once due to an earlier failure
  [   ERROR](      emtorch.experiment)<------------------------>: Experiment ended early, 2 case(s) not executed

Successful subtasks do not trigger the reaction.

  $ run success --override actions.failing.cmd=true --override actions.failing.on_failure=end-experiment a.bin b.bin
  [    INFO](      emtorch.experiment)<------------------------>: Progress [1/2] - a.bin
  [    INFO](        emtorch.subtasks)<            setups.setup>: Starting setups.setup
  [    INFO](        emtorch.subtasks)<         actions.failing>: Starting actions.failing
  [    INFO](        emtorch.subtasks)<            actions.next>: Starting actions.next
  [    INFO](        emtorch.subtasks)<             checks.once>: Starting checks.once
  [    INFO](      emtorch.experiment)<------------------------>: Progress [2/2] - b.bin
  [    INFO](        emtorch.subtasks)<            setups.setup>: Starting setups.setup
  [    INFO](        emtorch.subtasks)<         actions.failing>: Starting actions.failing
  [    INFO](        emtorch.subtasks)<            actions.next>: Starting actions.next
  [    INFO](        emtorch.subtasks)<             checks.once>: Starting checks.once
  [    INFO](        emtorch.subtasks)<             checks.once>: Skipping checks.once

Invalid value.

  $ emtorch config-check --config "$TESTDIR/on-failure.toml" --override actions.failing.on_failure=retry | sed "s|$TESTDIR/||"
  on-failure.toml: 1 error(s) found
    actions.failing.on_failure: Input should be 'proceed', 'skip_phase', 'skip_case' or 'end_experiment'

A monitor failing during startup stops following monitors and actions, while already
running monitors are not interrupted.

  $ emtorch run --config "$TESTDIR/on-failure-monitoring.toml" --output-prefix monitoring a.bin > /dev/null 2>&1
  [1]
  $ grep -hE 'Starting [a-z]+\.|Skipping|failed with|STDOUT' monitoring-*.log | sed -E 's/^[0-9-]+ [0-9:,]+ //'
  [    INFO](        emtorch.subtasks)<      monitoring.running>: Starting monitoring.running
  [    INFO](        emtorch.subtasks)<         monitoring.dead>: Starting monitoring.dead
  [ WARNING](        emtorch.subtasks)<         monitoring.dead>: monitoring.dead failed with 'failure', skip-case
  [    INFO](        emtorch.subtasks)<        monitoring.later>: Skipping monitoring.later due to an earlier failure
  [    INFO](        emtorch.subtasks)<          actions.action>: Skipping actions.action due to an earlier failure
  [    INFO](        emtorch.subtasks)<      monitoring.running>: STDOUT - b'still running'
