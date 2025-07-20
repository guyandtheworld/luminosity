import mido
import json
import time
import socket

PORT = 8081
# Try multiple broadcast addresses
BROADCAST_ADDRS = ["255.255.255.255", "192.168.1.255", "192.168.0.255"]

def main():
    # List available input ports
    print("Available MIDI input ports:")
    ports = mido.get_input_names()
    for i, port in enumerate(ports):
        print(f"{i}: {port}")
    
    # Look for LPD8
    lpd8_port = None
    for i, port in enumerate(ports):
        if "LPD8" in port:
            lpd8_port = port
            break
    
    if lpd8_port:
        print(f"Connecting to AKAI LPD8 on port: {lpd8_port}")
    else:
        print("LPD8 not found. Select port manually:")
        port_index = int(input("Enter port number: "))
        lpd8_port = ports[port_index]
    
    # Set up UDP socket for broadcasting
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Set socket timeout to avoid blocking
    sock.settimeout(0.1)
    
    # Open the input port
    with mido.open_input(lpd8_port) as inport:
        print(f"Monitoring {lpd8_port} and broadcasting to port {PORT}")
        try:
            while True:
                for msg in inport.iter_pending():
                    if msg.type in ['note_on', 'note_off', 'control_change']:
                        # Create message payload
                        command = {
                            "timestamp": time.time(),
                            "type": msg.type,
                            "data": dict(msg.dict())
                        }
                        
                        # Print to console
                        if msg.type == 'note_on':
                            pad_number = msg.note - 36 + 1  # LPD8 pads typically start at note 36
                            velocity = msg.velocity
                            print(f"Pad {pad_number} pressed with velocity {velocity}")
                        elif msg.type == 'control_change':
                            print(f"Knob: controller={msg.control}, value={msg.value}")
                        
                        # Try multiple broadcast addresses
                        data = json.dumps(command).encode()
                        success = False
                        for addr in BROADCAST_ADDRS:
                            try:
                                sock.sendto(data, (addr, PORT))
                                success = True
                                # Don't flood console with success messages
                            except Exception:
                                continue
                                
                        if success:
                            print("✓ Broadcast sent")
                        else:
                            print("✗ Broadcast failed")

                time.sleep(0.001)
        except KeyboardInterrupt:
            sock.close()
            print("\nExiting...")

if __name__ == "__main__":
    main()