import time

# Controller Libs
import board
import analogio


# MIDI libs
import usb_midi
import adafruit_midi
from adafruit_midi.control_change import ControlChange

# DEF midi
midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=1)

pins = [analogio.AnalogIn(board.A0), analogio.AnalogIn(board.A1), analogio.AnalogIn(board.A2)]


def convert_value_to_cc(i: int) -> int:
    max_pin_value = 65536
    max_cc_value = 127
    pin_perc = int(round(((i/max_pin_value)*100),0))
    
    return int((pin_perc*127)/100)

knob_states = []

while True:
    pin_values = [convert_value_to_cc(p.value) for p in pins]
    
    if not knob_states:
        knob_states = pin_values[:]
        print(f'>>> Initial states: {str(knob_states)}')
        print(f'>>> Sync Volume levels with Knob state')
        for channel, ks in enumerate(knob_states): midi.send(ControlChange(7, ks), int(channel))
        
        
    for channel, pin_value in enumerate(pin_values):
        if abs(pin_value - knob_states[channel]) > 2:
            new_pin_value = pin_value
            print(f'CC:{channel} - NPV:{new_pin_value} - OldPV:{knob_states[channel]}') 
            midi.send(ControlChange(7, new_pin_value), int(channel))
                
            knob_states[channel] = new_pin_value
                
            #print(' | '.join(str(p) for p in pin_values))

    time.sleep(0.1)

