"""
This Python script is designed to compute the impact radius of descending objects due to wind perturbations. 
The impact radius is influenced by several factors, including the object's surface area, mass, and altitude, 
as well as the local wind speed profile. 

As of now the following have been implemented:
- Lateral wind perturbation (note that the reynolds, Cd, and drag force on the object is computed considering 
an object starting with zero velocity at a given altitude. Since the spent rocket stages will start from 
separation with large velocities, the real Reynolds will be much higher, the Cd probably lower, but the 
overall drag much higher, but that should give a drag force which must be summed with the atmospheric drag. 
Since the atmospheric drag is computed separately, this wind force is only used to plot the impact circle 
having as radius the largest displacement caused by a wind with constant direction onto the surface area of 
the object).

Functions defined within the script include:
- `wind_speed_profile`: Returns the wind speed at a given altitude using cubic interpolation of empirical data.
- `get_impact_radius`: Computes the impact radius for specific events by integrating the equations of motion 
influenced by wind drag and gravity.

Other perturbations that could be implemented in the future are:
- Gravitational perturbations (Earth J2 and third-body perturbations from Sun and Moon);
- Coriolis force;
- Tidal forces;
- Electric drag from plasma re-entry.

Other possible future enhancements:
- Changing Earth's radius function based on latitude;
- Probabilistic analysis of descent trajectories.

This script is intended for launch vehicle simulations, particularly for assessing the impact risks associated
with spent rocket stages and other descending objects.
"""


from impact_with_drag_propagator import get_drag_coefficient, atmospheric_density, load_state_vector_from_csv
import numpy as np
from scipy.interpolate import interp1d

radius_earth = 6371.0 # km (average, to be enhanced)

# Sample empirical Cd vs Re data for a sphere (from tabulated references)
altitudes =   np.array([0, 5,  10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 80, 90, 100, 120])
wind_speeds = np.array([5, 30, 60, 40, 10, 5,  15, 25, 30, 40, 55, 65, 40, 0,  35,  10])
def wind_speed_profile(altitude):
    """
    Returns wind speed based on altitude in km.
    Altitude levels (in km) and their corresponding wind speeds (in m/s):
    from https://www.researchgate.net/figure/Average-wind-speeds-in-m-s-vs-altitude-in-km-On-an-average-wind-speeds-are-minimum-in_fig1_328173177
    and https://www.researchgate.net/figure/Wind-speed-m-s-VS-altitude-Km-14_fig3_324703592
    """
    # Create an interpolation function for Cd as a function of Re
    wind_interp = interp1d(altitudes, wind_speeds, kind='cubic', bounds_error=False, fill_value='extrapolate')
    # fix to avoid extrapolation at infinity
    if altitude >= 120:
        return 5  # Value for high altitudes
    else:
        return wind_interp(altitude)


def get_impact_radius(event_name):
    """
    Computes the impact radius due to wind effects using a numerical integration method.
    
    Args:
        state
        surface_area (float): The surface area of the object in m^2.
        mass (float): The mass of the object in kg.

    Returns:
        float: The computed impact radius in meters.
    """
    # Load the initial state vector from CSV
    flight_time, state = load_state_vector_from_csv(event_name)

    if event_name == 's1s2_separation' or 'drag_s1s1_separation':
        surface_area = 28.1175 # m2
        mass = ((1.79408515641864E+01 - 1.23e1) * 1e3) # kg
    if event_name == 's2s3_separation' or 'drag_s2s3_separation':
        surface_area = 7.185 # m2
        mass = ((3.01735153404769E+00 -  1.08735152707548E+00)*1e3) # kg
    if event_name == 's2fairing_separation' or 'drag_s2fairing_separation':
        surface_area = 17.2 # m2 8 of L3 times diameter of 2.15m
        mass = ((1.04228914258135E+01 - 1.01628914258135E+01)*1e3) # kg    
    else:
        raise ValueError(f"Event name '{event_name}' not recognized. Try with s1s2_separation or s2s3_separation or s2fairing_separation. Or try putting drag_ in front of them")

    x, y, z, vx, vy, vz = state # km and km/s
    r = np.sqrt(x**2 + y**2 + z**2) # km
    altitude = r - radius_earth # this makes sense
    # Initialize variables
    time = 0  # Time in seconds
    dt = 1e-2  # Time step for integration (in seconds)
    starting_altitude = r - radius_earth # this makes sense
    altitude = starting_altitude  # Current altitude in km
    velocity = 0.0  # Initial velocity in m/s
    displacement = 0.0  # Total displacement due to wind in meters
    g = 9.81  # Gravitational acceleration in m/s^2

    while altitude > 0:  # Continue until impact
        # Wind speed as a function of altitude (simple profile)
        wind_speed = wind_speed_profile(altitude)

        # Calculate drag acceleration
        # Important semplification: this is considering an object which starts not moving, only subject to lateral wind
        drag_force_wind = 0.5 * atmospheric_density(altitude) * (velocity + wind_speed)**2 * surface_area * get_drag_coefficient(wind_speed)
        drag_acceleration = drag_force_wind / mass

        # Compute total acceleration (gravity and drag)
        total_acceleration = -g - drag_acceleration  # Negative due to direction

        # Runge-Kutta integration for velocity and altitude
        # Define the system of equations
        def equations(t, state):
            altitude = state[0]
            velocity = state[1]
            wind_speed = wind_speed_profile(altitude)
            drag_force = 0.5 * atmospheric_density(altitude) * (velocity + wind_speed)**2 * surface_area * get_drag_coefficient(velocity)
            drag_acceleration = drag_force / mass
            total_acceleration = -g - drag_acceleration  # Negative due to direction
            # print(altitude) # for debugging
            return [velocity, total_acceleration]

        # Runge-Kutta 4th order integration
        state = [altitude, velocity]
        k1 = equations(time, state)
        k2 = equations(time + dt / 2, [state[0] + dt / 2 * k1[0], state[1] + dt / 2 * k1[1]])
        k3 = equations(time + dt / 2, [state[0] + dt / 2 * k2[0], state[1] + dt / 2 * k2[1]])
        k4 = equations(time + dt, [state[0] + dt * k3[0], state[1] + dt * k3[1]])

        # Update state using the average of k1, k2, k3, k4
        altitude += (dt / 6) * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
        velocity += (dt / 6) * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])

        # Calculate displacement caused by wind
        displacement += wind_speed * dt

        # Update time
        time += dt

    return float(displacement[0])  # Return the total displacement caused by wind

# # S1-S2 separation
# event_name = 's1s2_separation'
# surface_area = 28.1175 # m2
# mass = ((1.79408515641864E+01 - 1.23e1) * 1e3) # kg
# S2-S3 separation
# event_name = 's2s3_separation'
# surface_area = 7.185 # m2
# mass = ((3.01735153404769E+00 -  1.08735152707548E+00)*1e3) # kg

# impact_radius = get_impact_radius(event_name)
# print(f'Computed impact radius is: {float(impact_radius)} km')