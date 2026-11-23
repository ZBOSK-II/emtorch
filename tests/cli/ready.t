Readiness of monitoring subtasks, configured with `ready_pattern` and `ready_timeout`.

  $ touch a.bin
  $ run() {
  >   prefix=$1; shift
  >   emtorch run --config "$TESTDIR/ready.toml" --output-prefix "$prefix" "$@" > /dev/null 2>&1
  > }
  $ log() { grep -hE "$2" "$1"-*.log | sed -E 's/^[0-9-]+ [0-9:,]+ //'; }

The next monitor is started only after an output line matches the pattern.

  $ run delayed a.bin
  $ log delayed 'monitoring\.(shell|next)>: (STDOUT|Ready|Starting monitoring)'
  [    INFO](        emtorch.subtasks)<        monitoring.shell>: Starting monitoring.shell
  [    INFO](        emtorch.subtasks)<        monitoring.shell>: STDOUT - b'start'
  [    INFO](        emtorch.subtasks)<        monitoring.shell>: STDOUT - b'ready-now'
  [    INFO](        emtorch.subtasks)<        monitoring.shell>: Ready monitoring.shell
  [    INFO](        emtorch.subtasks)<         monitoring.next>: Starting monitoring.next

A ready line printed right before the program exits is still matched.

  $ run exit --override 'monitoring.shell.cmd=echo ready-now' --repeats 20 a.bin
  $ log exit 'Ready monitoring.shell' | wc -l
  20
  $ grep -c 'without becoming ready' exit-*.log
  0
  [1]

When the pattern does not match in time, the program is killed, the subtask results
in `not_ready` and the next monitor is started.

  $ run timeout --override 'monitoring.shell.cmd=echo started; sleep 10; echo done' \
  >   --override monitoring.shell.ready_pattern=never --override monitoring.shell.ready_timeout=0.1 a.bin
  [1]
  $ log timeout 'monitoring\.(shell|next)>: (STDOUT|Ready|Starting monitoring)'
  [    INFO](        emtorch.subtasks)<        monitoring.shell>: Starting monitoring.shell
  [    INFO](        emtorch.subtasks)<        monitoring.shell>: STDOUT - b'started'
  [    INFO](        emtorch.subtasks)<         monitoring.next>: Starting monitoring.next
  $ grep -h '"monitoring.shell": ' timeout-*.json
          "monitoring.shell": "not_ready",

Children of the killed program are stopped as well.

  $ run children --override 'monitoring.shell.cmd=(sleep 0.5; touch marker) & sleep 10' \
  >   --override monitoring.shell.ready_pattern=never --override monitoring.shell.ready_timeout=0.1 a.bin
  [1]
  $ sleep 0.8
  $ test -e marker
  [1]

Errors while reading the program output are not swallowed.

  $ emtorch run --config "$TESTDIR/ready.toml" --output-prefix overflow \
  >   --override "monitoring.shell.cmd=head -c 200000 /dev/zero | tr '\\\\0' x" \
  >   --override monitoring.shell.ready_pattern=never a.bin 2>&1 | grep ERROR
  ERROR: unhandled errors in a TaskGroup (1 sub-exception) [ExceptionGroup]
