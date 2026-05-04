import can
import time
import struct
import random

def run_emulator():
    # Используем socketcan и vcan0
    bus = can.interface.Bus(channel='vcan0', interface='socketcan')
    print("🚀 Satellite Emulator sending data to vcan0...")
    while True:
        try:
            # Напряжение: ID 257 (0x101)
            v_val = random.uniform(27.0, 29.0)
            v_msg = can.Message(arbitration_id=0x101, data=struct.pack('>f', v_val), is_extended_id=False)
            bus.send(v_msg)
            
            # Ток: ID 258 (0x102)
            i_val = random.uniform(1.0, 3.5)
            i_msg = can.Message(arbitration_id=0x102, data=struct.pack('>f', i_val), is_extended_id=False)
            bus.send(i_msg)
            
            time.sleep(1.0)
        except Exception as e:
            print(f"Error sending: {e}")

if __name__ == "__main__":
    run_emulator()
