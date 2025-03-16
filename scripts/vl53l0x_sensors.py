import time
import board
import busio
import adafruit_vl53l0x
import RPi.GPIO as GPIO
import numpy as np
from collections import deque

# Configuration parameters
XSHUT_PINS = [6, 13, 19, 26]  # GPIO pin numbers for each sensor's XSHUT pin
I2C_ADDRESSES = [0x30, 0x31, 0x32, 0x33]  # Non-conflicting addresses
SAMPLE_SIZE = 5  # Number of readings to average
READ_FREQUENCY = 0.05  # Time between readings in seconds (50ms)
TIMEOUT_VALUE = 1000  # Value to use when sensor times out or reads above range

# Setup GPIO
GPIO.setmode(GPIO.BCM)
for pin in XSHUT_PINS:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)  # Disable all sensors initially

# Initialize I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Storage for sensor objects
sensors = []
# Storage for sensor readings (moving window)
sensor_readings = [deque(maxlen=SAMPLE_SIZE) for _ in range(len(XSHUT_PINS))]

def initialize_sensors():
    """Initialize all sensors with unique I2C addresses"""
    for i, pin in enumerate(XSHUT_PINS):
        print(f"Initializing sensor {i + 1} on pin {pin}")
        
        # Ensure only the sensor being configured is enabled
        for j, xshut_pin in enumerate(XSHUT_PINS):
            GPIO.output(xshut_pin, GPIO.HIGH if j == i else GPIO.LOW)
        time.sleep(0.1)  # Give the sensor time to boot
        
        try:
            # Initialize the sensor at the default address (0x29)
            sensor = adafruit_vl53l0x.VL53L0X(i2c)
            
            # Change to the unique address
            sensor.set_address(I2C_ADDRESSES[i])
            print(f"Sensor {i + 1} set to address {hex(I2C_ADDRESSES[i])}")
            
            # Configure sensor for faster/more reliable readings
            # For VL53L0X, longer timing budget = more accurate readings
            # For a maze robot, we might want to balance speed and accuracy
            sensor.measurement_timing_budget = 30000  # 30ms timing budget (minimum is 20ms)
            
            sensors.append(sensor)
        except Exception as e:
            print(f"Error initializing sensor {i + 1}: {e}")

    # After all sensors are initialized, power them all on
    for pin in XSHUT_PINS:
        GPIO.output(pin, GPIO.HIGH)
    time.sleep(0.1)

def read_sensors_averaged():
    """Read all sensors and return averaged values"""
    average_distances = []
    
    for i, sensor in enumerate(sensors):
        try:
            # Get new reading
            distance = sensor.range
            
            # Cap the maximum range to avoid abnormal readings
            if distance > 2000:  # VL53L0X range is typically up to 2m
                distance = TIMEOUT_VALUE
                
            # Add to the readings queue
            sensor_readings[i].append(distance)
            
            # Calculate average of readings in the window
            if len(sensor_readings[i]) > 0:
                avg_distance = sum(sensor_readings[i]) / len(sensor_readings[i])
                average_distances.append(avg_distance)
            else:
                average_distances.append(TIMEOUT_VALUE)
                
        except Exception as e:
            print(f"Error reading sensor {i + 1}: {e}")
            average_distances.append(TIMEOUT_VALUE)
    
    return average_distances

def cleanup():
    """Clean up GPIO and resources"""
    GPIO.cleanup()
    print("Cleanup complete")

def main():
    try:
        # Initialize all sensors
        initialize_sensors()
        
        print("Starting continuous readings. Press CTRL+C to exit.")
        
        # Main reading loop
        while True:
            distances = read_sensors_averaged()
            
            # Print the averaged distances
            print("\nAveraged Distances:")
            for i, dist in enumerate(distances):
                print(f"Sensor {i + 1}: {dist:.1f} mm")
            
            # This is where you would add your obstacle avoidance logic
            # For example:
            detect_obstacles(distances)
            
            # Small delay between reading cycles
            time.sleep(READ_FREQUENCY)
            
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
    finally:
        cleanup()

def detect_obstacles(distances):
    """Basic obstacle detection logic - customize for your maze navigation"""
    # Example thresholds - adjust based on your maze dimensions
    DANGER_THRESHOLD = 150  # mm - very close obstacle
    WARNING_THRESHOLD = 300  # mm - approaching obstacle
    
    # Check for obstacles in each direction
    directions = ["Front", "Right", "Back", "Left"]  # Adjust based on your sensor placement
    
    for i, distance in enumerate(distances):
        if distance < DANGER_THRESHOLD:
            print(f"DANGER! {directions[i]} obstacle at {distance:.1f}mm")
        elif distance < WARNING_THRESHOLD:
            print(f"Warning: {directions[i]} obstacle at {distance:.1f}mm")

if __name__ == "__main__":
    main()