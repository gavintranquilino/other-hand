"""
Name: Weather Check
Description: Check and display current weather information.
Icon: 🌤️
"""

import random

def main():
    """Main weather function"""
    # Simulate weather data (in real implementation, would fetch from API)
    conditions = ["Sunny", "Cloudy", "Rainy", "Partly Cloudy", "Snow"]
    temperatures = [15, 20, 25, 30, 18]
    
    condition = random.choice(conditions)
    temp = random.choice(temperatures)
    
    print(f"Current Weather: {condition}")
    print(f"Temperature: {temp}°C")
    print("Have a great day!")

if __name__ == "__main__":
    main()
