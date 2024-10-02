import numpy as np
import csv
from scipy.integrate import solve_ivp
from pyatmos import coesa76
from fluids import drag
from scipy.interpolate import interp1d

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

# Function to get atmospheric density using pyatmosphere (COESA 1976 model)
def atmospheric_density(altitude):
    """
    Returns the air density at a given altitude using pyatmosphere's COESA 1976 model.
    Altitude is in kilometers, and the density is returned in kg/m^3.
    """
    # debug
    print(altitude)
    coesa76_geom = coesa76(altitude) # in km
    # print(coesa76_geom.rho)
    return coesa76_geom.rho  # Density in kg/m^3

# Sample empirical Cd vs Re data for a sphere (from tabulated references)
reynolds_numbers = np.array([1e4, 3e5, 4e5,  5e5,  6e5,  7e5, 8e5, 9e5,   1e6,  2e6])
drag_coefficients = np.array([1, 0.98, 0.37, 0.15, 0.19, 0.2, 0.22, 0.23, 0.25, 0.4])
def get_drag_coefficient(Reynolds):
    """
    Returns the drag coefficient (Cd) based on the Reynolds number (Re) for circular cylinders (NACA-TN-3038)
    Data is taken from "Summary of Drag Coefficients of Various Shaped Cylinders by General Electric - Atomic Products Division - Aircraft Nuclear Propulsion Department
    """
    # Create an interpolation function for Cd as a function of Re
    cd_interp = interp1d(reynolds_numbers, drag_coefficients, kind='cubic', bounds_error=False, fill_value='extrapolate')
    # fix to avoid extrapolation at infinity
    if Reynolds >= 2e6:
        return 0.38  # Value for high Reynolds number
        # return 0.0
    else:
        return cd_interp(Reynolds)
    
def get_drag_coefficient(Reynolds):
    Cd = 0.4
    return Cd

def drag_acceleration(state, surface_area, mass):
    x, y, z, vx, vy, vz = state
    r = np.sqrt(x**2 + y**2 + z**2)
    altitude = r - radius_earth # this makes sense
    rho = atmospheric_density(altitude)

    velocity = np.array([vx*1000, vy*1000, vz*1000]) # convert km/s to m/s
    v = np.linalg.norm(velocity) # in m/s

    if v > 0:
        # drag_coefficient
        if mass > 5000:
            characteristic_dimension = 3.45 # diameter of S1 in m
        else:
            characteristic_dimension = 2.15 # diameter of S2 or S3 in m
        kinematic_viscosity = 1.48e-5 # kinematic viscosity of air at 15 deg Celsius in m2/s
        reynolds = v*characteristic_dimension/kinematic_viscosity # -
        drag_coefficient = get_drag_coefficient(reynolds) # -
        # Drag force
        F_drag_x = 0.5 * rho * (vx*1e3)**2 * drag_coefficient * surface_area # N
        F_drag_y = 0.5 * rho * (vy*1e3)**2 * drag_coefficient * surface_area # N
        F_drag_z = 0.5 * rho * (vy*1e3)**2 * drag_coefficient * surface_area # N

        # Acceleration due to drag (deceleration is opposite to velocity vector)
        # a_drag = -F_drag / mass * velocity / v
        a_drag_x = float(-F_drag_x / mass)*1e-3 # N/kg = m/s2 to convert to km/s2
        a_drag_y = float(-F_drag_y / mass)*1e-3 # N/kg = m/s2 to convert to km/s2
        a_drag_z = float(-F_drag_z / mass)*1e-3 # N/kg = m/s2 to convert to km/s2
        a_drag = [a_drag_x, a_drag_y, a_drag_z] # in km/s2
    else:
        a_drag = np.array([0.0, 0.0, 0.0])  # No drag if not moving
    return a_drag

# def drag_acceleration(state, surface_area, mass):
#     x, y, z, vx, vy, vz = state
#     r = np.sqrt(x**2 + y**2 + z**2)
#     altitude = r - radius_earth  # altitude in km
#     rho = atmospheric_density(altitude)  # density in kg/m^3

