import mido
import threading
import time
from pynput import keyboard


class MidiRouter:
    def __init__(self):
        self.active_notes = set()
        self.output_ports = {}
        self.current_output = None
        self.keyboard_listener = None
        self.virtual_input = None
        self.running = False

        # Teclas/puertos (la primera será la seleccionada por defecto)
        self.teclas_puertos = ['1', '2', '3', '0', 'q']  # '1' es ahora el primer elemento

    def create_virtual_ports(self):
        """Crea puertos y selecciona '1' por defecto"""
        try:
            # Puerto de entrada
            self.virtual_input = mido.open_input('MIDI-IN', virtual=True)
            print("\n🎹 Puerto ENTRADA: 'MIDI-IN'")

            # Crear puertos de salida
            for tecla in self.teclas_puertos:
                port_name = f"MIDI-{tecla}"
                self.output_ports[tecla] = mido.open_output(port_name, virtual=True)
                print(f"🎚️ Puerto SALIDA '{tecla}': '{port_name}'")

            # Seleccionar automáticamente la tecla '1'
            if '1' in self.output_ports:
                self.current_output = '1'
                print(f"\n🔴 Puerto inicial seleccionado: MIDI-1 (Tecla 1)")

            print("\n🔌 En QjackCtl conecta:")
            print("  MIDI-IN → Tus controladores MIDI")
            for tecla in self.teclas_puertos:
                print(f"  MIDI-{tecla} → Instrumento {tecla}")

        except Exception as e:
            print(f"\n❌ Error creando puertos: {e}")
            self.shutdown()
            exit(1)

    def send_all_notes_off(self):
        """Apaga todas las notas activas"""
        for port in self.output_ports.values():
            for note in list(self.active_notes):
                port.send(mido.Message('note_off', note=note, velocity=0))
        self.active_notes.clear()

    def switch_output(self, tecla):
        """Cambia al puerto asociado a la tecla"""
        if tecla not in self.output_ports:
            return

        if tecla == self.current_output:
            return

        print(f"\n🔀 Cambiando a: MIDI-{tecla} (Tecla {tecla})")
        self.send_all_notes_off()
        self.current_output = tecla

    def midi_input_loop(self):
        """Bucle principal de procesamiento MIDI"""
        try:
            for msg in self.virtual_input:
                if not self.running:
                    break

                # Reenviar solo al puerto activo
                if self.current_output and msg.type != 'clock':
                    self.output_ports[self.current_output].send(msg)

                    # Actualizar estado de notas
                    if msg.type == 'note_on' and msg.velocity > 0:
                        self.active_notes.add(msg.note)
                    elif msg.type in ('note_off', 'note_on') and msg.velocity == 0:
                        self.active_notes.discard(msg.note)

        except Exception as e:
            print(f"⚠️ Error MIDI: {e}")

    def on_press(self, key):
        """Maneja pulsaciones de teclado"""
        try:
            key_char = getattr(key, 'char', None)
            if key_char in self.output_ports:
                self.switch_output(key_char)
        except Exception as e:
            print(f"⚠️ Error de teclado: {e}")

    def start(self):
        """Inicia el sistema con '1' seleccionado"""
        print("\n🚀 MIDI Router - Listo")
        print("💡 Teclas activas:", " ".join(self.teclas_puertos))

        self.create_virtual_ports()

        # Iniciar listeners
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press)
        self.keyboard_listener.start()

        self.running = True
        midi_thread = threading.Thread(target=self.midi_input_loop, daemon=True)
        midi_thread.start()

        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        """Cierra todos los recursos"""
        print("\n🛑 Cerrando router...")
        self.running = False
        self.send_all_notes_off()

        if self.keyboard_listener:
            self.keyboard_listener.stop()

        if self.virtual_input:
            self.virtual_input.close()

        for port in self.output_ports.values():
            port.close()

        print("✅ Recursos liberados")


if __name__ == "__main__":
    router = MidiRouter()
    router.start()