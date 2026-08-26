<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# Subtask: ping-alive

## Description
Uses flood ping to check whether a given network endpoint is responding. This subtask sends ICMP echo requests continuously and waits for any response within the specified timeout. It is designed for quick connectivity checks to determine if a host is reachable on the network.

## Use Cases
- Verifying that a device is powered on and network-ready before starting experiments
- Precondition checks in `setups` phases to ensure target hosts are reachable
- Quick network connectivity validation after device reboot or configuration changes
- Monitoring device availability during long-running experiments
- Testing if a service or device has come online

## Configuration Arguments

### Required Arguments
- **host** (string): IP address or hostname of the target to check.
- **timeout** (float): Maximum time in seconds to wait for any response.
- **interval** (int): Interval in milliseconds between successive ping requests.

### Optional Arguments
None.

## Result
Returns SUCCESS if at least one ping response is received within the timeout period. Returns FAILURE if no response is received.

## Example Configuration

```toml
[[setups]]
type = "ping-alive"
name = "check_device"

[setups.args]
host = "192.168.1.100"
timeout = 5.0
interval = 100
```

```toml
[[checks]]
type = "ping-alive"
name = "wait_for_reboot"

[checks.args]
host = "10.0.0.50"
timeout = 30.0
interval = 500
```

## Notes
- This subtask uses the system's `ping` command with flood mode for rapid checking.
- The interval is specified in milliseconds between ping packets.
- A single successful response is sufficient to return SUCCESS — use `ping-stable` for sustained connectivity verification.
- Requires appropriate permissions for sending ICMP packets (may need `CAP_NET_RAW` or root on some systems).
- Useful in `setups` phases to ensure the experiment environment is ready before proceeding.

## See Also
- [ping-stable](./ping-stable.md) — Verify stable, sustained network connectivity
- [remote](./remote.md) — Execute commands on remote hosts after connectivity is confirmed
