"""
Name: Lock
Description: Locks the computer
Icon: 🔒
Color: #FFFFFF
Activation: On Press
"""

import subprocess
import platform
import sys

def safe_print(message):
    """Safely print a message, handling encoding issues on Windows."""
    try:
        print(message)
    except UnicodeEncodeError:
        # Fallback for Windows console encoding issues
        print(message.encode('ascii', 'replace').decode('ascii'))

def lock_computer():
    """Lock the computer based on the operating system."""
    system = platform.system().lower()
    
    try:
        if system == "windows":
            lock_windows()
        elif system == "darwin":  # macOS
            lock_macos()
        elif system == "linux":
            lock_linux()
        else:
            safe_print(f"ERROR: Unsupported operating system: {system}")
            return False
        
        return True
        
    except Exception as e:
        safe_print(f"ERROR: Failed to lock computer - {str(e)}")
        return False

def lock_windows():
    """Lock Windows computer using multiple methods."""
    methods = [
        lock_windows_rundll32,
        lock_windows_powershell,
        lock_windows_user32
    ]
    
    for method in methods:
        try:
            if method():
                safe_print("SUCCESS: Computer locked (Windows)")
                return True
        except Exception as e:
            continue
    
    raise Exception("All Windows locking methods failed")

def lock_windows_rundll32():
    """Lock Windows using rundll32."""
    try:
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], timeout=5)
        return True
    except Exception:
        return False

def lock_windows_powershell():
    """Lock Windows using PowerShell."""
    try:
        cmd = [
            "powershell", "-Command",
            """
            Add-Type -TypeDefinition '
            using System;
            using System.Runtime.InteropServices;
            public class LockScreen {
                [DllImport("user32.dll")]
                public static extern bool LockWorkStation();
            }';
            [LockScreen]::LockWorkStation()
            """
        ]
        subprocess.run(cmd, timeout=10)
        return True
    except Exception:
        return False

def lock_windows_user32():
    """Lock Windows using ctypes and user32.dll."""
    try:
        import ctypes
        user32 = ctypes.windll.user32
        user32.LockWorkStation()
        return True
    except Exception:
        return False

def lock_macos():
    """Lock macOS computer."""
    try:
        # Method 1: Use pmset (preferred)
        subprocess.run(["/usr/bin/pmset", "displaysleepnow"], timeout=5)
        safe_print("SUCCESS: Computer locked (macOS - display sleep)")
        return True
    except Exception:
        pass
    
    try:
        # Method 2: Use screensaver with immediate lock
        subprocess.run(["/usr/bin/open", "-a", "ScreenSaverEngine"], timeout=5)
        safe_print("SUCCESS: Screensaver activated (macOS)")
        return True
    except Exception:
        pass
    
    try:
        # Method 3: Use AppleScript
        applescript = """
        tell application "System Events"
            keystroke "q" using {control down, command down}
        end tell
        """
        subprocess.run(["osascript", "-e", applescript], timeout=5)
        safe_print("SUCCESS: Computer locked (macOS - AppleScript)")
        return True
    except Exception:
        pass
    
    raise Exception("All macOS locking methods failed")

def lock_linux():
    """Lock Linux computer using multiple desktop environments."""
    methods = [
        ("loginctl", ["loginctl", "lock-session"]),
        ("gnome-screensaver", ["gnome-screensaver-command", "--lock"]),
        ("xdg-screensaver", ["xdg-screensaver", "lock"]),
        ("i3lock", ["i3lock"]),
        ("slock", ["slock"]),
        ("xlock", ["xlock", "-mode", "blank"]),
        ("dm-tool", ["dm-tool", "lock"]),
        ("xset", ["xset", "s", "activate"])
    ]
    
    for method_name, cmd in methods:
        try:
            result = subprocess.run(cmd, timeout=5, capture_output=True)
            if result.returncode == 0:
                safe_print(f"SUCCESS: Computer locked (Linux - {method_name})")
                return True
        except FileNotFoundError:
            continue
        except Exception:
            continue
    
    # Final fallback: try to activate screensaver
    try:
        subprocess.run(["xset", "dpms", "force", "off"], timeout=3)
        safe_print("SUCCESS: Display turned off (Linux)")
        return True
    except Exception:
        pass
    
    raise Exception("All Linux locking methods failed")

def main():
    """Main function to lock the computer."""
    safe_print("🔒 Attempting to lock computer...")
    
    if lock_computer():
        safe_print("✓ Computer lock command executed successfully")
    else:
        safe_print("✗ Failed to lock computer")
        safe_print("💡 Manual alternatives:")
        system = platform.system().lower()
        if system == "windows":
            safe_print("   - Press Windows + L")
            safe_print("   - Press Ctrl + Alt + Del, then Lock")
        elif system == "darwin":
            safe_print("   - Press Control + Command + Q")
            safe_print("   - Click Apple menu > Lock Screen")
        elif system == "linux":
            safe_print("   - Press Ctrl + Alt + L (most distributions)")
            safe_print("   - Use your desktop environment's lock shortcut")

if __name__ == "__main__":
    main()
