Listing available subtasks.

  $ emtorch subtasks
  Known subtasks:
  
  \tcoap-monitor (esc)
  \tcoap-send (esc)
  \techo (esc)
  \texec (esc)
  \tfile-write (esc)
  \tlogger-float-matcher (esc)
  \tlogger-int-matcher (esc)
  \tping-alive (esc)
  \tping-stable (esc)
  \tremote (esc)
  \tsftp-get (esc)
  \tsftp-put (esc)
  \tshell (esc)
  
  Type 'emtorch subtask <NAME>' to get help on the given subtask's arguments

Subtask documentation.

  $ emtorch subtask echo
  
  echo
  ====
  
  Writes the provided message to the log.
  
  
  Arguments
  ---------
    message                  - ($-string) message to write to log

  $ emtorch subtask shell
  
  shell
  =====
  
  Executes system shell command.
  
  
  Arguments
  ---------
    cmd                      - ($-string) shell command to be executed
    timeout                  - (float) execution timeout (default: 1.0)
    signal                   - (string) signal name to be sent to the program at the end of monitoring (default: None)
    ready_pattern            - (regex) regular expression; the subtask is considered ready (next monitoring subtask is started) once an output line matches it, instead of right after start (default: None)
    ready_timeout            - (float) time to wait for `ready_pattern` to match, in seconds; when exceeded the program is killed and the subtask results in `not_ready`; no limit when not set (default: None)

Missing or unknown subtask name.

  $ emtorch subtask
  usage: emtorch subtask [-h] name
  emtorch subtask: error: the following arguments are required: name
  [2]

  $ emtorch subtask unknown
  ERROR: Unknown subtask type 'unknown' [UnknownSubTaskTypeError]
  [255]
