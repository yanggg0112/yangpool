#!/usr/bin/env python3

import pigpio
import time
import sys
import signal

# Initialize pigpio
pi = pigpio.pi()
if not pi.connected:
    print("Failed to connect to pigpio daemon!")
    exit(1)

# Define GPIO pins - revised to avoid conflicts with XSHUT_PINS [6, 13, 19, 26]
ESC1_M1 = 21
ESC1_M2 = 20
ESC2_M1 = 1  
ESC2_M2 = 12  

# Setup GPIO pins as outputs
pi.set_mode(ESC1_M1, pigpio.OUTPUT)
pi.set_mode(ESC1_M2, pigpio.OUTPUT)
pi.set_mode(ESC2_M1, pigpio.OUTPUT)
pi.set_mode(ESC2_M2, pigpio.OUTPUT)

# Initialize PWM
pi.set_PWM_frequency(ESC1_M1, 50)  # 50 Hz frequency
pi.set_PWM_frequency(ESC1_M2, 50)
pi.set_PWM_frequency(ESC2_M1, 50)
pi.set_PWM_frequency(ESC2_M2, 50)

pi.set_PWM_range(ESC1_M1, 2000)  # Set PWM range to 0-2000
pi.set_PWM_range(ESC1_M2, 2000)
pi.set_PWM_range(ESC2_M1, 2000)
pi.set_PWM_range(ESC2_M2, 2000)

# Initialize motors at 0
pi.set_PWM_dutycycle(ESC1_M1, 0)
pi.set_PWM_dutycycle(ESC1_M2, 0)
pi.set_PWM_dutycycle(ESC2_M1, 0)
pi.set_PWM_dutycycle(ESC2_M2, 0)

def cleanup():
    """Stop all motors and cleanup GPIO"""
    print("\nStopping motors and cleaning up...")
    pi.set_PWM_dutycycle(ESC1_M1, 0)
    pi.set_PWM_dutycycle(ESC1_M2, 0)
    pi.set_PWM_dutycycle(ESC2_M1, 0)
    pi.set_PWM_dutycycle(ESC2_M2, 0)
    pi.stop()

# Register signal handlers for clean shutdown
def signal_handler(sig, frame):
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def motor_fwd(direction, speed=0.2):
    """Move robot in specified direction at given speed
    
    Args:
        direction: 'N','S','E','W','X' (X = stop)
        speed: 0.0-1.0 (as a fraction of max speed)
    """
    speed = min(max(speed, 0.0), 1.0)  # Clamp speed between 0 and 1
    
    # Convert speed to PWM value (base 150 + offset up to 50)
    pwm_value = int(50 * speed) + 150
    
    print(f"Moving {direction} at {speed:.2f} speed (PWM: {pwm_value})")
    
    if direction == 'N':
        pi.set_PWM_dutycycle(ESC2_M1, pwm_value)
        pi.set_PWM_dutycycle(ESC2_M2, 150)
        pi.set_PWM_dutycycle(ESC1_M1, 0)
        pi.set_PWM_dutycycle(ESC1_M2, 0)
    elif direction == 'S':
        pi.set_PWM_dutycycle(ESC2_M1, -int(50 * speed) + 150)
        pi.set_PWM_dutycycle(ESC2_M2, 150)
        pi.set_PWM_dutycycle(ESC1_M1, 0)
        pi.set_PWM_dutycycle(ESC1_M2, 0)
    elif direction == 'E':
        pi.set_PWM_dutycycle(ESC1_M1, pwm_value)
        pi.set_PWM_dutycycle(ESC1_M2, 150)
        pi.set_PWM_dutycycle(ESC2_M1, 0)
        pi.set_PWM_dutycycle(ESC2_M2, 0)
    elif direction == 'W':
        pi.set_PWM_dutycycle(ESC1_M1, -int(50 * speed) + 150)
        pi.set_PWM_dutycycle(ESC1_M2, 150)
        pi.set_PWM_dutycycle(ESC2_M1, 0)
        pi.set_PWM_dutycycle(ESC2_M2, 0)
    elif direction == 'X':
        pi.set_PWM_dutycycle(ESC1_M1, 0)
        pi.set_PWM_dutycycle(ESC1_M2, 0)
        pi.set_PWM_dutycycle(ESC2_M1, 0)
        pi.set_PWM_dutycycle(ESC2_M2, 0)

def motor_spin(rotate, speed=0.2):
    """Rotate robot clockwise or counter-clockwise
    
    Args:
        rotate: positive value for CW, negative for CCW
        speed: 0.0-1.0 (as a fraction of max rotation speed)
    """
    speed = min(max(speed, 0.0), 1.0)  # Clamp speed between 0 and 1
    offset = int(7 * speed)  # Scale the offset based on speed
    
    if rotate > 0:
        print(f"Rotating CW at {speed:.2f} speed")
        pi.set_PWM_dutycycle(ESC1_M1, 150)
        pi.set_PWM_dutycycle(ESC1_M2, 150 + offset)
        pi.set_PWM_dutycycle(ESC2_M1, 150)
        pi.set_PWM_dutycycle(ESC2_M2, 150 - offset)
    else:
        print(f"Rotating CCW at {speed:.2f} speed")
        pi.set_PWM_dutycycle(ESC1_M1, 150)
        pi.set_PWM_dutycycle(ESC1_M2, 150 - offset)
        pi.set_PWM_dutycycle(ESC2_M1, 150)
        pi.set_PWM_dutycycle(ESC2_M2, 150 + offset)

