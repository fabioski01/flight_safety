import numpy as np
import csv
from scipy.integrate import solve_ivp

# Define constants
mu_earth = 398600.4418  # Earth's gravitational parameter, km^3/s^2
radius_earth = 6371  # Earth's radius in km

# Function to read the state vector from the CSV file based on event name
def load_state_vector_from_csv(event_name, csv_filename='state_vectors.csv'):
    with open(csv_filename, 'r') as file:
        reader = csv.reader(file)
        header = next(reader)  # Read the header
        
        # Iterate through the rows to find the matching event
        for row in reader:
            if row[-1] == event_name:  # Match the event name
                # Extract time, position, and velocity
                flight_time = float(row[0])  # Time in seconds
                position = np.array([float(row[1]), float(row[2]), float(row[3])])  # Position in km
                velocity = np.array([float(row[4]), float(row[5]), float(row[6])])  # Velocity in km/s
                state_vector = np.hstack((position, velocity))
                return flight_time, state_vector
    raise ValueError(f"Event name '{event_name}' not found in {csv_filename}")

# Function that defines the two-body equations of motion
def two_body_equations(t, state, mu):
    x, y, z, vx, vy, vz = state
    r = np.sqrt(x**2 + y**2 + z**2)
    
    # Newton's law of gravitation
    ax = -mu * x / r**3
    ay = -mu * y / r**3
    az = -mu * z / r**3
    
    return [vx, vy, vz, ax, ay, az]

# Event function to detect when the spacecraft impacts the Earth's surface
def impact_condition(t, state, mu):
    x, y, z = state[:3]
    r = np.sqrt(x**2 + y**2 + z**2)
    return r - radius_earth  # Trigger event when r = Earth's radius

impact_condition.terminal = True  # Stop propagation at impact
impact_condition.direction = -1  # Detect only when approaching the Earth's surface

# Propagation function
def propagate_trajectory(event_name, csv_input='state_vectors.csv', csv_output='propagated_state_vector_{}.csv'):
    # Load the initial state vector from CSV
    flight_time, state0 = load_state_vector_from_csv(event_name, csv_input)

    # Define the time span for propagation (start from event time)
    t_span = (flight_time, flight_time + 3600 * 24)  # Propagate for up to 24 hours

    # Set up the propagation
    sol = solve_ivp(two_body_equations, t_span, state0, args=(mu_earth,),
                    events=impact_condition, rtol=1e-14, atol=1e-14) # tolerance can be lowered for lower timestep

    # Save the results to a new CSV file
    output_filename = csv_output.format(event_name)
    with open(output_filename, 'w', newline='') as file:
        writer = csv.writer(file)
        # Write header
        writer.writerow(['Time (s)', 'X (km)', 'Y (km)', 'Z (km)', 'Vx (km/s)', 'Vy (km/s)', 'Vz (km/s)'])
        # Write the state vectors
        for i in range(len(sol.t)):
            writer.writerow([sol.t[i], sol.y[0, i], sol.y[1, i], sol.y[2, i], sol.y[3, i], sol.y[4, i], sol.y[5, i]])

    print(f"Propagation complete. Results saved to {output_filename}")

# Example usage
event_name = 's1s2_separation'  # Define the event name you want to propagate from
propagate_trajectory(event_name)
