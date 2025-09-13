"""
Name: Timer
Description: A simple countdown timer that displays remaining time.
Icon: ⏲️
"""

import time

def main():
    """Main timer function"""
    duration = 30  # 30 seconds
    
    print(f"Starting {duration}-second timer...")
    
    for remaining in range(duration, 0, -1):
        print(f"Time remaining: {remaining} seconds")
        time.sleep(1)
    
    print("Timer finished!")

if __name__ == "__main__":
    main()
