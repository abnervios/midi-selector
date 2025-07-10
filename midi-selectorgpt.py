import mido
import threading
from pynput import keyboard as pkb

# Mapeo de teclas a canales MIDI (1-16)
channel_map = {
    '1': 0,  # Canal 1 (0 basado)
    '2': 1,
    '3': 2,
    # agrega más si quieres
}

current_channel = 0  # Por defecto canal 1

active_notes = set()
output_port = None
virtual_input_name = 'EntradaVirtualControlador'
virtual_output_name = 'SalidaVirtualUnica'

def send_all_notes_off():
    if output_port:
        for note in list(active_notes):
            msg = mido.Message('note_off', note=note, velocity=0, channel=current_channel)
            output_port.send(msg)
        active_notes.clear()

def switch_channel(channel):
    global current_channel
    if channel == current_channel:
        return
    print(f"\n🎛 Cambiando canal MIDI a: {channel + 1}")
    send_all_notes_off()
    current_channel = channel

def midi_input_loop(virtual_port_name):
    global active_notes
    with mido.open_input(virtual_port_name, virtual=True) as inport:
        print(f"Puerto MIDI virtual de entrada creado: '{virtual_port_name}'. Conecta tu controlador aquí.")
        for msg in inport:
            # Cambia canal de mensajes MIDI que son tipo note_on / note_off / control_change / etc.
            if msg.type in ('note_on', 'note_off', 'control_change', 'program_change', 'pitchwheel'):
                msg.channel = current_channel

            if output_port:
                output_port.send(msg)

            if msg.type == 'note_on' and msg.velocity > 0:
                active_notes.add(msg.note)
            elif msg.type in ('note_off', 'note_on') and msg.velocity == 0:
                active_notes.discard(msg.note)

def on_press(key):
    try:
        if key.char in channel_map:
            switch_channel(channel_map[key.char])
    except AttributeError:
        pass

if __name__ == "__main__":
    output_port = mido.open_output(virtual_output_name, virtual=True)
    threading.Thread(target=midi_input_loop, args=(virtual_input_name,), daemon=True).start()

    print("🎹 Selector MIDI con puerto virtual único y cambio de canal MIDI")
    print(f"Puerto entrada: {virtual_input_name}")
    print(f"Puerto salida: {virtual_output_name}")
    print("Presiona 1, 2, 3 para cambiar instrumento (canal MIDI)")

    with pkb.Listener(on_press=on_press) as listener:
        listener.join()
123