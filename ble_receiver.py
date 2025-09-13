#!/usr/bin/env python3
"""
BLE Receiver Script for ESP32 "Other Hand HTN25"
Connects to the ESP32 and receives encoder position data when button is pressed.
"""

import asyncio
import sys
from bleak import BleakClient, BleakScanner
import logging

# ESP32 BLE Configuration (from your Arduino code)
DEVICE_NAME = "Other Hand HTN25"
DEVICE_MAC = "d8:3b:da:75:11:fd"  # Your ESP32's MAC address
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"

# Enable logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def notification_handler(sender, data):
    """Handle incoming BLE notifications from ESP32"""
    try:
        # Decode the received data
        message = data.decode('utf-8')
        print(f"📡 Received from ESP32: {message}")
        print(f"📡 Raw data: {data}")
        print("-" * 50)
    except Exception as e:
        print(f"❌ Error decoding data: {e}")
        print(f"📡 Raw bytes: {data}")

def disconnect_handler(client):
    """Handle BLE disconnection events"""
    print("🔌 Device disconnected!")
    print("⚠️  Connection lost to ESP32")
    return True  # Return True to indicate we want to handle the disconnect

async def find_device():
    """Scan for the ESP32 device"""
    print("🔍 Scanning for ESP32 device...")
    
    devices = await BleakScanner.discover(timeout=10.0)
    
    # Look for device by name or MAC address
    target_device = None
    for device in devices:
        if (device.name == DEVICE_NAME or 
            device.address.lower() == DEVICE_MAC.lower()):
            target_device = device
            break
    
    if target_device:
        print(f"✅ Found device: {target_device.name} ({target_device.address})")
        return target_device
    else:
        print(f"❌ Device '{DEVICE_NAME}' not found!")
        print("\n📋 Available devices:")
        for device in devices:
            print(f"  - {device.name} ({device.address})")
        return None

async def connect_and_receive():
    """Main function to connect to ESP32 and receive data with auto-reconnect"""
    
    while True:  # Infinite reconnection loop
        try:
            # Find the device
            device = await find_device()
            if not device:
                print("⏳ Device not found, retrying in 5 seconds...")
                await asyncio.sleep(5)
                continue
            
            # Connect to the device
            print(f"🔗 Connecting to {device.address}...")
            
            async with BleakClient(device.address, disconnected_callback=disconnect_handler) as client:
                print(f"✅ Connected to {device.name}!")
                
                # Check connection status
                if not client.is_connected:
                    print("❌ Connection failed!")
                    await asyncio.sleep(3)
                    continue
                
                # Check if the service exists
                services = client.services
                service_found = False
                
                for service in services:
                    if service.uuid.lower() == SERVICE_UUID.lower():
                        service_found = True
                        print(f"✅ Found service: {service.uuid}")
                        break
                
                if not service_found:
                    print(f"❌ Service {SERVICE_UUID} not found!")
                    await asyncio.sleep(3)
                    continue
                
                # Subscribe to notifications from the characteristic
                print(f"📡 Subscribing to notifications...")
                await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
                print(f"✅ Subscribed to characteristic: {CHARACTERISTIC_UUID}")
                
                print("\n🎯 Ready to receive data! Press the button on your ESP32...")
                print("Press Ctrl+C to stop\n")
                
                # Keep the connection alive and listen for notifications
                try:
                    while client.is_connected:
                        await asyncio.sleep(1)
                        
                        # Check connection status periodically
                        if not client.is_connected:
                            print("⚠️  Connection lost during operation!")
                            break
                            
                except KeyboardInterrupt:
                    print("\n🛑 Stopping...")
                    return  # Exit the reconnection loop on Ctrl+C
                    
                finally:
                    # Unsubscribe from notifications if still connected
                    if client.is_connected:
                        try:
                            await client.stop_notify(CHARACTERISTIC_UUID)
                            print("✅ Unsubscribed from notifications")
                        except Exception as e:
                            print(f"⚠️  Error unsubscribing: {e}")
                    print("✅ Disconnected cleanly")
                    
        except KeyboardInterrupt:
            print("\n🛑 User requested stop")
            break
        except Exception as e:
            print(f"❌ Connection error: {e}")
            if "disconnected" in str(e).lower() or "connection" in str(e).lower():
                print("🔄 Device disconnected unexpectedly")
        
        # Wait before attempting reconnection
        print("🔄 Attempting reconnection in 3 seconds...")
        await asyncio.sleep(3)

def main():
    """Entry point"""
    print("🚀 ESP32 BLE Receiver Starting...")
    print(f"🎯 Looking for device: {DEVICE_NAME}")
    print(f"📍 MAC Address: {DEVICE_MAC}")
    print("-" * 50)
    
    try:
        asyncio.run(connect_and_receive())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()