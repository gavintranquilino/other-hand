"""
Name: Screenshot
Description: Takes a screenshot of the screen
Icon: 📷
Color: #32CD32
Activate: On Press
"""

import subprocess
import platform
import os
import sys
import datetime

# ============ CONFIGURATION ============
SCREENSHOT_DIR = "screenshots"  # Directory to save screenshots
SCREENSHOT_FORMAT = "png"       # File format: png, jpg, bmp
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"  # Timestamp format for filename
# ======================================

def get_screenshot_path():
    """Get the path where screenshots should be saved."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    screenshot_dir = os.path.join(script_dir, SCREENSHOT_DIR)
    
    # Create screenshots directory if it doesn't exist
    if not os.path.exists(screenshot_dir):
        os.makedirs(screenshot_dir)
    
    # Generate filename with timestamp
    timestamp = datetime.datetime.now().strftime(TIMESTAMP_FORMAT)
    filename = f"screenshot_{timestamp}.{SCREENSHOT_FORMAT}"
    
    return os.path.join(screenshot_dir, filename)

def screenshot_windows():
    """Take screenshot on Windows using multiple methods."""
    screenshot_path = get_screenshot_path()
    
    methods = [
        # Method 1: PowerShell with .NET
        lambda: subprocess.run([
            "powershell", "-Command",
            f"Add-Type -AssemblyName System.Drawing; "
            f"Add-Type -AssemblyName System.Windows.Forms; "
            f"$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; "
            f"$bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height; "
            f"$graphics = [System.Drawing.Graphics]::FromImage($bitmap); "
            f"$graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size); "
            f"$bitmap.Save('{screenshot_path}', [System.Drawing.Imaging.ImageFormat]::{SCREENSHOT_FORMAT.upper()}); "
            f"$graphics.Dispose(); $bitmap.Dispose()"
        ], capture_output=True),
        
        # Method 2: Use Windows built-in snippingtool
        lambda: subprocess.run([
            "powershell", "-Command",
            f"Start-Process -FilePath 'ms-screenclip:' -Wait; "
            f"Start-Sleep -Seconds 2"
        ], capture_output=True),
        
        # Method 3: Use nircmd if available
        lambda: subprocess.run([
            "nircmd", "savescreenshot", screenshot_path
        ], capture_output=True),
    ]
    
    for method in methods:
        try:
            result = method()
            if result.returncode == 0 and os.path.exists(screenshot_path):
                return screenshot_path
        except Exception:
            continue
    
    return None

def screenshot_macos():
    """Take screenshot on macOS."""
    screenshot_path = get_screenshot_path()
    
    methods = [
        # Method 1: Use screencapture (built-in)
        lambda: subprocess.run([
            "screencapture", "-x", screenshot_path
        ], capture_output=True),
        
        # Method 2: Use screencapture with different options
        lambda: subprocess.run([
            "screencapture", "-T", "0", screenshot_path
        ], capture_output=True),
        
        # Method 3: AppleScript approach
        lambda: subprocess.run([
            "osascript", "-e",
            f"do shell script \"screencapture '{screenshot_path}'\""
        ], capture_output=True),
    ]
    
    for method in methods:
        try:
            result = method()
            if result.returncode == 0 and os.path.exists(screenshot_path):
                return screenshot_path
        except Exception:
            continue
    
    return None

def screenshot_linux():
    """Take screenshot on Linux using available tools."""
    screenshot_path = get_screenshot_path()
    
    methods = [
        # Method 1: scrot
        lambda: subprocess.run([
            "scrot", screenshot_path
        ], capture_output=True),
        
        # Method 2: gnome-screenshot
        lambda: subprocess.run([
            "gnome-screenshot", "-f", screenshot_path
        ], capture_output=True),
        
        # Method 3: import (ImageMagick)
        lambda: subprocess.run([
            "import", "-window", "root", screenshot_path
        ], capture_output=True),
        
        # Method 4: xwd + convert
        lambda: subprocess.run([
            "sh", "-c", f"xwd -root | convert xwd:- '{screenshot_path}'"
        ], capture_output=True),
        
        # Method 5: maim
        lambda: subprocess.run([
            "maim", screenshot_path
        ], capture_output=True),
        
        # Method 6: spectacle (KDE)
        lambda: subprocess.run([
            "spectacle", "-b", "-o", screenshot_path
        ], capture_output=True),
    ]
    
    for method in methods:
        try:
            result = method()
            if result.returncode == 0 and os.path.exists(screenshot_path):
                return screenshot_path
        except Exception:
            continue
    
    return None

def screenshot_pillow():
    """Take screenshot using Pillow/PIL if available."""
    try:
        from PIL import ImageGrab
        screenshot_path = get_screenshot_path()
        
        # Take screenshot
        screenshot = ImageGrab.grab()
        screenshot.save(screenshot_path)
        
        if os.path.exists(screenshot_path):
            return screenshot_path
    except ImportError:
        return None
    except Exception:
        return None
    
    return None

def screenshot_pyautogui():
    """Take screenshot using pyautogui if available."""
    try:
        import pyautogui
        screenshot_path = get_screenshot_path()
        
        # Take screenshot
        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_path)
        
        if os.path.exists(screenshot_path):
            return screenshot_path
    except ImportError:
        return None
    except Exception:
        return None
    
    return None

def screenshot_mss():
    """Take screenshot using mss library if available."""
    try:
        import mss
        screenshot_path = get_screenshot_path()
        
        with mss.mss() as sct:
            # Grab the entire screen
            monitor = sct.monitors[0]  # All monitors
            screenshot = sct.grab(monitor)
            
            # Save screenshot
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=screenshot_path)
        
        if os.path.exists(screenshot_path):
            return screenshot_path
    except ImportError:
        return None
    except Exception:
        return None
    
    return None

def take_screenshot():
    """
    Take a screenshot of the screen using multiple fallback methods.
    Returns the path to the saved screenshot or None if failed.
    """
    # Try cross-platform libraries first (most reliable)
    methods = [
        screenshot_pyautogui,
        screenshot_pillow,
        screenshot_mss,
    ]
    
    # Add OS-specific methods
    system = platform.system().lower()
    if system == "windows":
        methods.append(screenshot_windows)
    elif system == "darwin":  # macOS
        methods.append(screenshot_macos)
    elif system == "linux":
        methods.append(screenshot_linux)
    
    # Try each method until one succeeds
    for method in methods:
        try:
            result = method()
            if result:
                return result
        except Exception:
            continue
    
    return None

def main():
    """Main function to take a screenshot."""
    screenshot_path = take_screenshot()
    return screenshot_path

if __name__ == "__main__":
    main()