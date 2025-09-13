"""
Name: Quick Note
Description: Display a quick reminder or note message.
Icon: 📝
"""

def main():
    """Main note function"""
    notes = [
        "Remember to drink water!",
        "Take a break every hour",
        "Check your posture",
        "Don't forget lunch",
        "Review your goals for today"
    ]
    
    import random
    note = random.choice(notes)
    
    print("📝 Quick Reminder:")
    print(f"   {note}")

if __name__ == "__main__":
    main()
