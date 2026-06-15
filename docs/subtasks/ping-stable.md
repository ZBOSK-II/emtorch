<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# Subtask: ping-stable

## Description
Uses ping to verify that a network endpoint is responding consistently and stably. Unlike `ping-alive` which only checks for any response, this subtask sends a specified number of ping requests at a given interval and requires all of them to succeed, ensuring stable network connectivity.

## Use Cases
- Validating stable network connectivity before starting experiments
- Post-experiment verification that the device remained responsive throughout the test
- Testing network reliability after configuration changes
- Ensuring a device is fully booted and stable, not just momentarily reachable
- Quality checks for wireless or flaky network links

## Configuration Arguments

### Required Arguments
- **host** (string): IP address or hostname of the target to check.
- **count** (int): Number of ping requests to send.
- **interval** (int): Interval in milliseconds between successive ping requests.

### Optional Arguments
None.

## Example Configuration

```toml
[[checks]]
type = "ping-stable"
name = "verify_stable_link"

[checks.args]
host = "192.168.1.100"
count = 10
interval = 200
```

```toml
[[setups]]
type = "ping-stable"
name = "wait_for_device"

[setups.args]
host = "10.0.0.50"
count = 5
interval = 1000
```

## Result
Returns SUCCESS if all ping requests receive a response (0% packet loss). Returns FAILURE if any request is lost.

## Notes
- All specified ping requests must succeed for the subtask to return SUCCESS.
- The interval is specified in milliseconds between ping packets.
- For a quick "is it alive?" check, use `ping-alive` instead — this subtask is for sustained verification.
- Packet loss of even a single ping causes FAILURE, making this a strict stability check.
- Useful in `checks` phases after experiment actions to confirm the device is still responsive.

## See Also
- [ping-alive](./ping-alive.md) — Quick connectivity check (any response)
- [remote](./remote.md) — Execute commands on remote hosts after stable connectivity is verified
