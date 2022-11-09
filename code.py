import time

# Controller Libs
import board
import digitalio
import rotaryio

# MIDI libs
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

# DEF midi
midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=1)

# DEF CC
cc = ConsumerControl(usb_hid.devices)

# Button = [Switch, InputA, InputB]
main = [digitalio.DigitalInOut(board.GP12), board.GP11, board.GP10]
b = [digitalio.DigitalInOut(board.GP15), board.GP14, board.GP13]
c = [digitalio.DigitalInOut(board.GP22), board.GP27, board.GP26]
d = [digitalio.DigitalInOut(board.GP19), board.GP21, board.GP20]
e = [digitalio.DigitalInOut(board.GP16), board.GP18, board.GP17]
rotaries = [main, b, c, d, e]
keys = []
encoders = []

def print_change(rotary: int, old: int, new: int) -> None:
    print(f'Rotary {rotary}: {old} -> {new}')

def main(encoder_states: list) -> None:
    while True:
        for i, e in enumerate(encoders):
            state = e.position
            state_change = state - encoder_states[i]

            if state_change > 0:
                if i == 0:
                    for _ in range(state_change):
                        cc.send(ConsumerControlCode.VOLUME_INCREMENT)
                else:
                    midi.send(ControlChange(7, 1), int(i))
            elif  state_change < 0:
                if i == 0:
                    for _ in range(-state_change):
                        cc.send(ConsumerControlCode.VOLUME_DECREMENT)
                else:
                    midi.send(ControlChange(7, 0), int(i))

            if state_change != 0:
                print_change(i, encoder_states[i], state)
                encoder_states[i] = state

        for i, k in enumerate(keys):
            if k.value:
                print(f'Key {i} pressed')

                if i == 0:
                    cc.send(ConsumerControlCode.MUTE)
                else:
                    midi.send(ControlChange(7, i), int(i))
                print(f'Key {i} pressed')

                time.sleep(0.1)

        time.sleep(0.1)

if __name__ == '__main__':
    for i, r in enumerate(rotaries):
            keys.append(r[0])
            keys[i].direction = digitalio.Direction.INPUT
            keys[i].pull = digitalio.Pull.DOWN

            encoders.append(rotaryio.IncrementalEncoder(r[1], r[2]))

    for e in encoders[1:]:
        e.position = 125

    encoder_states = [e.position for e in encoders]
    main(encoder_states)


