import numpy as np
import csv
from scipy.integrate import solve_ivp

# Define constants
mu_earth = 398600.4418  # Earth's gravitational parameter, km^3/s^2
radius_earth = 6371  # Earth's radius in km. This is a source of error since it is not constant along the earth's latitude as it is a spheroid. At Shetland latitude (60.8161 in decimals), the Earth's radius is 6361.869 km at sea level. This means that the impact points in reality could be "before" the simulated ones (e.g. impact points in the equatorial zone where the radius is 6378.137 km well over the average 6371 km considered), or "after" the simulated ones (e.g. for impact points in the polar zones since there the Earth's radius is 6356.752km). The latter one should be the case for S1, fairing, and S2 impact points as they are all inside the artic circle. A "get_radius" function should be written for accurate impact point estimation (https://rechneronline.de/earth-radius/). Of course, the Earth is not  perfect spheroid since its mass is not perfectly evenly distributed.

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

def atmospheric_density(altitude):
    # Exponential atmospheric model based on altitude in km
    if altitude > 1000:
        return 0.0  # Beyond the atmosphere
    H = 8.5  # Scale height in km (typical for Earth atmosphere)
    rho_0 = 1.225  # Sea-level atmospheric density in kg/m^3
    return rho_0 * np.exp(-altitude / H)

def drag_acceleration(state, surface_area, drag_coefficient, mass):
    x, y, z, vx, vy, vz = state
    r = np.sqrt(x**2 + y**2 + z**2)
    altitude = r - radius_earth
    rho = atmospheric_density(altitude)

    velocity = np.array([vx, vy, vz])
    v = np.linalg.norm(velocity)

    # Drag force
    F_drag = 0.5 * rho * v**2 * drag_coefficient * surface_area

    # Acceleration due to drag (deceleration is opposite to velocity vector)
    a_drag = -F_drag / mass * velocity / v
    return a_drag

def two_body_equations_with_drag(t, state, mu, surface_area, drag_coefficient, mass):
    x, y, z, vx, vy, vz = state
    r = np.sqrt(x**2 + y**2 + z**2)
    
    # Gravitational acceleration
    ax = -mu * x / r**3
    ay = -mu * y / r**3
    az = -mu * z / r**3

    # Drag acceleration
    a_drag = drag_acceleration(state, surface_area, drag_coefficient, mass)

    # Total accelerations
    ax += a_drag[0]
    ay += a_drag[1]
    az += a_drag[2]

    return [vx, vy, vz, ax, ay, az]


# Event function to detect when the spacecraft impacts the Earth's surface
def impact_condition(t, state, mu, surface_area, drag_coefficient, mass):
    x, y, z = state[:3]
    r = np.sqrt(x**2 + y**2 + z**2)
    return r - radius_earth  # Trigger event when r = Earth's radius

impact_condition.terminal = True  # Stop propagation at impact
impact_condition.direction = -1  # Detect only when approaching the Earth's surface

def propagate_trajectory_with_drag(event_name, surface_area, drag_coefficient, mass, 
                                   csv_input='state_vectors.csv', csv_output='propagated_state_vector_drag_{}.csv'):
    # Load the initial state vector from CSV
    flight_time, state0 = load_state_vector_from_csv(event_name, csv_input)

    # Define the time span for propagation (start from event time)
    t_span = (flight_time, flight_time + 3600 * 24)  # Propagate for up to 24 hours

    # Set up the propagation with drag
    sol = solve_ivp(two_body_equations_with_drag, t_span, state0, 
                    args=(mu_earth, surface_area, drag_coefficient, mass),
                    events=impact_condition, rtol=1e-14, atol=1e-14)

    # Save the results to a new CSV file
    output_filename = csv_output.format(event_name)
    with open(output_filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Time (s)', 'X (km)', 'Y (km)', 'Z (km)', 'Vx (km/s)', 'Vy (km/s)', 'Vz (km/s)'])
        for i in range(len(sol.t)):
            writer.writerow([sol.t[i], sol.y[0, i], sol.y[1, i], sol.y[2, i], sol.y[3, i], sol.y[4, i], sol.y[5, i]])

    print(f"Propagation complete. Results saved to {output_filename}")


# # Example usage S1
# event_name = 's1s2_separation'  # Define the event name you want to propagate from
# propagate_trajectory_with_drag(event_name, surface_area=40, drag_coefficient=1.5, mass=((1.79408515641864E+01 - 1.23e1)*1e3)) # eg for S1 20m2 of surface area, 1.17 of Cd, and S1 dry mass which is improvisely subtracted from total rocket mass (Mg to Kg)

# Example usage S2
event_name = 's2s3_separation'  # Define the event name you want to propagate from
propagate_trajectory_with_drag(event_name, surface_area=10, drag_coefficient=1.5, mass=((3.01735153404769E+00 -  1.08735152707548E+00)*1e3)) # eg for S1 20m2 of surface area, 1.17 of Cd, and S1 dry mass which is improvisely subtracted from total rocket mass (Mg to Kg)