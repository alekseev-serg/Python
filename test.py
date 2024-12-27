import time
import os

# Function to increase CPU load
def increase_cpu_load(target_load):
    while True:
        start_time = time.time()
        while time.time() - start_time < 0.01:
            continue

        current_load = os.getloadavg()[0]
        if current_load < target_load:
            # Perform some CPU intensive operation here
            continue

# Set the target CPU load
target_cpu_load = 0.6

# Start increasing the CPU load
increase_cpu_load(target_cpu_load)