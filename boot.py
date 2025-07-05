import supervisor
import usb_hid
import usb_cdc
import storage
import usb_midi

company = "MTIL Industries"
device_name = "PicoMixer"
midi_name = "PicoMixer MIDI"

supervisor.set_usb_identification(company, device_name)
usb_midi.set_names(streaming_interface_name=device_name, audio_control_interface_name=midi_name)

# Disable CIRCUITPY drive
storage.disable_usb_drive()

# Disable CDC (serial) devices
# usb_cdc.disable()

# Enable only specific HID devices
#usb_hid.enable((usb_hid.Device.KEYBOARD,))
