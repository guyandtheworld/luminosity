#!/usr/bin/env python3
"""
Sister HQ Script
----------------
This script runs on the Raspberry Pi devices and receives commands from the Command HQ.
It sets up a simple HTTP server to receive JSON commands and respond to status requests.
"""

import json
import time
import argparse
import socket
import os
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from datetime import datetime

# Configuration
DEFAULT_PORT = 8081
SHIP_NAME = socket.gethostname()  # Use hostname as ship name

class CommandHandler(BaseHTTPRequestHandler):
    """HTTP handler for receiving commands and providing status"""
    
    def _set_headers(self, content_type="application/json"):
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.end_headers()
        
    def do_GET(self):
        """Handle GET requests for status"""
        if self.path == "/status":
            self._set_headers()
            status = self.server.sister_ship.get_status()
            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_response(404)
            self.end_headers()
            
    def do_POST(self):
        """Handle POST requests for commands"""
        if self.path == "/command":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                command = json.loads(post_data.decode())
                self._set_headers()
                result = self.server.sister_ship.handle_command(command)
                self.wfile.write(json.dumps({"success": True, "result": result}).encode())
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "Invalid JSON"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Custom log function to reduce console spam"""
        # Print more concise logs
        if args[1] in ["200", "201"]:  # Successful responses
            return
        super().log_message(format, *args)


class SisterShip:
    """Main class representing the sister ship"""
    
    def __init__(self):
        self.start_time = time.time()
        self.last_command = None
        self.command_count = 0
        self.command_history = []
        
    def get_status(self):
        """Get the current status of the ship"""
        # Get system info
        cpu_temp = self._get_cpu_temp()
        cpu_usage = self._get_cpu_usage()
        memory_usage = self._get_memory_usage()
        disk_usage = self._get_disk_usage()
        
        return {
            "ship_name": SHIP_NAME,
            "uptime": time.time() - self.start_time,
            "timestamp": datetime.now().isoformat(),
            "last_command": self.last_command,
            "command_count": self.command_count,
            "system": {
                "cpu_temp": cpu_temp,
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_usage": disk_usage
            }
        }
        
    def handle_command(self, command):
        """Process a command received from Command HQ"""
        self.command_count += 1
        self.last_command = command
        self.command_history.append(command)
        
        # Log the command
        print(f"Received command: {command['type']}")
        
        # Handle different command types
        if command["type"] == "echo":
            return {"message": command["data"]}
            
        elif command["type"] == "shutdown":
            # Schedule a shutdown
            def delayed_shutdown():
                time.sleep(5)
                os.system("sudo shutdown -h now")
            threading.Thread(target=delayed_shutdown).start()
            return {"message": "Shutdown scheduled in 5 seconds"}
            
        elif command["type"] == "reboot":
            # Schedule a reboot
            def delayed_reboot():
                time.sleep(5)
                os.system("sudo reboot")
            threading.Thread(target=delayed_reboot).start()
            return {"message": "Reboot scheduled in 5 seconds"}
            
        elif command["type"] == "execute":
            # Execute a shell command
            try:
                # Be careful with this in production!
                # This allows arbitrary command execution
                output = subprocess.check_output(
                    command["data"], 
                    shell=True, 
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                return {"output": output}
            except subprocess.CalledProcessError as e:
                return {"error": str(e), "output": e.output}
                
        elif command["type"] == "status":
            # Return detailed status
            return self.get_status()
            
        else:
            return {"error": f"Unknown command type: {command['type']}"}
    
    def _get_cpu_temp(self):
        """Get the CPU temperature"""
        try:
            temp = 0
            if os.path.exists('/sys/class/thermal/thermal_zone0/temp'):
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    temp = float(f.read()) / 1000.0
            return temp
        except:
            return 0
    
    def _get_cpu_usage(self):
        """Get the CPU usage percentage"""
        try:
            return float(subprocess.check_output(
                "top -bn1 | grep 'Cpu(s)' | awk '{print $2}'", 
                shell=True
            ).decode().strip())
        except:
            return 0
    
    def _get_memory_usage(self):
        """Get memory usage statistics"""
        try:
            total = subprocess.check_output(
                "free -m | awk 'NR==2{print $2}'", 
                shell=True
            ).decode().strip()
            used = subprocess.check_output(
                "free -m | awk 'NR==2{print $3}'", 
                shell=True
            ).decode().strip()
            return {
                "total": int(total),
                "used": int(used),
                "percent": round(int(used) / int(total) * 100, 1)
            }
        except:
            return {"total": 0, "used": 0, "percent": 0}
    
    def _get_disk_usage(self):
        """Get disk usage statistics"""
        try:
            total = subprocess.check_output(
                "df -h / | awk 'NR==2{print $2}'", 
                shell=True
            ).decode().strip()
            used = subprocess.check_output(
                "df -h / | awk 'NR==2{print $3}'", 
                shell=True
            ).decode().strip()
            percent = subprocess.check_output(
                "df -h / | awk 'NR==2{print $5}'", 
                shell=True
            ).decode().strip()
            return {
                "total": total,
                "used": used,
                "percent": percent
            }
        except:
            return {"total": "0G", "used": "0G", "percent": "0%"}

def run_server(port):
    """Run the HTTP server"""
    sister_ship = SisterShip()
    server_address = ('', port)
    httpd = HTTPServer(server_address, CommandHandler)
    httpd.sister_ship = sister_ship
    
    print(f"Starting Sister HQ server on port {port}...")
    print(f"Ship Name: {SHIP_NAME}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("Server stopped.")

def main():
    parser = argparse.ArgumentParser(description="Sister HQ for receiving commands")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to run on")
    args = parser.parse_args()
    
    run_server(args.port)

if __name__ == "__main__":
    main()