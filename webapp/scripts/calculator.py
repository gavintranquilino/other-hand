"""
Name: Calculator
Description: Opens the system calculator application
Icon: 🧮
Color: #ffb347
Activation: On Press
"""

import platform
import subprocess
import os
import sys

def safe_print(message):
    """Print with Windows-safe encoding"""
    try:
        print(message)
    except UnicodeEncodeError:
        # Fallback for Windows console encoding issues
        safe_message = message.encode('ascii', errors='replace').decode('ascii')
        print(safe_message)

def main():
    """Main calculator function - opens system calculator"""
    system = platform.system()
    
    try:
        if system == "Windows":
            # Windows Calculator
            safe_print("Calculator: Opening Windows Calculator...")
            subprocess.Popen(["calc.exe"])
            safe_print("SUCCESS: Windows Calculator opened successfully")
            
        elif system == "Linux":
            # Try common Linux calculators in order of preference
            calculators = [
                "gnome-calculator",  # GNOME Calculator (Ubuntu default)
                "kcalc",            # KDE Calculator
                "galculator",       # Lightweight calculator
                "qalculate-gtk",    # Advanced calculator
                "xcalc",            # X11 calculator (fallback)
                "bc"                # Command-line calculator (last resort)
            ]
            
            safe_print("Calculator: Opening Linux Calculator...")
            calculator_opened = False
            
            for calc in calculators:
                try:
                    # Check if calculator exists
                    result = subprocess.run(["which", calc], 
                                          capture_output=True, 
                                          text=True)
                    if result.returncode == 0:
                        # Calculator found, try to open it
                        if calc == "bc":
                            # bc is command-line, open in terminal
                            subprocess.Popen(["gnome-terminal", "--", "bc", "-l"])
                        else:
                            # GUI calculator
                            subprocess.Popen([calc])
                        
                        safe_print(f"SUCCESS: {calc} opened successfully")
                        calculator_opened = True
                        break
                        
                except Exception as e:
                    continue  # Try next calculator
            
            if not calculator_opened:
                safe_print("ERROR: No calculator application found")
                safe_print("TIP: Try installing: sudo apt install gnome-calculator")
                
        elif system == "Darwin":  # macOS
            safe_print("Calculator: Opening macOS Calculator...")
            subprocess.Popen(["open", "-a", "Calculator"])
            safe_print("SUCCESS: macOS Calculator opened successfully")
            
        else:
            safe_print(f"ERROR: Unsupported operating system: {system}")
            safe_print("INFO: Manual calculation fallback:")
            # Fallback to simple calculation display
            import random
            operations = ["+", "-", "*", "/"]
            num1 = random.randint(1, 100)
            num2 = random.randint(1, 50)
            op = random.choice(operations)
            
            if op == "+":
                result = num1 + num2
            elif op == "-":
                result = num1 - num2
            elif op == "*":
                result = num1 * num2
            else:  # division
                result = round(num1 / num2, 2)
            
            safe_print(f"   {num1} {op} {num2} = {result}")
            
    except Exception as e:
        safe_print(f"ERROR: Error opening calculator: {e}")
        safe_print("TIP: Please install a calculator application")

if __name__ == "__main__":
    main()