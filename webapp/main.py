from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import os
import json
import re
import asyncio
import threading
import logging
import subprocess
import sys
from bleak import BleakClient, BleakScanner
import time
import platform
from pathlib import Path

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration - OS agnostic paths
BASE_DIR = Path(__file__).parent
SCRIPTS_DIR = BASE_DIR / 'scripts'
LAYOUT_FILE = BASE_DIR / 'layout.json'

# Ensure directories exist
SCRIPTS_DIR.mkdir(exist_ok=True)

# OS Detection
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"
IS_MACOS = platform.system() == "Darwin"

# ESP32 BLE Configuration
DEVICE_NAME = "Other Hand HTN25"
DEVICE_MAC = "d8:3b:da:75:11:fd"
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"

# Global BLE state
ble_receiver = None
ble_connected = False
last_button_state = {}
ble_logs = []
MAX_LOG_LINES = 100

# Button activation tracking
button_states = {}  # Track press/release states for each module
button_timers = {}  # Track hold timers for each module

def parse_activation_type(activation_str):
    """Parse activation string to determine type and duration"""
    activation_str = activation_str.strip().lower()
    
    if activation_str == "on press":
        return "press", 0
    elif activation_str == "on release":
        return "release", 0
    elif activation_str.startswith("hold"):
        # Parse duration from "hold 3s", "hold 15s", etc.
        match = re.search(r'hold\s+(\d+)s?', activation_str)
        if match:
            duration = int(match.group(1))
            return "hold", duration
    
    # Default to "on press"
    return "press", 0

