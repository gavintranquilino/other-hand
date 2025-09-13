"""
Name: LinkedIn Opener
Description: Opens LinkedIn in your default browser
Icon: 💼
"""

import webbrowser

def main():
    """Open LinkedIn in the default browser"""
    linkedin_url = "https://www.linkedin.com"
    
    try:
        # Use webbrowser module - works on all platforms!
        webbrowser.open(linkedin_url)
        print("yay")
        
    except Exception as e:
        print(f"❌ Could not open LinkedIn: {e}")

if __name__ == "__main__":
    main()