#     velocity = np.array([vx * 1000, vy * 1000, vz * 1000])  # convert km/s to m/s
#     v = np.linalg.norm(velocity)  # total velocity magnitude in m/s

#     if v > 0:  # Avoid division by zero
#         # Calculate the drag coefficient
#         characteristic_dimension = 3.45  # diameter of S1 in meters
#         kinematic_viscosity = 1.48e-5  # kinematic viscosity of air in m^2/s
#         reynolds = v * characteristic_dimension / kinematic_viscosity  # Reynolds number
#         drag_coefficient = get_drag_coefficient(reynolds)  # Cd from your interpolation function

#         # Drag force vector
#         F_drag = -0.5 * rho * v**2 * drag_coefficient * surface_area * (velocity / v)  # N

#         # Drag acceleration vector
#         a_drag = F_drag / mass  # N/kg = m/s^2

#         # Convert drag acceleration to km/s^2
#         a_drag_km_s2 = a_drag * 1e-3  # convert m/s^2 to km/s^2
#     else:
#         a_drag_km_s2 = np.array([0.0, 0.0, 0.0])  # No drag if not moving

#     return a_drag_km_s2  # return as 3D array [ax, ay, az]

def two_body_equations_with_drag(t, state, mu, surface_area, mass):
    x, y, z, vx, vy, vz = state
    r = np.sqrt(x**2 + y**2 + z**2) # in km
    
    # Gravitational acceleration
    ax = -mu * x / r**3 # in km/s2
    ay = -mu * y / r**3 # in km/s2
    az = -mu * z / r**3 # in km/s2

    # Drag acceleration
    a_drag = drag_acceleration(state, surface_area, mass) # list of 3 in in km/s2

    # Total accelerations
    ax += a_drag[0] # in km/s2
    ay += a_drag[1] # in km/s2
    az += a_drag[2] # in km/s2

    return [vx, vy, vz, ax, ay, az] # in km/s and km/s2


# Event function to detect when the spacecraft impacts the Earth's surface
def impact_condition(t, state, mu, surface_area, mass):
    x, y, z = state[:3]
    r = np.sqrt(x**2 + y**2 + z**2) # in km
    return r - radius_earth  # Trigger event when r = Earth's radius

impact_condition.terminal = True  # Stop propagation at impact
impact_condition.direction = -1  # Detect only when approaching the Earth's surface

def propagate_trajectory_with_drag(event_name, surface_area, mass, 
                                   csv_input='state_vectors.csv', csv_output='propagated_state_vector_drag_{}.csv'):
    # Load the initial state vector from CSV
    flight_time, state0 = load_state_vector_from_csv(event_name, csv_input)

    # Define the time span for propagation (start from event time)
    t_span = (flight_time, flight_time + 3600 * 24)  # Propagate for up to 24 hours

    # Set up the propagation with drag
    sol = solve_ivp(two_body_equations_with_drag, t_span, state0, 
                    args=(mu_earth, surface_area,  mass),
                    events=impact_condition, rtol=1e-9, atol=1e-9)

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
# propagate_trajectory_with_drag(event_name, surface_area=28.1175, mass=((1.79408515641864E+01 - 1.23e1)*1e3)) 
# # eg for S1 length is 8.15 and diameter is 3.45m, Cd is ~1 for Reynolds <2*10^5 Then it falls to 0.2-0.3. For flow speed=0.8km/s the Re=7*10^6, which would be Re=0.3 S1 dry mass which is improvisely subtracted from total rocket mass (Mg to Kg)

# Example usage S2
event_name = 's2s3_separation'  # Define the event name you want to propagate from
propagate_trajectory_with_drag(event_name, surface_area=7.18, mass=((3.01735153404769E+00 -  1.08735152707548E+00)*1e3)) 
# eg for S1 length is 3.338m and diameter is 2.15m, mass isS1 dry mass which is improvisely subtracted from total rocket mass (Mg to Kg)