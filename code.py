import time
import board
import digitalio
import rotaryio
import usb_midi
import adafruit_midi
from adafruit_midi.control_change import ControlChange
import usb_hid
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

# Turn on Board LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT
led.value = True

# Define MIDI and Consumer Control
midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=1)
cc = ConsumerControl(usb_hid.devices)

# Define rotary encoder pins
rotary_pins = [
    (board.GP12, board.GP11, board.GP10),
    (board.GP15, board.GP14, board.GP13),
    (board.GP22, board.GP27, board.GP26),
    (board.GP19, board.GP21, board.GP20),
    (board.GP16, board.GP18, board.GP17)
]

MUTE_CC = 94  # This CC number may vary depending on your MIDI Mixer setup
DEBOUNCE_TIME = 0.05  # 50ms debounce time

def setup_io():
    keys = []
    encoders = []
    for switch, pin_a, pin_b in rotary_pins:
        key = digitalio.DigitalInOut(switch)
        key.direction = digitalio.Direction.INPUT
        key.pull = digitalio.Pull.DOWN
        keys.append(key)
        encoders.append(rotaryio.IncrementalEncoder(pin_a, pin_b))
    
    for encoder in encoders[1:]:
        encoder.position = 125
    
    return keys, encoders

def handle_encoder(index, state_change):
    if index == 0:
        control = ConsumerControlCode.VOLUME_INCREMENT if state_change > 0 else ConsumerControlCode.VOLUME_DECREMENT
        for _ in range(abs(state_change)):
            cc.send(control)
    else:
        value = 1 if state_change > 0 else 0
        midi.send(ControlChange(7, value), index)

def handle_button_press(index):
    global mute_states
    mute_states[index] = not mute_states[index]
    value = 0 if mute_states[index] else 127
    midi.send(ControlChange(MUTE_CC, value), channel=index)
    print(f'Key {index} {"muted" if mute_states[index] else "unmuted"}')

def main():
    global mute_states
    keys, encoders = setup_io()
    encoder_states = [e.position for e in encoders]
    mute_states = [False] * len(keys)
    last_button_states = [False] * len(keys)
    last_button_times = [0] * len(keys)

    while True:
        current_time = time.monotonic()

        for i, (encoder, state) in enumerate(zip(encoders, encoder_states)):
            new_state = encoder.position
            state_change = new_state - state
            if state_change != 0:
                print(f'Rotary {i}: {state} -> {new_state}')
                handle_encoder(i, state_change)
                encoder_states[i] = new_state

        for i, key in enumerate(keys):
            current_state = key.value
            if current_state != last_button_states[i]:
                if current_time - last_button_times[i] > DEBOUNCE_TIME:
                    if current_state:  # Button is pressed
                        handle_button_press(i)
                    last_button_times[i] = current_time
                last_button_states[i] = current_state

        time.sleep(0.01)

if __name__ == '__main__':
    main()