def get_duty_cycle(pin):
    """Get current duty cycle for a pin"""
    duty_cycle = pi.get_PWM_dutycycle(pin)
    return duty_cycle

def display_help():
    """Display help menu"""
    print("\nMotor Control Commands:")
    print("  N [speed] - Move North (forward) at optional speed (0.0-1.0)")
    print("  S [speed] - Move South (backward) at optional speed (0.0-1.0)")
    print("  E [speed] - Move East (right) at optional speed (0.0-1.0)")
    print("  W [speed] - Move West (left) at optional speed (0.0-1.0)")
    print("  CW [speed] - Rotate clockwise at optional speed (0.0-1.0)")
    print("  CCW [speed] - Rotate counter-clockwise at optional speed (0.0-1.0)")
    print("  X - Stop all motors")
    print("  T [seconds] - Run previous command for specified seconds, then stop")
    print("  STATUS - Display current motor settings")
    print("  HELP - Display this help menu")
    print("  QUIT - Exit program")
    print("\nExamples:")
    print("  N 0.5   - Move forward at half speed")
    print("  CW 0.7  - Rotate clockwise at 70% speed")
    print("  N       - Move forward at default speed (0.2)")
    print("  N 0.8 T 2.5  - Move forward at 80% speed for 2.5 seconds")

def show_status():
    """Display current status of all motors"""
    print("\nCurrent Motor Settings:")
    print(f"  ESC1_M1 (pin {ESC1_M1}): {get_duty_cycle(ESC1_M1)}")
    print(f"  ESC1_M2 (pin {ESC1_M2}): {get_duty_cycle(ESC1_M2)}")
    print(f"  ESC2_M1 (pin {ESC2_M1}): {get_duty_cycle(ESC2_M1)}")
    print(f"  ESC2_M2 (pin {ESC2_M2}): {get_duty_cycle(ESC2_M2)}")

def main():
    """Main command loop"""
    print("Motor Control Interface")
    print("Type 'HELP' for a list of commands or 'QUIT' to exit")
    
    last_command = None
    last_speed = 0.2
    
    while True:
        try:
            # Get command from user
            command_input = input("\nEnter command: ").strip().upper()
            if not command_input:
                continue
                
            # Parse the command
            parts = command_input.split()
            command = parts[0]
            
            # Process the command
            if command == "QUIT" or command == "EXIT":
                break
                
            elif command == "HELP":
                display_help()
                
            elif command == "STATUS":
                show_status()
                
            elif command == "N" or command == "S" or command == "E" or command == "W":
                # Extract speed if provided
                speed = last_speed
                if len(parts) > 1 and parts[1] != "T":
                    try:
                        speed = float(parts[1])
                    except ValueError:
                        print(f"Invalid speed value: {parts[1]}")
                        continue
                
                motor_fwd(command, speed)
                last_command = (motor_fwd, command, speed)
                last_speed = speed
                
                # Check for timed operation
                if "T" in parts:
                    try:
                        t_index = parts.index("T")
                        if t_index + 1 < len(parts):
                            duration = float(parts[t_index + 1])
                            print(f"Running for {duration} seconds...")
                            time.sleep(duration)
                            motor_fwd("X")
                    except (ValueError, IndexError):
                        print("Invalid time format. Use 'T seconds'")
                
            elif command == "X":
                motor_fwd("X")
                
            elif command == "CW":
                # Extract speed if provided
                speed = last_speed
                if len(parts) > 1 and parts[1] != "T":
                    try:
                        speed = float(parts[1])
                    except ValueError:
                        print(f"Invalid speed value: {parts[1]}")
                        continue
                
                motor_spin(1, speed)
                last_command = (motor_spin, 1, speed)
                last_speed = speed
                
                # Check for timed operation
                if "T" in parts:
                    try:
                        t_index = parts.index("T")
                        if t_index + 1 < len(parts):
                            duration = float(parts[t_index + 1])
                            print(f"Running for {duration} seconds...")
                            time.sleep(duration)
                            motor_fwd("X")
                    except (ValueError, IndexError):
                        print("Invalid time format. Use 'T seconds'")
                
            elif command == "CCW":
                # Extract speed if provided
                speed = last_speed
                if len(parts) > 1 and parts[1] != "T":
                    try:
                        speed = float(parts[1])
                    except ValueError:
                        print(f"Invalid speed value: {parts[1]}")
                        continue
                
                motor_spin(-1, speed)
                last_command = (motor_spin, -1, speed)
                last_speed = speed
                
                # Check for timed operation
                if "T" in parts:
                    try:
                        t_index = parts.index("T")
                        if t_index + 1 < len(parts):
                            duration = float(parts[t_index + 1])
                            print(f"Running for {duration} seconds...")
                            time.sleep(duration)
                            motor_fwd("X")
                    except (ValueError, IndexError):
                        print("Invalid time format. Use 'T seconds'")
                
            elif command == "REPEAT" or command == "R":
                if last_command:
                    func, *args = last_command
                    func(*args)
                else:
                    print("No previous command to repeat")
                    
            else:
                print(f"Unknown command: {command}")
                display_help()
                
        except KeyboardInterrupt:
            print("\nOperation cancelled")
            motor_fwd("X")
        except Exception as e:
            print(f"Error: {e}")
            
    # Clean up when done
    cleanup()
    print("Exiting motor control interface")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Unexpected error: {e}")
        cleanup()