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
midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=0)
cc = ConsumerControl(usb_hid.devices)

# Define rotary encoder pins
# Format: (switch_pin, encoder_pin_a, encoder_pin_b)
rotary_pins = [
    (board.GP12, board.GP10, board.GP11),  # Encoder 0 - System Volume
    (board.GP15, board.GP13, board.GP14),  # Encoder 1
    (board.GP22, board.GP26, board.GP27),  # Encoder 2
    (board.GP19, board.GP20, board.GP21),  # Encoder 3
    (board.GP16, board.GP17, board.GP18)   # Encoder 4
]

# MIDI CC numbers
VOLUME_CC = 7      # Standard MIDI volume control
MUTE_CC = 94       # Mute control (can be customized)
DEBOUNCE_TIME = 0.1  # 100ms debounce time

# Detect if running on Pico W
def is_pico_w():
    """Check if running on Pico W by looking for the wireless module"""
    try:
        import wifi
        return True
    except ImportError:
        return False

def setup_io():
    """Initialize all encoders and buttons"""
    keys = []
    encoders = []
    
    for switch, pin_a, pin_b in rotary_pins:
        # Setup button with pull-down resistor
        key = digitalio.DigitalInOut(switch)
        key.direction = digitalio.Direction.INPUT
        key.pull = digitalio.Pull.DOWN
        keys.append(key)
        
        # Setup encoder
        encoder = rotaryio.IncrementalEncoder(pin_a, pin_b)
        encoders.append(encoder)
    
    # No need to initialize positions - we're using relative mode
    
    return keys, encoders

def handle_encoder(index, encoder, state_change):
    """Handle encoder rotation for volume control"""
    if index == 0:
        # System volume - use HID consumer control
        # Multiply by 2 for slightly faster volume changes (4% per click on Windows)
        volume_steps = state_change * 2
        print(f'Encoder 0 (System): {"UP" if state_change > 0 else "DOWN"} by {abs(volume_steps)} steps')
        
        if state_change > 0:
            for _ in range(volume_steps):
                cc.send(ConsumerControlCode.VOLUME_INCREMENT)
        else:
            for _ in range(abs(volume_steps)):
                cc.send(ConsumerControlCode.VOLUME_DECREMENT)
    else:
        # MIDI channels 1-4 - send relative changes
        # For infinite encoders, send increment (127) or decrement (0) signals
        if state_change > 0:
            # Send increment signal for each step
            for _ in range(state_change):
                midi.send(ControlChange(VOLUME_CC, 127), channel=index-1)
                print(f'Encoder {index}: Increment (channel {index-1})')
        elif state_change < 0:
            # Send decrement signal for each step
            for _ in range(abs(state_change)):
                midi.send(ControlChange(VOLUME_CC, 0), channel=index-1)
                print(f'Encoder {index}: Decrement (channel {index-1})')

def handle_button_press(index, mute_states, pico_w):
    """Handle button press for mute toggle"""
    if index == 0:
        # System mute - use HID consumer control
        print('System mute button pressed - sending MUTE command')
        try:
            cc.send(ConsumerControlCode.MUTE)
            print('System mute command sent successfully')
        except Exception as e:
            print(f'Error sending mute command: {e}')
    else:
        # MIDI mute toggle for channels 1-4
        mute_states[index] = not mute_states[index]
        value = 0 if mute_states[index] else 127  # 0 = mute, 127 = unmute
        
        # Send on the correct MIDI channel (0-based)
        midi.send(ControlChange(MUTE_CC, value), channel=index-1)
        print(f'Channel {index} {"muted" if mute_states[index] else "unmuted"} (value={value})')

def main():
    """Main program loop"""
    # Detect device type
    pico_w = is_pico_w()
    device_type = "Pico W" if pico_w else "Pico"
    
    # Initialize hardware
    keys, encoders = setup_io()
    encoder_states = [e.position for e in encoders]
    mute_states = [False] * len(keys)
    key_pressed = [False] * len(keys)
    
    # Startup info
    print(f"MIDI Controller Started on {device_type}")
    print("Encoder 0: System Volume (HID)")
    print("Encoders 1-4: MIDI Channels 0-3")
    
    # Test button connectivity at startup
    print("\nInitial button states:")
    for i, key in enumerate(keys):
        print(f"Button {i}: {'HIGH' if key.value else 'LOW'}")
    print("\nReady!\n")
    
    # Main loop
    while True:
        # Handle encoders
        for i, encoder in enumerate(encoders):
            new_state = encoder.position
            state_change = new_state - encoder_states[i]
            
            if state_change != 0:
                handle_encoder(i, encoder, state_change)
                encoder_states[i] = new_state
        
        # Handle buttons with edge detection
        for i, key in enumerate(keys):
            # With Pull.DOWN: pressed = HIGH, released = LOW
            current_state = key.value
            
            # Detect button press (transition from not pressed to pressed)
            if current_state and not key_pressed[i]:
                print(f'Button {i} pressed')
                handle_button_press(i, mute_states, pico_w)
                key_pressed[i] = True
            elif not current_state and key_pressed[i]:
                print(f'Button {i} released')
                key_pressed[i] = False
        
        time.sleep(0.01)  # Small delay to prevent CPU hogging

if __name__ == '__main__':
    main()
