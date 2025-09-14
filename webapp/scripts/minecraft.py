"""
Name: Minecraft Bedrock
Description: Opens Minecraft Bedrock Edition on Windows
Icon: ⛏️
Color: #008F26
Activation: On Press
"""

import platform
import subprocess
import os
import time

def safe_print(message):
    """Print with Windows-safe encoding"""
    try:
        print(message)
    except UnicodeEncodeError:
        # Fallback for Windows console encoding issues
        safe_message = message.encode('ascii', errors='replace').decode('ascii')
        print(safe_message)

def main():
    """Main Minecraft function - opens Minecraft Bedrock Edition"""
    system = platform.system()
    
    if system == "Windows":
        safe_print("Minecraft: Starting Minecraft Bedrock Edition...")
        
        try:
            # Try multiple methods to launch Minecraft Bedrock Edition
            
            # Method 1: Try the Microsoft Store URI protocol
            try:
                safe_print("Attempting to launch via Microsoft Store...")
                # This will open Minecraft Bedrock from Microsoft Store
                subprocess.Popen([
                    "start", 
                    "minecraft://", 
                    "/wait"
                ], shell=True)
                safe_print("SUCCESS: Minecraft launched via Store protocol")
                return
            except Exception as e:
                safe_print(f"Store protocol failed: {e}")
            
            # Method 2: Try PowerShell to launch the app
            try:
                safe_print("Attempting to launch via PowerShell...")
                powershell_command = [
                    "powershell", 
                    "-Command", 
                    "Start-Process 'shell:AppsFolder\\Microsoft.MinecraftUWP_8wekyb3d8bbwe!App'"
                ]
                subprocess.Popen(powershell_command)
                safe_print("SUCCESS: Minecraft launched via PowerShell")
                return
            except Exception as e:
                safe_print(f"PowerShell method failed: {e}")
            
            # Method 3: Try the direct executable path (if installed traditionally)
            try:
                safe_print("Searching for Minecraft executable...")
                
                # Common installation paths
                possible_paths = [
                    os.path.expandvars(r"%LOCALAPPDATA%\Packages\Microsoft.MinecraftUWP_8wekyb3d8bbwe\LocalState\games\com.mojang\minecraftpe\Minecraft.Windows.exe"),
                    os.path.expandvars(r"%PROGRAMFILES%\WindowsApps\Microsoft.MinecraftUWP_*\Minecraft.exe"),
                    os.path.expandvars(r"%PROGRAMFILES(X86)%\Minecraft Launcher\MinecraftLauncher.exe"),
                ]
                
                for path in possible_paths:
                    if "*" in path:
                        # Handle wildcard paths
                        import glob
                        matches = glob.glob(path)
                        if matches:
                            path = matches[0]
                    
                    if os.path.exists(path):
                        safe_print(f"Found Minecraft at: {path}")
                        subprocess.Popen([path])
                        safe_print("SUCCESS: Minecraft launched via executable")
                        return
                        
            except Exception as e:
                safe_print(f"Direct executable method failed: {e}")
            
            # Method 4: Try Windows Run dialog
            try:
                safe_print("Attempting to open via Windows Run dialog...")
                subprocess.Popen(["start", "ms-windows-store://pdp/?productid=9NBLGGH2JHXJ"], shell=True)
                safe_print("INFO: Opened Microsoft Store page for Minecraft")
                safe_print("TIP: Click 'Launch' or 'Install' if not already installed")
                return
            except Exception as e:
                safe_print(f"Windows Run method failed: {e}")
            
            # If all methods fail
            safe_print("ERROR: Could not launch Minecraft Bedrock Edition")
            safe_print("TIP: Make sure Minecraft Bedrock is installed from Microsoft Store")
            safe_print("TIP: You can install it from: https://www.minecraft.net/en-us/store/minecraft-bedrock-edition")
            
        except Exception as e:
            safe_print(f"ERROR: Unexpected error launching Minecraft: {e}")
            
    elif system == "Linux":
        safe_print("INFO: Minecraft Bedrock Edition is not natively available on Linux")
        safe_print("TIP: Consider using Minecraft Java Edition instead")
        safe_print("TIP: Or try MCLauncher for unofficial Bedrock support")
        
    elif system == "Darwin":  # macOS
        safe_print("INFO: Minecraft Bedrock Edition is not natively available on macOS")
        safe_print("TIP: Consider using Minecraft Java Edition instead")
        safe_print("TIP: Bedrock is available on iOS App Store for mobile devices")
        
    else:
        safe_print(f"ERROR: Unsupported operating system: {system}")
        safe_print("INFO: Minecraft Bedrock Edition is primarily available on Windows and mobile platforms")

if __name__ == "__main__":
    main()
