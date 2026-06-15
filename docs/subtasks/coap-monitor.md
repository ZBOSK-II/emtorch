<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# Subtask: coap-monitor

## Description
Opens a UDP socket to monitor CoAP (Constrained Application Protocol) messages from a device. This subtask listens for incoming CoAP messages at a specified UDP address for a configured observation period. It is used to capture unsolicited CoAP messages such as notifications, sensor readings, or resource observations from IoT devices.

## Use Cases
- Monitoring CoAP resource observations from IoT sensors
- Capturing asynchronous notifications from constrained devices
- Receiving CoAP POST requests from devices sending data
- Observing device behavior over time in IoT experiments
- Collecting telemetry data from CoAP-enabled devices

## Configuration Arguments

### Required Arguments
- **address** (NetworkAddress): UDP address in the format `host:port` to listen on for CoAP messages (e.g., `0.0.0.0:5683`).
- **observation_timeout** (float): Duration in seconds to monitor for incoming messages.

### Optional Arguments
None.

## Result
Returns SUCCESS if any CoAP messages are received during the observation period. Returns FAILURE if no messages are received within the timeout.

## Example Configuration

```toml
[[monitoring]]
type = "coap-monitor"
name = "listen_sensor"

[monitoring.args]
address = "0.0.0.0:5683"
observation_timeout = 30.0
```

```toml
[[actions]]
type = "coap-monitor"
name = "capture_observations"

[actions.args]
address = "192.168.1.100:5683"
observation_timeout = 60.0
```

## Notes
- The monitor listens for incoming CoAP messages on the specified UDP address and port.
- This subtask typically runs in a `monitoring` phase to capture messages while other actions execute.
- The captured messages are logged and can be used by the `coap-send` subtask for communication.
- Ensure the chosen port is not blocked by a firewall and is not already in use.
- The standard CoAP port is 5683, but any available UDP port can be used.
- Use `coap-send` to send CoAP messages to devices using a monitor subtask as a communication endpoint.

## See Also
- [coap-send](./coap-send.md) — Send CoAP messages and wait for responses
