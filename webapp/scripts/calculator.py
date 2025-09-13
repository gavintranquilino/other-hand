"""
Name: Calculator
Description: Perform basic mathematical calculations.
Icon: 🧮
"""

import random

def main():
    """Main calculator function"""
    # Generate a random math problem
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
    
    print(f"🧮 Calculator")
    print(f"   {num1} {op} {num2} = {result}")

if __name__ == "__main__":
    main()
