"""
Name: Music Control
Description: Play/pause music from any open music player
Icon: 🎵
Color: #DDA0DD
Activation: On Press
"""

import platform
import subprocess
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
    """Main music control function - play/pause any open music player"""
    system = platform.system()
    
    try:
        if system == "Windows":
            safe_print("Music: Sending play/pause command...")
            
            try:
                # Method 1: Use virtual key codes for media keys via PowerShell
                powershell_cmd = [
                    "powershell", 
                    "-Command", 
                    """
                    Add-Type -TypeDefinition '
                    using System;
                    using System.Runtime.InteropServices;
                    public class MediaKeys {
                        [DllImport("user32.dll")]
                        public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
                        public static void SendMediaPlayPause() {
                            keybd_event(0xB3, 0, 0, UIntPtr.Zero);
                            keybd_event(0xB3, 0, 2, UIntPtr.Zero);
                        }
                    }';
                    [MediaKeys]::SendMediaPlayPause()
                    """
                ]
                subprocess.run(powershell_cmd, timeout=10)
                safe_print("SUCCESS: Play/pause command sent via PowerShell virtual keys")
                return
                
            except Exception as e:
                safe_print(f"PowerShell virtual key method failed: {e}")
            
            try:
                # Method 2: Use nircmd if available (lightweight utility)
                subprocess.run(["nircmd", "sendkeypress", "media_play_pause"], timeout=3)
                safe_print("SUCCESS: Play/pause command sent via nircmd")
                return
                
            except FileNotFoundError:
                safe_print("INFO: nircmd not found (optional utility)")
            except Exception as e:
                safe_print(f"nircmd method failed: {e}")
            
            try:
                # Method 3: Try space bar fallback (works with most media players)
                powershell_fallback = [
                    "powershell", 
                    "-Command", 
                    """
                    # Find media player processes
                    $players = Get-Process | Where-Object {$_.ProcessName -match 'spotify|musicbee|foobar|winamp|vlc|wmplayer|itunes|chrome|firefox|edge'} | Select-Object -First 1
                    if ($players) {
                        Add-Type -AssemblyName System.Windows.Forms
                        [System.Windows.Forms.SendKeys]::SendWait(' ')
                        Write-Host 'Space key sent to control media'
                    } else {
                        Write-Host 'No media player found'
                    }
                    """
                ]
                result = subprocess.run(powershell_fallback, capture_output=True, text=True, timeout=5)
                if "Space key sent" in result.stdout:
                    safe_print("SUCCESS: Space bar sent to control media")
                    return
                else:
                    safe_print("INFO: No active media player found")
                
            except Exception as e:
                safe_print(f"Space bar fallback method failed: {e}")
            
            # If all Windows methods fail
            safe_print("ERROR: Could not send play/pause command")
            safe_print("TIP: Try pressing the spacebar in your music player")
            safe_print("TIP: Or use media keys on your keyboard")
            
        elif system == "Linux":
            safe_print("Music: Sending play/pause command...")
            
            try:
                # Method 1: Use playerctl (most reliable for Linux)
                subprocess.run(["playerctl", "play-pause"], timeout=5)
                safe_print("SUCCESS: Play/pause command sent via playerctl")
                return
                
            except FileNotFoundError:
                safe_print("INFO: playerctl not found, trying alternative methods...")
            except Exception as e:
                safe_print(f"playerctl method failed: {e}")
            
            try:
                # Method 2: Use dbus to control media players
                subprocess.run([
                    "dbus-send", 
                    "--type=method_call", 
                    "--dest=org.mpris.MediaPlayer2.spotify",
                    "/org/mpris/MediaPlayer2", 
                    "org.mpris.MediaPlayer2.Player.PlayPause"
                ], timeout=5)
                safe_print("SUCCESS: Play/pause sent to Spotify via dbus")
                return
                
            except Exception as e:
                safe_print(f"dbus Spotify method failed: {e}")
            
            try:
                # Method 3: Try XDoTool to send spacebar (universal play/pause)
                subprocess.run(["xdotool", "key", "space"], timeout=3)
                safe_print("SUCCESS: Spacebar sent via xdotool")
                safe_print("INFO: This works if music player window is focused")
                return
                
            except FileNotFoundError:
                safe_print("INFO: xdotool not found")
            except Exception as e:
                safe_print(f"xdotool method failed: {e}")
            
            # Installation suggestions for Linux
            safe_print("TIP: Install playerctl for better music control:")
            safe_print("     Ubuntu/Debian: sudo apt install playerctl")
            safe_print("     Fedora: sudo dnf install playerctl")
            safe_print("     Arch: sudo pacman -S playerctl")
            
        elif system == "Darwin":  # macOS
            safe_print("Music: Sending play/pause command...")
            
            try:
                # Method 1: Use AppleScript to control music
                applescript_cmd = [
                    "osascript", 
                    "-e", 
                    'tell application "Music" to playpause'
                ]
                subprocess.run(applescript_cmd, timeout=5)
                safe_print("SUCCESS: Play/pause sent to Apple Music")
                return
                
            except Exception as e:
                safe_print(f"Apple Music control failed: {e}")
            
            try:
                # Method 2: Try Spotify control
                applescript_cmd = [
                    "osascript", 
                    "-e", 
                    'tell application "Spotify" to playpause'
                ]
                subprocess.run(applescript_cmd, timeout=5)
                safe_print("SUCCESS: Play/pause sent to Spotify")
                return
                
            except Exception as e:
                safe_print(f"Spotify control failed: {e}")
            
            try:
                # Method 3: Use system media keys
                subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 16'], timeout=3)
                safe_print("SUCCESS: Media key sent via System Events")
                return
                
            except Exception as e:
                safe_print(f"System Events method failed: {e}")
            
            safe_print("TIP: Make sure your music app (Music, Spotify, etc.) is running")
            
        else:
            safe_print(f"ERROR: Unsupported operating system: {system}")
            safe_print("INFO: Try pressing spacebar in your music player")
            
    except Exception as e:
        safe_print(f"ERROR: Unexpected error controlling music: {e}")
        safe_print("TIP: Try manually pressing spacebar in your music player")

if __name__ == "__main__":
    main()