def get_python_executable():
    """Get the correct Python executable for the current OS"""
    if IS_WINDOWS:
        # On Windows, prefer python.exe, then py.exe, then sys.executable
        try:
            result = subprocess.run(['python', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return 'python'
        except:
            pass
        
        try:
            result = subprocess.run(['py', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return 'py'
        except:
            pass
    
    # Fallback to sys.executable (works on all platforms)
    return sys.executable

def get_module_script(slot_id):
    """Get the script for a given slot ID from the layout"""
    try:
        if LAYOUT_FILE.exists():
            with open(LAYOUT_FILE, 'r', encoding='utf-8') as f:
                layout = json.load(f)
                module_id = layout.get(slot_id)
                if module_id:
                    script_path = SCRIPTS_DIR / f"{module_id}.py"
                    if script_path.exists():
                        return str(script_path), module_id
        return None, None
    except Exception as e:
        print(f"Error getting module script: {e}")
        return None, None

def execute_script(script_path, module_id, reason=""):
    """Execute a script and log the output - OS agnostic"""
    try:
        python_cmd = get_python_executable()
        
        # Create platform-appropriate command
        if IS_WINDOWS:
            # On Windows, handle spaces in paths and use shell=True for better compatibility
            cmd = [python_cmd, str(script_path)]
            result = subprocess.run(cmd, 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=30,
                                  shell=False,
                                  encoding='utf-8',
                                  errors='replace')
        else:
            # On Linux/macOS, use standard approach
            result = subprocess.run([python_cmd, str(script_path)], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=30,
                                  encoding='utf-8',
                                  errors='replace')
        
        # Get output, handling both stdout and stderr
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            if output:
                output += "\n"
            output += f"STDERR: {result.stderr}"
        
        if not output:
            output = f"Script completed with return code: {result.returncode}"
        
        log_msg = f"🚀 Executed {module_id} {reason}: {output.strip()}"
        if ble_receiver:
            ble_receiver.add_log(log_msg)
        print(log_msg)
        
    except subprocess.TimeoutExpired:
        error_msg = f"❌ Script {module_id} timed out (30s)"
        if ble_receiver:
            ble_receiver.add_log(error_msg, "error")
        print(error_msg)
    except FileNotFoundError as e:
        error_msg = f"❌ Python executable not found for {module_id}: {e}"
        if ble_receiver:
            ble_receiver.add_log(error_msg, "error")
        print(error_msg)
    except Exception as e:
        error_msg = f"❌ Error executing {module_id}: {e}"
        if ble_receiver:
            ble_receiver.add_log(error_msg, "error")
        print(error_msg)

class WebAppBLEReceiver:
    """BLE Receiver integrated with Flask-SocketIO for real-time updates"""
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.is_running = False
        self.client = None
        self.reconnect_count = 0
        self.max_reconnect_attempts = 10
        
    def add_log(self, message, level="info"):
        """Add a log message and emit to connected clients"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "message": message,
            "level": level
        }
        
        global ble_logs
        ble_logs.append(log_entry)
        
        # Keep only last MAX_LOG_LINES entries
        if len(ble_logs) > MAX_LOG_LINES:
            ble_logs.pop(0)
        
        # Emit to all connected clients
        self.socketio.emit('ble_log', log_entry)
        
    def notification_handler(self, sender, data):
        """Handle incoming BLE notifications from ESP32"""
        global last_button_state, ble_connected, button_states, button_timers
        
        try:
            message = data.decode('utf-8').strip()
            self.add_log(f"📡 Received: {message}")
            
            # Parse button data: "position,state" (e.g., "4,1" = module 4, button pressed)
            if ',' in message:
                parts = message.split(',')
                if len(parts) == 2:
                    try:
                        position = int(parts[0])  # 0-7 (modules 0-7)
                        button_state = int(parts[1])  # 0 = released, 1 = pressed
                        
                        # Convert position to slot ID (binary representation)
                        slot_id = f"{position:03b}"  # Convert to 3-bit binary string
                        
                        # Update button state
                        last_button_state = {
                            "slot": slot_id,
                            "module_number": position,  # 0-7 for display
                            "pressed": button_state == 1,
                            "timestamp": time.time()
                        }
                        
                        # Emit button state to all connected clients
                        self.socketio.emit('button_press', last_button_state)
                        
                        self.add_log(f"🔘 Module {position} {'pressed' if button_state == 1 else 'released'}")
                        
                        # Handle script execution based on activation type
                        self.handle_button_activation(slot_id, position, button_state == 1)
                        
                    except ValueError:
                        self.add_log(f"❌ Invalid data format: {message}", "error")
                        
        except Exception as e:
            self.add_log(f"❌ Error processing data: {e}", "error")

    def handle_button_activation(self, slot_id, position, is_pressed):
        """Handle script execution based on button activation type"""
        global button_states, button_timers
        
        # Get the script and its activation type for this slot
        script_path, module_id = get_module_script(slot_id)
        if not script_path or not module_id:
            return  # No script assigned to this slot
        
        # Parse activation from script metadata
        _, _, _, _, activation = parse_script_metadata(script_path)
        activation_type, hold_duration = parse_activation_type(activation)
        
        # Track button state changes
        prev_state = button_states.get(position, False)
        button_states[position] = is_pressed
        
        if activation_type == "press" and is_pressed and not prev_state:
            # Execute on button press (press down event)
            self.add_log(f"🎯 Activating {module_id} (On Press)")
            threading.Thread(target=execute_script, args=(script_path, module_id, "(On Press)")).start()
            
        elif activation_type == "release" and not is_pressed and prev_state:
            # Execute on button release (release event)
            self.add_log(f"🎯 Activating {module_id} (On Release)")
            threading.Thread(target=execute_script, args=(script_path, module_id, "(On Release)")).start()
            
        elif activation_type == "hold":
            if is_pressed and not prev_state:
                # Button pressed - start hold timer
                def hold_timer():
                    time.sleep(hold_duration)
                    # Check if button is still pressed after hold duration
                    if button_states.get(position, False):
                        self.add_log(f"🎯 Activating {module_id} (Hold {hold_duration}s)")
                        execute_script(script_path, module_id, f"(Hold {hold_duration}s)")
                
                # Cancel any existing timer for this position
                if position in button_timers:
                    button_timers[position].cancel()
                
                # Start new hold timer
                timer = threading.Timer(hold_duration, hold_timer)
                timer.start()
                button_timers[position] = timer
                self.add_log(f"⏱️ Hold timer started for {module_id} ({hold_duration}s)")
                
            elif not is_pressed and prev_state:
                # Button released - cancel hold timer if running
                if position in button_timers:
                    button_timers[position].cancel()
                    del button_timers[position]
                    self.add_log(f"⏹️ Hold timer cancelled for {module_id}")

    def disconnect_handler(self, client):
        """Handle BLE disconnection events"""
        global ble_connected
        ble_connected = False
        self.add_log("🔌 Device disconnected!", "warning")
        self.socketio.emit('ble_status', {'connected': False})

    async def find_and_connect_device(self):
        """Find ESP32 device and establish connection - OS agnostic"""
        self.add_log("🔍 Scanning for ESP32...")
        
        # Platform-specific configuration
        if IS_WINDOWS:
            scan_timeout = 25.0
            connect_timeout = 60.0
            stabilization_delay = 6.0
            retry_delay = 4.0
        elif IS_LINUX:
            scan_timeout = 15.0
            connect_timeout = 30.0
            stabilization_delay = 3.0
            retry_delay = 2.0
        else:  # macOS
            scan_timeout = 20.0
            connect_timeout = 40.0
            stabilization_delay = 4.0
            retry_delay = 3.0
        
        # Scan for device with multiple attempts
        target_device = None
        for scan_attempt in range(3):
            try:
                self.add_log(f"🔍 Scan attempt {scan_attempt + 1}/3 (timeout: {scan_timeout}s)")
                devices = await BleakScanner.discover(timeout=scan_timeout)
                
                self.add_log(f"📱 Found {len(devices)} BLE devices")
                
                for device in devices:
                    # Check both name and MAC address (case-insensitive)
                    device_name = device.name or "Unknown"
                    device_addr = device.address.upper().replace(":", "").replace("-", "")
                    target_addr = DEVICE_MAC.upper().replace(":", "").replace("-", "")
                    
                    if (device_name == DEVICE_NAME or device_addr == target_addr):
                        target_device = device
                        self.add_log(f"✅ Found target device: {device_name} ({device.address})")
                        break
                
                if target_device:
                    break
                else:
                    self.add_log(f"❌ Target device not found in scan {scan_attempt + 1}/3", "warning")
                    if scan_attempt < 2:
                        await asyncio.sleep(retry_delay)
                        
            except Exception as e:
                self.add_log(f"❌ Scan attempt {scan_attempt + 1} failed: {e}", "error")
                if scan_attempt < 2:
                    await asyncio.sleep(retry_delay)
                
        if not target_device:
            raise Exception(f"ESP32 device '{DEVICE_NAME}' not found after {3} scan attempts")
        
        # Connect to device with OS-specific settings
        self.add_log(f"🔗 Connecting to {target_device.address} (timeout: {connect_timeout}s)...")
        
        # Create client with OS-specific parameters
        client_kwargs = {
            "address_or_ble_device": target_device.address,
            "disconnected_callback": self.disconnect_handler,
            "timeout": connect_timeout,
        }
        
        # Windows-specific: don't use cached services (can cause issues)
        if not IS_WINDOWS:
            client_kwargs["use_cached_services"] = True
        
        self.client = BleakClient(**client_kwargs)
        
        # Connect with retries
        for attempt in range(3):
            try:
                self.add_log(f"🔗 Connection attempt {attempt + 1}/3...")
                await self.client.connect()
                
                if self.client.is_connected:
                    self.add_log("✅ Connected successfully!")
                    break
                else:
                    raise Exception("Connection reported success but client not connected")
                    
            except Exception as e:
                self.add_log(f"❌ Connection attempt {attempt + 1} failed: {e}", "error")
                if attempt < 2:
                    self.add_log(f"⏳ Retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                else:
                    raise Exception(f"Failed to connect after 3 attempts: {e}")
        
        # Platform-specific stabilization
        self.add_log(f"⏳ Stabilizing connection ({stabilization_delay}s)...")
        await asyncio.sleep(stabilization_delay)
        
        if not self.client.is_connected:
            raise Exception("Connection lost during stabilization")
            
        return self.client

    async def setup_notifications(self):
        """Setup BLE notifications with error handling"""
        self.add_log("📡 Setting up notifications...")
        
        services = self.client.services
        target_service = None
        
        for service in services:
            if service.uuid.lower() == SERVICE_UUID.lower():
                target_service = service
                break
        
        if not target_service:
            raise Exception(f"Service {SERVICE_UUID} not found")
        
        self.add_log(f"✅ Found service: {target_service.uuid}")
        
        # Subscribe to notifications
        for attempt in range(3):
            try:
                await self.client.start_notify(CHARACTERISTIC_UUID, self.notification_handler)
                self.add_log("✅ Subscribed to notifications!")
                return
                
            except Exception as e:
                self.add_log(f"❌ Notification setup attempt {attempt + 1} failed: {e}", "error")
                if attempt < 2:
                    await asyncio.sleep(1)
                else:
                    raise Exception(f"Failed to setup notifications: {e}")

    async def maintain_connection(self):
        """Maintain connection and handle data"""
        global ble_connected
        ble_connected = True
        
        self.add_log("🎯 Ready to receive data! Press buttons on ESP32...")
        self.socketio.emit('ble_status', {'connected': True})
        
        try:
            while self.is_running and self.client and self.client.is_connected:
                await asyncio.sleep(1.0)
                
                # Periodic connection check
                if not self.client.is_connected:
                    self.add_log("⚠️ Connection lost during operation", "warning")
                    break
                    
        except Exception as e:
            self.add_log(f"❌ Connection maintenance error: {e}", "error")
            
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Clean up BLE connection"""
        global ble_connected
        
        if self.client and self.client.is_connected:
            try:
                self.add_log("🧹 Cleaning up connection...")
                await self.client.stop_notify(CHARACTERISTIC_UUID)
                await self.client.disconnect()
                self.add_log("✅ Disconnected cleanly")
            except Exception as e:
                self.add_log(f"❌ Cleanup error: {e}", "error")
        
        ble_connected = False
        self.socketio.emit('ble_status', {'connected': False})

    async def run(self):
        """Main run loop with OS-agnostic reconnection logic"""
        self.is_running = True
        
        # Platform-specific retry settings
        if IS_WINDOWS:
            max_attempts = 8  # Windows needs more attempts
            base_delay = 6
            max_delay = 30
        else:
            max_attempts = 5
            base_delay = 3
            max_delay = 20
        
        while self.is_running and self.reconnect_count < max_attempts:
            try:
                # Connect to device
                await self.find_and_connect_device()
                
                # Setup notifications
                await self.setup_notifications()
                
                # Reset reconnect counter on successful connection
                self.reconnect_count = 0
                
                # Maintain connection
                await self.maintain_connection()
                
            except Exception as e:
                self.add_log(f"❌ Connection error: {e}", "error")
                self.reconnect_count += 1
                
                if self.reconnect_count < max_attempts:
                    # Exponential backoff with platform-specific limits
                    delay = min(base_delay + self.reconnect_count * 2, max_delay)
                    self.add_log(f"🔄 Reconnecting in {delay}s... (attempt {self.reconnect_count}/{max_attempts})")
                    await asyncio.sleep(delay)
                else:
                    self.add_log(f"❌ Max reconnection attempts ({max_attempts}) reached", "error")
                    break
        
        self.is_running = False
        await self.cleanup()

    def stop(self):
        """Stop the BLE receiver"""
        self.is_running = False

def parse_script_metadata(file_path):
    """Parse name, description, icon, color, and activation from script docstring - OS agnostic"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Extract docstring
        docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        if not docstring_match:
            return None, None, None, None, None
        
        docstring = docstring_match.group(1).strip()
        
        # Parse name, description, icon, color, and activation
        name_match = re.search(r'Name:\s*(.+)', docstring)
        desc_match = re.search(r'Description:\s*(.+)', docstring)
        icon_match = re.search(r'Icon:\s*(.+)', docstring)
        color_match = re.search(r'Color:\s*(.+)', docstring)
        activation_match = re.search(r'Activation:\s*(.+)', docstring)
        
        name = name_match.group(1).strip() if name_match else Path(file_path).stem
        description = desc_match.group(1).strip() if desc_match else "No description available"
        icon = icon_match.group(1).strip() if icon_match else "🔧"
        color = color_match.group(1).strip() if color_match else None
        activation = activation_match.group(1).strip() if activation_match else "On Press"
        
        return name, description, icon, color, activation
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return None, None, None, None, None

def get_script_code(file_path):
    """Read the full script code - OS agnostic"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/scripts')
def get_scripts():
    """Get all available scripts with metadata - OS agnostic"""
    scripts = []
    
    # Ensure scripts directory exists
    SCRIPTS_DIR.mkdir(exist_ok=True)
    
    try:
        for file_path in SCRIPTS_DIR.glob('*.py'):
            name, description, icon, color, activation = parse_script_metadata(str(file_path))
            
            if name:  # Only include if we could parse metadata
                scripts.append({
                    'id': file_path.stem,
                    'name': name,
                    'description': description,
                    'icon': icon,
                    'color': color,
                    'activation': activation,
                    'path': file_path.name,
                    'code': get_script_code(str(file_path))
                })
    except Exception as e:
        print(f"Error reading scripts directory: {e}")
    
    return jsonify(scripts)

@app.route('/api/layout', methods=['GET'])
def get_layout():
    """Get the current layout - OS agnostic"""
    if LAYOUT_FILE.exists():
        try:
            with open(LAYOUT_FILE, 'r', encoding='utf-8') as f:
                layout = json.load(f)
            return jsonify(layout)
        except Exception as e:
            print(f"Error reading layout: {e}")
    
    # Return empty layout if file doesn't exist
    return jsonify({
        "000": None, "001": None, "010": None, "011": None,
        "100": None, "101": None, "110": None, "111": None
    })

@app.route('/api/layout', methods=['POST'])
def save_layout():
    """Save the current layout - OS agnostic"""
    try:
        layout = request.json
        with open(LAYOUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(layout, f, indent=2, ensure_ascii=False)
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error saving layout: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/scripts', methods=['POST'])
def create_script():
    """Create a new script file"""
    try:
        data = request.json
        name = data.get('name', 'Unnamed')
        description = data.get('description', 'No description')
        icon = data.get('icon', '🔧')
        color = data.get('color')
        code = data.get('code', '')
        
        if not name:
            return jsonify({"success": False, "error": "Script name is required"}), 400
        
        # Generate script ID from name
        script_id = name.lower().replace(' ', '_').replace('-', '_')
        # Remove any non-alphanumeric characters except underscore
        import re
        script_id = re.sub(r'[^a-z0-9_]', '', script_id)
        
        if not script_id:
            script_id = 'untitled_script'
        
        # Check if file already exists
        script_path = SCRIPTS_DIR / f"{script_id}.py"
        counter = 1
        original_id = script_id
        while script_path.exists():
            script_id = f"{original_id}_{counter}"
            script_path = SCRIPTS_DIR / f"{script_id}.py"
            counter += 1
        
        # Create the script content
        color_line = f"Color: {color}\n" if color else ""
        script_content = f'''"""
Name: {name}
Description: {description}
Icon: {icon}
{color_line}"""

{code}'''
        
        # Write the script file with proper encoding
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
            
        return jsonify({
            "success": True, 
            "script_id": script_id,
            "path": f"{script_id}.py"
        })
    except Exception as e:
        print(f"Error creating script: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/scripts/<script_id>', methods=['PUT'])
def update_script(script_id):
    """Update an existing script - OS agnostic"""
    try:
        data = request.json
        script_path = SCRIPTS_DIR / f"{script_id}.py"
        
        if not script_path.exists():
            return jsonify({"success": False, "error": "Script not found"}), 404
        
        # Create the updated script content
        name = data.get('name', 'Unnamed')
        description = data.get('description', 'No description')
        icon = data.get('icon', '🔧')
        color = data.get('color')
        code = data.get('code', '')
        
        color_line = f"Color: {color}\n" if color else ""
        script_content = f'''"""
Name: {name}
Description: {description}
Icon: {icon}
{color_line}"""

{code}'''
        
        # Write the updated script with proper encoding
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
            
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error updating script: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/scripts/<script_id>', methods=['DELETE'])
def delete_script(script_id):
    """Delete a script - OS agnostic"""
    try:
        script_path = SCRIPTS_DIR / f"{script_id}.py"
        
        if not script_path.exists():
            return jsonify({"success": False, "error": "Script not found"}), 404
        
        script_path.unlink()  # Pathlib method for deleting files
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error deleting script: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/scripts/<script_id>/test', methods=['POST'])
def test_script(script_id):
    """Test a script by running it and capturing output - OS agnostic"""
    try:
        script_path = SCRIPTS_DIR / f"{script_id}.py"
        
        if not script_path.exists():
            return jsonify({"success": False, "error": "Script not found"}), 404
        
        # Use subprocess for more reliable cross-platform execution
        try:
            python_cmd = get_python_executable()
            
            # Run with platform-appropriate settings
            if IS_WINDOWS:
                result = subprocess.run(
                    [python_cmd, str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    encoding='utf-8',
                    errors='replace',
                    shell=False
                )
            else:
                result = subprocess.run(
                    [python_cmd, str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    encoding='utf-8',
                    errors='replace'
                )
            
            stdout_content = result.stdout or ""
            stderr_content = result.stderr or ""
            
            return jsonify({
                "success": True,
                "output": stdout_content,
                "error": stderr_content if stderr_content else None,
                "return_code": result.returncode
            })
            
        except subprocess.TimeoutExpired:
            return jsonify({
                "success": False,
                "output": "",
                "error": "Script execution timed out (10s limit)"
            })
        except Exception as subprocess_error:
            # Fallback to exec() method
            try:
                from io import StringIO
                import contextlib
                
                # Read the script content
                with open(script_path, 'r', encoding='utf-8') as f:
                    script_content = f.read()
                
                # Create output capture
                output = StringIO()
                error_output = StringIO()
                
                # Create a safe namespace
                safe_globals = {
                    "__name__": "__main__",
                    "__builtins__": __builtins__,
                    "print": print,
                }
                
                # Add common modules
                try:
                    safe_globals.update({
                        "os": __import__("os"),
                        "sys": __import__("sys"),
                        "json": __import__("json"),
                        "time": __import__("time"),
                        "random": __import__("random"),
                        "datetime": __import__("datetime"),
                        "webbrowser": __import__("webbrowser"),
                        "platform": __import__("platform"),
                        "pathlib": __import__("pathlib"),
                    })
                except ImportError:
                    pass  # Some modules might not be available
                
                # Execute with output capture
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error_output):
                    exec(script_content, safe_globals, {})
                
                return jsonify({
                    "success": True,
                    "output": output.getvalue(),
                    "error": error_output.getvalue() if error_output.getvalue() else None
                })
                
            except Exception as exec_error:
                return jsonify({
                    "success": False,
                    "output": "",
                    "error": f"Execution error: {str(exec_error)}"
                })
    
    except Exception as e:
        print(f"Error testing script: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# BLE Management Routes
@app.route('/api/ble/status')
def get_ble_status():
    """Get current BLE connection status"""
    global ble_connected, last_button_state, ble_logs
    return jsonify({
        "connected": ble_connected,
        "last_button": last_button_state,
        "logs": ble_logs[-20:] if ble_logs else []  # Return last 20 log entries
    })

@app.route('/api/ble/logs')
def get_ble_logs():
    """Get all BLE logs"""
    global ble_logs
    return jsonify({"logs": ble_logs})

@app.route('/api/ble/connect', methods=['POST'])
def connect_ble():
    """Start BLE connection in a separate thread - OS agnostic"""
    global ble_receiver
    
    try:
        if ble_receiver and ble_receiver.is_running:
            return jsonify({"success": False, "error": "BLE receiver already running"}), 400
        
        # Create and start BLE receiver
        ble_receiver = WebAppBLEReceiver(socketio)
        
        def run_ble_async():
            # Create new event loop for this thread (required on Windows)
            if IS_WINDOWS:
                # Windows-specific event loop policy
                if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
                    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(ble_receiver.run())
            except Exception as e:
                print(f"BLE async error: {e}")
            finally:
                try:
                    loop.close()
                except:
                    pass
        
        # Start BLE receiver in a separate thread
        ble_thread = threading.Thread(target=run_ble_async, daemon=True)
        ble_thread.start()
        
        return jsonify({"success": True, "message": "BLE connection started"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/ble/disconnect', methods=['POST'])
def disconnect_ble():
    """Stop BLE connection"""
    global ble_receiver, ble_connected
    
    try:
        if ble_receiver:
            ble_receiver.stop()
            ble_receiver = None
        
        ble_connected = False
        return jsonify({"success": True, "message": "BLE connection stopped"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# SocketIO Events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    # Send current BLE status to new client
    emit('ble_status', {'connected': ble_connected})
    if last_button_state:
        emit('button_press', last_button_state)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

@socketio.on('request_ble_status')
def handle_ble_status_request():
    """Handle request for current BLE status"""
    global ble_connected, last_button_state, ble_logs
    emit('ble_status', {'connected': ble_connected})
    if last_button_state:
        emit('button_press', last_button_state)
    emit('ble_logs', {'logs': ble_logs[-20:] if ble_logs else []})

# Auto-start BLE connection on startup (optional)
def auto_start_ble():
    """Auto-start BLE connection if enabled"""
    # You can uncomment this to auto-start BLE on server startup
    # try:
    #     time.sleep(2)  # Give server time to start
    #     with app.test_request_context():
    #         connect_ble()
    # except Exception as e:
    #     print(f"Auto-start BLE failed: {e}")
    pass

if __name__ == '__main__':
    print(f"🚀 Starting Flask-SocketIO app on {platform.system()}")
    print(f"📁 Scripts directory: {SCRIPTS_DIR}")
    print(f"📄 Layout file: {LAYOUT_FILE}")
    print(f"🐍 Python executable: {get_python_executable()}")
    
    # Start auto BLE connection in a separate thread
    ble_auto_thread = threading.Thread(target=auto_start_ble, daemon=True)
    ble_auto_thread.start()
    
    # Platform-specific Flask configuration
    if IS_WINDOWS:
        # Windows-specific settings for better compatibility
        socketio.run(
            app, 
            debug=False,  # Disable debug on Windows to avoid reload issues
            host='0.0.0.0', 
            port=5000, 
            allow_unsafe_werkzeug=True,
            use_reloader=False  # Disable reloader on Windows
        )
    else:
        # Linux/macOS settings
        socketio.run(
            app, 
            debug=True, 
            host='0.0.0.0', 
            port=5000, 
            allow_unsafe_werkzeug=True
        )