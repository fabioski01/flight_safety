"""
This Python script models the trajectory of a spacecraft considering atmospheric drag effects. 
It utilizes numerical methods to propagate the state vector derived from initial conditions read from 
a CSV file, applying the two-body problem equations with drag included. The script employs the 
COESA 1976 atmospheric model for air density calculations and provides functions to calculate drag 
coefficients based on Reynolds numbers for different object shapes.

Key features include:
- Loading state vectors for different events from a CSV file.
- Extracting the atmospheric density from COESA 1976 atmospheric model.
- Extracting drag coefficient for a circular cylinder from empirical tables given the Reynolds.
- Computing atmospheric drag acceleration on the spacecraft.
- Propagating the spacecraft's trajectory over a defined time span.
- Saving the propagated trajectory results back to a CSV file.

Future features:
- Extracting Earth radius depending on latitude
- More precise impact point computation considering gravitational and tidal perturbations
and additional drags.

Constants for Earth's gravitational parameter and radius are defined at the beginning, with 
necessary adjustments noted for accuracy based on geographic latitude variations. 
The script is intended for use in launch vehicle simulations, particularly to compute and
propagate trajectories and impact points for spent rocket stages and other components.
"""

import numpy as np
import csv
from scipy.integrate import solve_ivp
from pyatmos import coesa76
from scipy.interpolate import interp1d
from functions_def import earth_radius_at_latitude, convert_j2000_to_geographic
import os # for path finding

# Define constants
mu_earth = 398600.4418  # Earth's gravitational parameter, km^3/s^2

# Function to read the state vector from the CSV file based on event name
def load_state_vector_from_csv(event_name, trajectory_astos_name):
    """
    Loads the state vector (position and velocity) for a specified event from a CSV file.

    Args:
        event_name (str): The name of the event for which the state vector is being loaded.
        trajectory_astos_name(str): The path to the CSV file containing state vectors. Defaults to 'state_vectors.csv'.

    Returns:
        tuple: A tuple containing:
            - flight_time (float): The time of the event in seconds.
            - state_vector (numpy array): A 6-element array with the position (in km) and velocity (in km/s) of the object.

    Raises:
        ValueError: If the event name is not found in the CSV file.
    """
    # Map special event names to standard event names
    event_name_map = {
        'drag_s1s2_separation': 's1s2_separation',
        'drag_s2s3_separation': 's2s3_separation',
        'drag_s2fairing_separation': 's2fairing_separation'
    }
    
    # If the event name is in the map, replace it with the standard name
    event_name = event_name_map.get(event_name, event_name)
    csv_filename = 'state_vectors.csv'
    csv_filename = os.path.join(f'csv_files_{trajectory_astos_name}', csv_filename)  # kind of a hotfix to not change the entire structure
    # Open and read the CSV file
    with open(csv_filename, 'r') as file:
        reader = csv.reader(file)
        header = next(reader)  # Skip the header
        
        # Iterate through the rows to find the matching event
        for row in reader:
            if row[-1] == event_name:  # Match the event name
                # Extract time, position, and velocity
                flight_time = float(row[0])  # Time in seconds
                position = np.array([float(row[1]), float(row[2]), float(row[3])])  # Position in km
                velocity = np.array([float(row[4]), float(row[5]), float(row[6])])  # Velocity in km/s
                state_vector = np.hstack((position, velocity))
                return flight_time, state_vector
    
    # Raise an error if the event name is not found
    raise ValueError(f"Event name '{event_name}' not found in {csv_filename}")

def earth_radius_from_j2000(state7):
    """
    Calculate the Earth's radius from a J2000 state vector (x, y, z) at a given event time.
    
    Args:
        Args:
        state7 (array-like): A 7-element array representing the state vector [time, x, y, z, vx, vy, vz], 
                            where time is flight time in seconds, x, y, z are the positions in km, and vx, vy, vz are the velocities in km/s.    
    Returns:
        float: Earth's radius at the corresponding latitude in kilometers.
    """
    # Convert J2000 state vector to geographic latitude
    x, y, z = state7[1:4]
    event_time = state7[0]
    lat, lon, alt = convert_j2000_to_geographic(x, y, z, event_time)
    
    # Calculate Earth's radius at that latitude
    earth_radius = earth_radius_at_latitude(lat)
    # print(f'latitude from earth_radius_from_j2000(state7):{lat}')
    # print(f'earth radius from earth_radius_from_j2000(state7): {earth_radius}')
    return earth_radius # in km 

