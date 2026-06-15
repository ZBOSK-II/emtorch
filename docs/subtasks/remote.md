<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# Subtask: remote

## Description
Executes a command on a remote machine via SSH connection. This subtask connects to a remote host using the provided credentials and runs the specified command, capturing its output. Essential for interacting with embedded devices, remote servers, or target hardware in IoT experimentation scenarios.

## Use Cases
- Running commands on remote embedded devices (Raspberry Pi, ESP-based systems, etc.)
- Controlling testbed nodes in distributed experiments
- Executing setup or teardown procedures on remote servers
- Collecting data from remote measurement equipment
- Deploying and configuring software on remote hosts

## Configuration Arguments

### Required Arguments
- **connection** (object): SSH connection configuration containing:
  - **host** (string): Remote host address (IP or hostname).
  - **port** (int, default 22): SSH port number.
  - **username** (string): SSH login username.
  - **password** (string): SSH login password.
- **cmd** ($-string): Command to execute on the remote host.

### Optional Arguments
- **timeout** (float, default 5.0): Operation timeout in seconds.
- **signal** (string, optional): Signal name to send to the remote process if timeout occurs.

## Result
Returns SUCCESS if the remote command exits with code 0, FAILURE if non-zero, ERROR on connection issues or unexpected errors, TIMEOUT if the command exceeds the specified timeout.

## Example Configuration

```toml
[[actions]]
type = "remote"
name = "collect_remote_data"

[actions.args]
connection = { host = "192.168.1.100", port = 22, username = "pi", password = "raspberry" }
cmd = "cat /sys/class/thermal/thermal_zone0/temp"
timeout = 10
```

```toml
[[setups]]
type = "remote"
name = "reboot_device"

[setups.args]
connection = { host = "10.0.0.50", username = "root", password = "rootpass" }
cmd = "reboot"
timeout = 30
```

## Notes
- SSH connection is established for each execution; credentials must be provided in the configuration.
- Password-based authentication is supported — for frequent use, consider key-based authentication for better security.
- The remote host must be reachable over the network and have an SSH server running.
- Template variables in the command string are expanded before execution.
- Default timeout is 5 seconds, which is longer than local subtasks to account for network latency.
- For file transfers to/from remote hosts, use the `sftp-get` and `sftp-put` subtasks.

## See Also
- [sftp-get](./sftp-get.md) — Download files from remote hosts
- [sftp-put](./sftp-put.md) — Upload files to remote hosts
- [ping-alive](./ping-alive.md) — Test connectivity before running remote commands
- [shell](./shell.md) — Run commands locally
