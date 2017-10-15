#Test for Relay

Home Assistant Config Example

``` yaml

mqtt:
  broker: 192.168.2.153



switch 1:
  - platform: mqtt
    name: "SW1"
    state_topic: "devices/esp8266_D_e302ee00/sw1/state"
    command_topic: "devices/esp8266_D_e302ee00/sw1/set"
    payload_on: "ON"
    payload_off: "OFF"
    optimistic: false
    qos: 0

switch 11:
  - platform: mqtt
    name: "SW1 manual"
    state_topic: "devices/esp8266_D_e302ee00/sw1/state"
    command_topic: "devices/esp8266_D_e302ee00/sw1/set"
    payload_on: "ON"
    payload_off: "OFF"
    optimistic: true
    qos: 0
    retain: true

switch 2:
  - platform: mqtt
    name: "SW2"
    state_topic: "devices/esp8266_D_e302ee00/sw2/state"
    command_topic: "devices/esp8266_D_e302ee00/sw2/set"
    payload_on: "ON"
    payload_off: "OFF"
    optimistic: false
    qos: 0

switch 22:
  - platform: mqtt
    name: "SW2 manual"
    state_topic: "devices/esp8266_D_e302ee00/sw2/state"
    command_topic: "devices/esp8266_D_e302ee00/sw2/set"
    payload_on: "ON"
    payload_off: "OFF"
    optimistic: True
    qos: 0
    retain: True

sensor 1:
  platform: mqtt
  name: "Temperature"
  state_topic:  "devices/esp8266_D_e302ee00/18b20"
  qos: 0
  unit_of_measurement: "ºC"

``` 