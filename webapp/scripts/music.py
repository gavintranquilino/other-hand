"""
Name: Music Control
Description: Control music playback (play, pause, next track).
Icon: 🎵
Color: #DDA0DD
"""

import random

def main():
    """Main music control function"""
    actions = ["Play", "Pause", "Next Track", "Previous Track", "Shuffle"]
    songs = ["Song A", "Song B", "Song C", "Song D"]
    
    action = random.choice(actions)
    current_song = random.choice(songs)
    
    print(f"🎵 Music Control: {action}")
    if action in ["Play", "Pause"]:
        print(f"   Current: {current_song}")
    elif "Track" in action:
        print(f"   Now Playing: {current_song}")

if __name__ == "__main__":
    main()
