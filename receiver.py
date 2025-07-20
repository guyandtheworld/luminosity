import socket
import json

PORT = 8081
BUFFER_SIZE = 1024

def main():
    # Set up UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', PORT))  # Empty string means all interfaces
    
    print(f"MIDI UDP Receiver running on port {PORT}")
    print("Waiting for broadcasts...")
    
    try:
        while True:
            # Receive data
            data, addr = sock.recvfrom(BUFFER_SIZE)
            
            try:
                msg = json.loads(data.decode())
                print(msg)
                # Process the MIDI message
                if msg["type"] == "note_on":
                    note_data = msg["data"]
                    pad_number = note_data['note'] - 36 + 1
                    print(f"Pad {pad_number} pressed with velocity {note_data['velocity']}")
                elif msg["type"] == "control_change":
                    cc_data = msg["data"]
                    print(f"Knob: controller={cc_data['control']}, value={cc_data['value']}")
                
            except json.JSONDecodeError:
                print("Invalid JSON received")
                
    except KeyboardInterrupt:
        sock.close()
        print("\nExiting...")

if __name__ == "__main__":
    main()