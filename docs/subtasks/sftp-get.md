<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# Subtask: sftp-get

## Description
Downloads a file from a remote host using SFTP (SSH File Transfer Protocol). This subtask connects to a remote machine with the provided credentials and transfers a file from the remote filesystem to a local path. Essential for collecting experiment results, logs, and data from remote devices.

## Use Cases
- Collecting experiment results and log files from remote devices
- Downloading sensor data, measurements, or captured traces
- Retrieving configuration backups from network equipment
- Gathering output files after remote command execution
- Archiving remote data to local storage for analysis

## Configuration Arguments

### Required Arguments
- **local_path** ($-string): Path on the local filesystem where the downloaded file will be saved.
- **remote_path** ($-string): Path on the remote filesystem of the file to download.
- **connection** (object): SFTP connection configuration containing:
  - **host** (string): Remote host address (IP or hostname).
  - **port** (int, default 22): SSH port number.
  - **username** (string): SSH login username.
  - **password** (string): SSH login password.

### Optional Arguments
- **timeout** (float, default 5.0): Operation timeout in seconds.

## Result
Returns SUCCESS if the file is downloaded successfully. Returns FAILURE or ERROR if the file cannot be found, the connection fails, or the transfer times out.

## Example Configuration

```toml
[[actions]]
type = "sftp-get"
name = "download_results"

[actions.args]
local_path = "/tmp/experiment_results.csv"
remote_path = "/home/pi/data/output.csv"
connection = { host = "192.168.1.100", port = 22, username = "pi", password = "raspberry" }
timeout = 10
```

```toml
[[checks]]
type = "sftp-get"
name = "get_logs"

[checks.args]
local_path = "$EMTORCH_DATA_PATH/device.log"
remote_path = "/var/log/experiment.log"
connection = { host = "10.0.0.50", username = "root", password = "admin123" }
timeout = 15
```

## Notes
- The remote host must have an SSH server running with SFTP support (typically enabled by default).
- The local directory must already exist — the subtask creates the file but not parent directories.
- If a file already exists at `local_path`, it will be overwritten.
- Template variables in path arguments are expanded before execution.
- For uploading files to remote hosts, use the complementary `sftp-put` subtask.
- Combine with `remote` subtask to first execute commands that generate output files, then download them.

## See Also
- [sftp-put](./sftp-put.md) — Upload files to remote hosts
- [remote](./remote.md) — Execute commands on remote hosts via SSH
