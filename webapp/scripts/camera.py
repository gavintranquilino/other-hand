"""
Name: Camera Photo
Description: Takes a photo with the camera if available
Icon: 📸
Color: #FF6347
Activate: On Press
"""

import subprocess
import platform
import os
import sys
import datetime
import time

# ============ CONFIGURATION ============
PHOTO_DIR = "photos"            # Directory to save photos
PHOTO_FORMAT = "jpg"            # File format: jpg, png, bmp
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"  # Timestamp format for filename
CAMERA_INDEX = 0                # Camera index (0 for default camera)
PHOTO_DELAY = 2                 # Delay in seconds before taking photo
# ======================================

def get_photo_path():
    """Get the path where photos should be saved."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    photo_dir = os.path.join(script_dir, PHOTO_DIR)
    
    # Create photos directory if it doesn't exist
    if not os.path.exists(photo_dir):
        os.makedirs(photo_dir)
    
    # Generate filename with timestamp
    timestamp = datetime.datetime.now().strftime(TIMESTAMP_FORMAT)
    filename = f"photo_{timestamp}.{PHOTO_FORMAT}"
    
    return os.path.join(photo_dir, filename)

def camera_opencv():
    """Take photo using OpenCV if available."""
    try:
        import cv2
        photo_path = get_photo_path()
        
        # Initialize camera
        cap = cv2.VideoCapture(CAMERA_INDEX)
        
        if not cap.isOpened():
            return None
        
        # Set camera properties for better quality
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Give camera time to initialize
        time.sleep(PHOTO_DELAY)
        
        # Take several frames to ensure camera is ready
        for _ in range(5):
            ret, frame = cap.read()
        
        # Take the final photo
        ret, frame = cap.read()
        
        if ret:
            # Save the photo
            cv2.imwrite(photo_path, frame)
            cap.release()
            
            if os.path.exists(photo_path):
                return photo_path
        
        cap.release()
        return None
        
    except ImportError:
        return None
    except Exception:
        return None

def camera_pillow():
    """Take photo using Pillow with ImageGrab (webcam) if available."""
    try:
        from PIL import Image, ImageGrab
        import numpy as np
        
        # This method doesn't directly access camera, but can be used with other tools
        # Mainly kept for compatibility
        return None
        
    except ImportError:
        return None
    except Exception:
        return None

def camera_pygame():
    """Take photo using pygame camera module if available."""
    try:
        import pygame
        import pygame.camera
        photo_path = get_photo_path()
        
        # Initialize pygame camera
        pygame.camera.init()
        
        # Get list of cameras
        cameras = pygame.camera.list_cameras()
        if not cameras:
            return None
        
        # Use first available camera
        camera = pygame.camera.Camera(cameras[CAMERA_INDEX], (640, 480))
        camera.start()
        
        # Give camera time to initialize
        time.sleep(PHOTO_DELAY)
        
        # Take photo
        image = camera.get_image()
        camera.stop()
        
        # Save photo
        pygame.image.save(image, photo_path)
        
        if os.path.exists(photo_path):
            return photo_path
        
        return None
        
    except ImportError:
        return None
    except Exception:
        return None

def camera_windows():
    """Take photo on Windows using multiple methods."""
    photo_path = get_photo_path()
    
    methods = [
        # Method 1: PowerShell with Windows Camera API
        lambda: subprocess.run([
            "powershell", "-Command",
            f"Add-Type -AssemblyName System.Drawing; "
            f"$webcam = New-Object System.Windows.Media.VideoCaptureDevice; "
            f"Start-Sleep -Seconds {PHOTO_DELAY}; "
            f"# This is a simplified approach - actual implementation would need more complex API calls"
        ], capture_output=True),
        
        # Method 2: Use Windows Camera app via URI
        lambda: subprocess.run([
            "powershell", "-Command",
            f"Start-Process 'microsoft.windows.camera:' -Wait"
        ], capture_output=True),
        
        # Method 3: Use fswebcam if available (requires installation)
        lambda: subprocess.run([
            "fswebcam", "-r", "1280x720", "--no-banner", photo_path
        ], capture_output=True),
        
        # Method 4: Use ffmpeg if available
        lambda: subprocess.run([
            "ffmpeg", "-f", "dshow", "-i", f"video=\"USB Video Device\"", 
            "-vframes", "1", "-y", photo_path
        ], capture_output=True),
    ]
    
    for method in methods:
        try:
            result = method()
            if result.returncode == 0 and os.path.exists(photo_path):
                return photo_path
        except Exception:
            continue
    
    return None

def camera_macos():
    """Take photo on macOS using built-in tools."""
    photo_path = get_photo_path()
    
    methods = [
        # Method 1: Use imagesnap (needs to be installed: brew install imagesnap)
        lambda: subprocess.run([
            "imagesnap", photo_path
        ], capture_output=True),
        
        # Method 2: Use ffmpeg
        lambda: subprocess.run([
            "ffmpeg", "-f", "avfoundation", "-i", "0", "-vframes", "1", "-y", photo_path
        ], capture_output=True),
        
        # Method 3: AppleScript to trigger Photo Booth
        lambda: subprocess.run([
            "osascript", "-e",
            'tell application "Photo Booth" to activate'
        ], capture_output=True),
    ]
    
    for method in methods:
        try:
            result = method()
            if result.returncode == 0 and os.path.exists(photo_path):
                return photo_path
        except Exception:
            continue
    
    return None

def camera_linux():
    """Take photo on Linux using available tools."""
    photo_path = get_photo_path()
    
    methods = [
        # Method 1: fswebcam
        lambda: subprocess.run([
            "fswebcam", "-r", "1280x720", "--no-banner", photo_path
        ], capture_output=True),
        
        # Method 2: ffmpeg
        lambda: subprocess.run([
            "ffmpeg", "-f", "v4l2", "-i", "/dev/video0", "-vframes", "1", "-y", photo_path
        ], capture_output=True),
        
        # Method 3: streamer
        lambda: subprocess.run([
            "streamer", "-f", "jpeg", "-o", photo_path
        ], capture_output=True),
        
        # Method 4: mplayer
        lambda: subprocess.run([
            "mplayer", "tv://", "-vo", f"jpeg:outdir={os.path.dirname(photo_path)}", 
            "-frames", "1"
        ], capture_output=True),
        
        # Method 5: guvcview
        lambda: subprocess.run([
            "guvcview", "--image", photo_path, "--exit_on_close"
        ], capture_output=True),
    ]
    
    for method in methods:
        try:
            result = method()
            if result.returncode == 0 and os.path.exists(photo_path):
                return photo_path
        except Exception:
            continue
    
    return None

def check_camera_availability():
    """Check if a camera is available on the system."""
    try:
        import cv2
        cap = cv2.VideoCapture(CAMERA_INDEX)
        if cap.isOpened():
            cap.release()
            return True
        return False
    except ImportError:
        # If OpenCV not available, assume camera might be available
        return True
    except Exception:
        return False

def take_photo():
    """
    Take a photo with the camera using multiple fallback methods.
    Returns the path to the saved photo or None if failed.
    """
    # Check if camera is available
    if not check_camera_availability():
        return None
    
    # Try cross-platform libraries first (most reliable)
    methods = [
        camera_opencv,
        camera_pygame,
        camera_pillow,
    ]
    
    # Add OS-specific methods
    system = platform.system().lower()
    if system == "windows":
        methods.append(camera_windows)
    elif system == "darwin":  # macOS
        methods.append(camera_macos)
    elif system == "linux":
        methods.append(camera_linux)
    
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
    """Main function to take a photo with the camera."""
    photo_path = take_photo()
    return photo_path

if __name__ == "__main__":
    main()