"""
Name: Watch RLCS 
Description: Watch the RLCS 2024-2025 World Championships live on Twitch
Icon: ⚽
Color: #FF8400
Activate: On Press
"""

import webbrowser

def main():
    """Open RLCS in the default browser"""
    linkedin_url = "https://www.twitch.tv/rocketleague"
    
    try:
        # Use webbrowser module - works on all platforms!
        webbrowser.open(linkedin_url)
        print("yay")
        
    except Exception as e:
        print(f"❌ Could not open LinkedIn: {e}")

if __name__ == "__main__":
    main()