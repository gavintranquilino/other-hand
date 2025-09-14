"""
Name: Bruh
Description: Plays the Bruh Sound
Icon: 🤦‍♂️
Color: #FFFF33
Activate: On Press
"""

import subprocess
import platform
import os
import sys

# ============ CONFIGURATION ============
SOUND_FILE = "bruh.mp3"  # Change this to any sound file in the sounds/ directory
# Available sounds: boom.mp3, bruh.mp3, clash.mp3, danger.mp3, goose.mp3, 
#                   this is rocket leauge.mp3, wrong.mp3, y2mate_rQlfs1Y.mp3
# ======================================

def get_sound_path():
    """Get the absolute path to the configured sound file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sound_path = os.path.join(script_dir, "sounds", SOUND_FILE)
    
    if os.path.exists(sound_path):
        return sound_path
    else:
        return None

def play_sound_windows(sound_path):
    """Play sound on Windows using multiple methods."""
    methods = [
        # Method 1: PowerShell with Windows Media Player
        lambda: subprocess.run([
            "powershell", "-Command",
            f"Add-Type -AssemblyName presentationCore; "
            f"$mediaPlayer = New-Object system.windows.media.mediaplayer; "
            f"$mediaPlayer.open([uri]'{sound_path}'); "
            f"$mediaPlayer.Play(); "
            f"Start-Sleep -Seconds 2"
        ], timeout=10),
        
        # Method 2: Use Windows Media Player directly
        lambda: subprocess.run(["wmplayer", "/play", "/close", sound_path], timeout=10),
        
        # Method 3: PowerShell with SoundPlayer
        lambda: subprocess.run([
            "powershell", "-Command",
            f"[console]::beep(800,500); "
            f"Add-Type -AssemblyName System.Windows.Forms; "
            f"$sound = New-Object System.Media.SoundPlayer('{sound_path}'); "
            f"$sound.PlaySync()"
        ], timeout=10),
        
        # Method 4: Use default associated program
        lambda: subprocess.run(["start", "/min", sound_path], shell=True, timeout=10)
    ]
    
    for i, method in enumerate(methods, 1):
        try:
            method()
            return True
        except Exception as e:
            continue
    
    return False

def play_sound_macos(sound_path):
    """Play sound on macOS."""
    methods = [
        # Method 1: Use afplay (built-in)
        lambda: subprocess.run(["afplay", sound_path], timeout=10),
        
        # Method 2: Use open with default application
        lambda: subprocess.run(["open", sound_path], timeout=10),
        
        # Method 3: Use QuickTime Player
        lambda: subprocess.run(["open", "-a", "QuickTime Player", sound_path], timeout=10)
    ]
    
    for i, method in enumerate(methods, 1):
        try:
            method()
            return True
        except Exception as e:
            continue
    
    return False

def play_sound_linux(sound_path):
    """Play sound on Linux using available players."""
    # Common Linux audio players in order of preference
    players = [
        ["paplay", sound_path],           # PulseAudio
        ["aplay", sound_path],            # ALSA
        ["mpg123", sound_path],           # MP3 player
        ["mpv", "--no-video", sound_path], # mpv
        ["vlc", "--intf", "dummy", "--play-and-exit", sound_path], # VLC
        ["mplayer", "-really-quiet", sound_path], # MPlayer
        ["ffplay", "-nodisp", "-autoexit", sound_path], # FFmpeg
        ["cvlc", "--play-and-exit", sound_path], # VLC command line
        ["xdg-open", sound_path]          # Default application
    ]
    
    for player_cmd in players:
        try:
            result = subprocess.run(player_cmd, timeout=10, capture_output=True)
            if result.returncode == 0:
                return True
        except FileNotFoundError:
            continue
        except Exception as e:
            continue
    
    return False

def play_boom_sound():
    """Play the configured sound file."""
    sound_path = get_sound_path()
    if not sound_path:
        return False
    
    system = platform.system().lower()
    
    try:
        if system == "windows":
            return play_sound_windows(sound_path)
        elif system == "darwin":  # macOS
            return play_sound_macos(sound_path)
        elif system == "linux":
            return play_sound_linux(sound_path)
        else:
            return False
            
    except Exception as e:
        return False

def main():
    """Main function to play the configured sound."""
    play_boom_sound()

if __name__ == "__main__":
    main()