def atmospheric_density(altitude):
    """
    Returns the air density at a given altitude using pyatmosphere's COESA 1976 model.
    Args:
        altitude (float): The altitude in kilometers for which the air density is being computed.

    Returns:
        float: The air density at the given altitude in kg/m^3.
    """
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
    Args:
        Reynolds (float): The Reynolds number for which the drag coefficient is extracted.

    Returns:
        float: The drag coefficient Cd at the given Reynolds.
    """
    # Create an interpolation function for Cd as a function of Re
    cd_interp = interp1d(reynolds_numbers, drag_coefficients, kind='cubic', bounds_error=False, fill_value='extrapolate')
    # fix to avoid extrapolation at infinity
    if Reynolds >= 2e6:
        return 0.38  # Value for high Reynolds number
        # return 0.0
    else:
        return cd_interp(Reynolds)

def drag_acceleration(state7, surface_area, mass):
    """
    Computes the acceleration due to drag on an object in the atmosphere, given its state vector, surface area, and mass.
    
    Args:
        state7 (array-like): A 7-element array representing the state vector [time, x, y, z, vx, vy, vz], 
                            where time is flight time in seconds, x, y, z are the positions in km, and vx, vy, vz are the velocities in km/s.
        surface_area (float): The surface area of the object in square meters.
        mass (float): The mass of the object in kilograms.
    
    Returns:
        list: A 3-element list representing the drag acceleration in km/s² in the x, y, and z directions.
    """
    x, y, z, vx, vy, vz = state7[1:]
    r = np.sqrt(x**2 + y**2 + z**2)
    radius_earth = earth_radius_from_j2000(state7)
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
        # # Drag force

        # F_drag_x = 0.5 * rho * (vx)**2 * drag_coefficient * surface_area # N
        # F_drag_y = 0.5 * rho * (vy)**2 * drag_coefficient * surface_area # N
        # F_drag_z = 0.5 * rho * (vy)**2 * drag_coefficient * surface_area # N
        F_drag = 0.5 * rho * (v)**2 * drag_coefficient * surface_area # N
        # # Acceleration due to drag (deceleration is opposite to velocity vector)
        # a_drag = -F_drag / mass * velocity / v
        # Drag accelerations in x, y, z directions
        # a_drag_x = float(-F_drag_x / mass)*1e-3 # N/kg = m/s2 to convert to km/s2
        # a_drag_y = float(-F_drag_y / mass)*1e-3 # N/kg = m/s2 to convert to km/s2
        # a_drag_z = float(-F_drag_z / mass)*1e-3 # N/kg = m/s2 to convert to km/s2
        a_drag_x = float(F_drag / mass)*(vx*1000/v)*1e-3 # N/kg = m/s2 to convert to km/s2
        a_drag_y = float(F_drag / mass)*(vy*1000/v)*1e-3 # N/kg = m/s2 to convert to km/s2
        a_drag_z = float(F_drag / mass)*(vz*1000/v)*1e-3 # N/kg = m/s2 to convert to km/s2
        a_drag = [a_drag_x, a_drag_y, a_drag_z] # in km/s2
    else:
        a_drag = np.array([0.0, 0.0, 0.0])  # No drag if not moving
    # print(f'acc drag x: {a_drag_x}') # for debugging
    # print(f'drag acc: {a_drag}') # for debugging
    # print(f'drag force: {F_drag}') # for debugging
    return a_drag

def two_body_equations_with_drag(t, state7, mu, surface_area, mass):
    """
    Computes the state derivatives for a two-body problem with atmospheric drag.

    Args:
        t (float): The current time (not used in this implementation, but necessary for ode solvers).
        state7 (list): The current state vector [time, x, y, z, vx, vy, vz], where time is flight time in seconds, (x, y, z) are the position coordinates in kilometers,
                      and (vx, vy, vz) are the velocity components in kilometers per second.
        mu (float): The gravitational parameter (GM) of the central body (Earth) in km^3/s^2.
        surface_area (float): The surface area of the spacecraft in square meters.
        mass (float): The mass of the spacecraft in kilograms.

    Returns:
        list: A list containing the derivatives [vx, vy, vz, ax, ay, az], where (ax, ay, az) are the accelerations in kilometers per second squared.
    """
    x, y, z, vx, vy, vz = state7[1:] # skips time which is first element
    r = np.sqrt(x**2 + y**2 + z**2) # in km
    
    # Gravitational acceleration
    ax = -mu * x / r**3 # in km/s2
    ay = -mu * y / r**3 # in km/s2
    az = -mu * z / r**3 # in km/s2

    # Drag acceleration
    a_drag = drag_acceleration(state7, surface_area, mass) # list of 3 in in km/s2

    # Total accelerations
    ax += a_drag[0] # in km/s2
    ay += a_drag[1] # in km/s2
    az += a_drag[2] # in km/s2

    return [vx, vy, vz, ax, ay, az] # in km/s and km/s2

def impact_condition(t, state6, mu, surface_area, mass):
    """
    Event function to detect when the spacecraft impacts the Earth's surface.

    Args:
        t (float): Current time in seconds during the simulation.
        state6 (array-like): A 6-element array representing the state vector [x, y, z, vx, vy, vz], 
                            where x, y, z are the positions in km. This is imported from the solve_ivp
        mu (float): Standard gravitational parameter for the Earth (in km³/s²).
        surface_area (float): The surface area of the spacecraft in square meters.
        mass (float): The mass of the spacecraft in kilograms.

    Returns:
        float: The difference between the current radial distance of the spacecraft from Earth's center and the Earth's radius.
               The event triggers when this value is zero (i.e., when the spacecraft reaches the surface of the Earth).
    """
    x, y, z, vx, vy, vz = state6 # skips first element which is time
    r = np.sqrt(x**2 + y**2 + z**2) # in km

    state7 = [t] + list(state6) # reconstruct state7 needed to get latitude to get earth radius
    radius_earth = earth_radius_from_j2000(state7)
    difference = r - radius_earth
    # print(f'Time: {t}, Radial Distance: {r}, Earth Radius: {radius_earth}, Difference: {difference}, x: {x}, y: {y}, z: {z}, vx: {vx}, vy: {vy}, vz: {vz}') # for debugging
    # Return a thresholded condition for triggering impact
    # if np.any(np.isnan(state6)) or np.any(np.isinf(state6)):
    #     print("NaN or Inf detected in state6!")
    return difference if difference > 0 else 0  # Event triggers when approaching Earth's surface

impact_condition.terminal = True  # Stop propagation at impact
impact_condition.direction = -1  # Detect only when approaching the Earth's surface

def propagate_trajectory_with_drag(event_name, surface_area, mass, trajectory_astos_name):
    """
    Propagates the trajectory of the spacecraft considering atmospheric drag and saves the result to a CSV file.

    Args:
        event_name (str): The name of the event for which the state vector is being propagated (e.g., 's1s2_separation').
        surface_area (float): The surface area of the spacecraft in square meters.
        mass (float): The mass of the spacecraft in kilograms.
        trajectory_astos_name (str): Name to be used for the folder where the CSV file is saved.
        csv_input (str): The name of the input CSV file containing the initial state vector. Default is csv_files/'state_vectors.csv'.
    
    Returns:
        None: The function saves the propagated trajectory to a CSV file.
    """
    # CSV file folder should already exist from state vectors of events. Output and input folder should coincide
    folder_name = f"csv_files_{trajectory_astos_name}"
    # os.makedirs(folder_name, exist_ok=True)
    
    # Define the output file path within the folder
    output_filename = os.path.join(folder_name, f"propagated_state_vector_drag_{event_name}.csv")
    csv_input = os.path.join(folder_name, 'state_vectors.csv')  # This is to make a FILE to be opened (NOT a directory)
    # Load the initial state vector from CSV
    state7 = load_state_vector_from_csv(event_name, trajectory_astos_name)
    state6 = state7[1]# then in two_body_eq the time is skipped
    # Ensure state6 is a flat array
    state6 = np.array(state6).flatten()
    flight_time = state7[0] # first element is time
    state7 = [flight_time] + list(state6)
    # Define the time span for propagation (start from event time)
    t_span = (flight_time, flight_time + 3600 * 24)  # Propagate for up to 24 hours

    # Wrapper function for two_body_equations_with_drag to add time back into state7
    def two_body_equations_with_drag_wrapper(t, state6, mu, surface_area, mass):
        # Rebuild state7 by adding the time component (t) back
        state7 = [t] + list(state6)
        return two_body_equations_with_drag(t, state7, mu, surface_area, mass)

    # Set up the propagation with drag using state6 (6 elements) for solve_ivp
    sol = solve_ivp(two_body_equations_with_drag_wrapper, t_span, state6, 
                    args=(mu_earth, surface_area, mass),
                    events=impact_condition, method='RK45', rtol=1e-7, atol=1e-7)

    # Save the results to a new CSV file
    with open(output_filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Time (s)', 'X (km)', 'Y (km)', 'Z (km)', 'Vx (km/s)', 'Vy (km/s)', 'Vz (km/s)'])
        for i in range(len(sol.t)):
            writer.writerow([sol.t[i], sol.y[0, i], sol.y[1, i], sol.y[2, i], sol.y[3, i], sol.y[4, i], sol.y[5, i]])

    print(f"Propagation complete. Results saved to {output_filename}")


# # Example usage S1-S2
# event_name = 's1s2_separation'  # Define the event name you want to propagate from
# propagate_trajectory_with_drag(event_name, surface_area=28.1175, mass=((1.79408515641864E+01 - 1.23e1)*1e3)) 
# # eg for S1 length is 8.15 and diameter is 3.45m, Cd is ~1 for Reynolds <2*10^5 Then it falls to 0.2-0.3. For flow speed=0.8km/s the Re=7*10^6, which would be Re=0.3 S1 dry mass which is improvisely subtracted from total rocket mass (Mg to Kg)

# # Example usage S2-S3
# event_name = 's2s3_separation'  # Define the event name you want to propagate from
# propagate_trajectory_with_drag(event_name, surface_area=7.18, mass=((3.01735153404769E+00 -  1.08735152707548E+00)*1e3)) 
# # eg for S2 length is 3.338m and diameter is 2.15m, mass is S2 dry mass which is improvisely subtracted from total rocket mass (Mg to Kg)

# # Example usage S2-fairing
# event_name = 's2fairing_separation'  # Define the event name you want to propagate from
# propagate_trajectory_with_drag(event_name, surface_area=17.2, mass = (( 1.04228914258135E+01 - 1.01628914258135E+01)*1e3)) 
# # eg for fairing length L3 is 8m and diameter is 2.15m, mass is fairing dry mass which is improvisely subtracted from total rocket mass (Mg to Kg)