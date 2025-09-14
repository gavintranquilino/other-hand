"""
Name: Mouse Click
Description: Clicks the mouse at current position
Icon: 🖱️
Color: #4169E1
Activate: On Press
"""

import subprocess
import platform
import os
import sys

def click_mouse_windows():
    """Click mouse on Windows using multiple methods."""
    methods = [
        # Method 1: PowerShell with Windows Forms
        lambda: subprocess.run([
            "powershell", "-Command",
            "Add-Type -AssemblyName System.Windows.Forms; "
            "[System.Windows.Forms.Cursor]::Position = [System.Windows.Forms.Cursor]::Position; "
            "Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; "
            "public class Mouse { "
            "[DllImport(\"user32.dll\")] public static extern void mouse_event(int dwFlags, int dx, int dy, int cButtons, int dwExtraInfo); "
            "}'; "
            "[Mouse]::mouse_event(0x02, 0, 0, 0, 0); Start-Sleep -Milliseconds 50; [Mouse]::mouse_event(0x04, 0, 0, 0, 0)"
        ], capture_output=True),
        
        # Method 2: VBScript via PowerShell
        lambda: subprocess.run([
            "powershell", "-Command",
            "$VBScript = 'Set wshShell = CreateObject(\"WScript.Shell\"): wshShell.SendKeys \"{ENTER}\"'; "
            "echo $VBScript | Out-File -FilePath temp_click.vbs -Encoding ASCII; "
            "cscript //nologo temp_click.vbs; "
            "Remove-Item temp_click.vbs"
        ], capture_output=True),
        
        # Method 3: Use nircmd if available
        lambda: subprocess.run(["nircmd", "sendmouse", "left", "click"], capture_output=True),
    ]
    
    for method in methods:
        try:
            result = method()
            if result.returncode == 0:
                return True
        except Exception:
            continue
    
    return False

def click_mouse_macos():
    """Click mouse on macOS."""
    methods = [
        # Method 1: AppleScript
        lambda: subprocess.run([
            "osascript", "-e", 
            "tell application \"System Events\" to click at (current mouse position)"
        ], capture_output=True),
        
        # Method 2: Alternative AppleScript
        lambda: subprocess.run([
            "osascript", "-e",
            "tell application \"System Events\" to tell process \"System Events\" to click"
        ], capture_output=True),
        
        # Method 3: cliclick if available
        lambda: subprocess.run(["cliclick", "c:."], capture_output=True),
    ]
    
    for method in methods:
        try:
            result = method()
            if result.returncode == 0:
                return True
        except Exception:
            continue
    
    return False

def click_mouse_linux():
    """Click mouse on Linux using available tools."""
    methods = [
        # Method 1: xdotool
        lambda: subprocess.run(["xdotool", "click", "1"], capture_output=True),
        
        # Method 2: xte
        lambda: subprocess.run(["xte", "mouseclick 1"], capture_output=True, shell=True),
        
        # Method 3: wmctrl + xdotool alternative
        lambda: subprocess.run(["sh", "-c", "xdotool mousemove_relative 0 0 click 1"], capture_output=True),
        
        # Method 4: Using X11 directly via python-xlib (if available)
        lambda: click_mouse_linux_xlib(),
    ]
    
    for method in methods:
        try:
            result = method()
            if result and (hasattr(result, 'returncode') and result.returncode == 0 or result is True):
                return True
        except Exception:
            continue
    
    return False

def click_mouse_linux_xlib():
    """Try to click using python Xlib if available."""
    try:
        from Xlib import X, display
        from Xlib.ext import record
        from Xlib.protocol import rq
        
        d = display.Display()
        root = d.screen().root
        
        # Get current mouse position
        pointer = root.query_pointer()
        x, y = pointer.root_x, pointer.root_y
        
        # Simulate mouse click
        root.warp_pointer(x, y)
        d.sync()
        
        # Mouse down
        root.ungrab_pointer(X.CurrentTime)
        fake_input(d, X.ButtonPress, 1)
        d.sync()
        
        # Mouse up
        fake_input(d, X.ButtonRelease, 1)
        d.sync()
        
        return True
    except ImportError:
        return False
    except Exception:
        return False

def fake_input(display, event_type, detail):
    """Helper function for Xlib mouse events."""
    try:
        display.xtest_fake_input(event_type, detail)
    except:
        # Fallback if xtest extension is not available
        pass

def click_mouse_pyautogui():
    """Try to click using pyautogui if available."""
    try:
        import pyautogui
        pyautogui.click()
        return True
    except ImportError:
        return False
    except Exception:
        return False

def click_mouse_pynput():
    """Try to click using pynput if available."""
    try:
        from pynput.mouse import Button, Listener, MouseButton
        from pynput import mouse
        
        # Create mouse controller
        mouse_controller = mouse.Mouse()
        
        # Click at current position
        mouse_controller.click(Button.left, 1)
        return True
    except ImportError:
        return False
    except Exception:
        return False

def click_mouse():
    """
    Click the mouse at the current cursor position.
    Uses multiple fallback methods to ensure compatibility across all systems and Python versions.
    """
    # Try cross-platform libraries first (most reliable)
    methods = [
        click_mouse_pyautogui,
        click_mouse_pynput,
    ]
    
    # Add OS-specific methods
    system = platform.system().lower()
    if system == "windows":
        methods.append(click_mouse_windows)
    elif system == "darwin":  # macOS
        methods.append(click_mouse_macos)
    elif system == "linux":
        methods.append(click_mouse_linux)
    
    # Try each method until one succeeds
    for method in methods:
        try:
            if method():
                return True
        except Exception:
            continue
    
    return False

def main():
    """Main function to perform mouse click."""
    click_mouse()

if __name__ == "__main__":
    main()