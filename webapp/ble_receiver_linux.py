#!/usr/bin/env python3
"""
Improved BLE Receiver for Linux - Handles Linux BLE stack quirks
"""

import asyncio
import sys
import platform
from bleak import BleakClient, BleakScanner
import logging
import time

# ESP32 BLE Configuration
DEVICE_NAME = "Other Hand HTN25"
DEVICE_MAC = "d8:3b:da:75:11:fd"
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"

# Linux-optimized settings
SCAN_TIMEOUT = 20.0
CONNECTION_TIMEOUT = 30.0
STABILIZATION_DELAY = 3.0
MAX_RECONNECT_ATTEMPTS = 10

# Enable logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LinuxBLEReceiver:
    def __init__(self):
        self.is_running = False
        self.client = None
        self.reconnect_count = 0
        
    def notification_handler(self, sender, data):
        """Handle incoming BLE notifications from ESP32"""
        try:
            message = data.decode('utf-8')
            print(f"📡 ESP32: {message}")
            logger.info(f"Received: {message}")
        except Exception as e:
            print(f"📡 ESP32 sent raw: {data}")
            logger.info(f"Raw data: {data}")

    def disconnect_handler(self, client):
        """Handle BLE disconnection events"""
        print("🔌 Connection lost!")
        logger.warning("BLE connection lost unexpectedly")

    async def find_and_connect_device(self):
        """Find ESP32 device and establish connection"""
        print("🔍 Scanning for ESP32...")
        
        # Longer scan with multiple attempts
        for scan_attempt in range(3):
            try:
                devices = await BleakScanner.discover(timeout=SCAN_TIMEOUT)
                
                target_device = None
                for device in devices:
                    if (device.name == DEVICE_NAME or 
                        device.address.upper() == DEVICE_MAC.upper()):
                        target_device = device
                        break
                
                if target_device:
                    print(f"✅ Found {target_device.name} ({target_device.address})")
                    break
                else:
                    print(f"❌ Device not found in scan {scan_attempt + 1}/3")
                    if scan_attempt < 2:
                        await asyncio.sleep(2)
                        
            except Exception as e:
                logger.error(f"Scan attempt {scan_attempt + 1} failed: {e}")
                
        if not target_device:
            raise Exception("ESP32 device not found after multiple scan attempts")
        
        # Attempt connection with Linux-specific optimizations
        print(f"🔗 Connecting to {target_device.address}...")
        
        # Create client with Linux-optimized settings
        self.client = BleakClient(
            target_device.address,
            disconnected_callback=self.disconnect_handler,
            timeout=CONNECTION_TIMEOUT,
            use_cached_services=True,  # Use cached services since device is paired
        )
        
        # Connect with retries
        for attempt in range(3):
            try:
                await self.client.connect()
                
                if self.client.is_connected:
                    print(f"✅ Connected successfully!")
                    break
                else:
                    raise Exception("Connection reported success but client not connected")
                    
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    await asyncio.sleep(2)
                else:
                    raise Exception(f"Failed to connect after 3 attempts: {e}")
        
        # Stabilization delay - critical for Linux BLE
        print(f"⏳ Stabilizing connection ({STABILIZATION_DELAY}s)...")
        await asyncio.sleep(STABILIZATION_DELAY)
        
        if not self.client.is_connected:
            raise Exception("Connection lost during stabilization")
            
        return self.client

    async def setup_notifications(self):
        """Setup BLE notifications with error handling"""
        print("📡 Setting up notifications...")
        
        # Verify service exists (it should since device is paired)
        services = self.client.services
        target_service = None
        
        for service in services:
            if service.uuid.lower() == SERVICE_UUID.lower():
                target_service = service
                break
        
        if not target_service:
            raise Exception(f"Service {SERVICE_UUID} not found")
        
        print(f"✅ Found service: {target_service.uuid}")
        
        # Verify characteristic exists
        target_char = None
        for char in target_service.characteristics:
            if char.uuid.lower() == CHARACTERISTIC_UUID.lower():
                target_char = char
                break
        
        if not target_char:
            raise Exception(f"Characteristic {CHARACTERISTIC_UUID} not found")
        
        print(f"✅ Found characteristic: {target_char.uuid}")
        print(f"   Properties: {target_char.properties}")
        
        # Subscribe to notifications with retries
        for attempt in range(3):
            try:
                await self.client.start_notify(CHARACTERISTIC_UUID, self.notification_handler)
                print("✅ Subscribed to notifications!")
                return
                
            except Exception as e:
                logger.error(f"Notification setup attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    await asyncio.sleep(1)
                else:
                    raise Exception(f"Failed to setup notifications: {e}")

    async def maintain_connection(self):
        """Maintain connection and handle data"""
        print("\n🎯 Ready to receive data! Press button on ESP32...")
        print("Press Ctrl+C to stop\n")
        
        last_check = time.time()
        check_interval = 5.0  # Check connection every 5 seconds
        
        try:
            while self.is_running and self.client and self.client.is_connected:
                await asyncio.sleep(0.5)
                
                # Periodic connection check
                current_time = time.time()
                if current_time - last_check > check_interval:
                    if not self.client.is_connected:
                        print("⚠️  Connection lost during operation")
                        break
                    print(f"💓 Connection healthy (RSSI: checking...)")
                    last_check = current_time
                    
        except Exception as e:
            logger.error(f"Connection maintenance error: {e}")
            
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Clean up BLE connection"""
        if self.client and self.client.is_connected:
            try:
                print("🧹 Cleaning up connection...")
                await self.client.stop_notify(CHARACTERISTIC_UUID)
                await self.client.disconnect()
                print("✅ Disconnected cleanly")
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    async def run(self):
        """Main run loop with reconnection logic"""
        self.is_running = True
        
        while self.is_running and self.reconnect_count < MAX_RECONNECT_ATTEMPTS:
            try:
                # Connect to device
                await self.find_and_connect_device()
                
                # Setup notifications
                await self.setup_notifications()
                
                # Reset reconnect counter on successful connection
                self.reconnect_count = 0
                
                # Maintain connection
                await self.maintain_connection()
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping by user request...")
                break
                
            except Exception as e:
                print(f"❌ Connection error: {e}")
                self.reconnect_count += 1
                
                if self.reconnect_count < MAX_RECONNECT_ATTEMPTS:
                    delay = min(5 + self.reconnect_count * 2, 20)  # Progressive delay
                    print(f"🔄 Reconnecting in {delay}s... (attempt {self.reconnect_count}/{MAX_RECONNECT_ATTEMPTS})")
                    await asyncio.sleep(delay)
                else:
                    print(f"❌ Max reconnection attempts ({MAX_RECONNECT_ATTEMPTS}) reached")
                    break
        
        self.is_running = False
        await self.cleanup()

def main():
    print("🚀 Linux-Optimized ESP32 BLE Receiver")
    print("=" * 50)
    print(f"Target: {DEVICE_NAME} ({DEVICE_MAC})")
    print(f"Platform: {platform.system()}")
    
    if platform.system() != "Linux":
        print("⚠️  This version is optimized for Linux")
    
    print("\n💡 Requirements:")
    print("   - User must be in 'bluetooth' group")
    print("   - Bluetooth service must be running")
    print("   - ESP32 should be paired/bonded")
    print("-" * 50)
    
    receiver = LinuxBLEReceiver()
    
    try:
        asyncio.run(receiver.run())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main()
