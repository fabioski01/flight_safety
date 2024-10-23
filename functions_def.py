import pandas as pd
import numpy as np
import csv
from astropy import units as u
from astropy.coordinates import GCRS, ITRS, CartesianRepresentation, EarthLocation
from astropy.time import Time
from pyproj import Transformer # for wsg84
from geopy.distance import geodesic
import math

def convert_seconds_to_iso(seconds):
    """
    Converts a time in seconds since the J2000 epoch to an ISO 8601 formatted string.

    Args:
        seconds (float): The time in seconds since the J2000 epoch.

    Returns:
        str: An ISO 8601 formatted time string corresponding to the input seconds.
    """
    # The epoch is set to some known reference time, e.g., J2000
    j2000_epoch = Time("2000-01-01T12:00:00", scale='utc')  # J2000 epoch should be at 12, but it is wrong
    # print(f'epoch: {(j2000_epoch + seconds * u.s).iso}') # for debugging
    return (j2000_epoch + seconds * u.s).iso

def earth_radius_at_latitude(latitude_degrees):
    """
    Calculate the Earth's radius at a given latitude using the provided formula.
    
    Args:
        latitude_degrees (float): Latitude in degrees.
    
    Returns:
        float: Earth's radius at the specified latitude in kilometers.
    """
    # Convert latitude from degrees to radians
    latitude_radians = math.radians(latitude_degrees)
    
    # Constants: Earth's equatorial and polar radii (in kmeters)
    r1 = 6378137  # Equatorial radius in meters is 6378.137 km
    r2 = 6356752  # Polar radius in meters is 6356.752 km
    
    # Calculate radius using the provided formula
    numerator = (r1**2 * math.cos(latitude_radians))**2 + (r2**2 * math.sin(latitude_radians))**2
    denominator = (r1 * math.cos(latitude_radians))**2 + (r2 * math.sin(latitude_radians))**2
    radius = math.sqrt(numerator / denominator)

    # # Use a point at the specified latitude and the equator (0,0) to calculate distance
    # point_on_equator = (0, 0)
    # point_at_latitude = (latitude_degrees, 0)

    # # Calculate the distance from the equator to the point at the given latitude
    # radius = geodesic(point_on_equator, point_at_latitude).kilometers
    return radius/1000 # convert m to km

# def earth_radius_with_geod(latitude_degrees):
#     """
#     Compute the Earth's radius at a given latitude using the WGS84 ellipsoid model via the geographiclib library.

#     Args:
#         lat (float): Geodetic latitude in degrees.

#     Returns:
#         float: Earth radius at the given latitude in kilometers.
#     """
#     geod = Geodesic.WGS84
#     radius = geod.EquatorialRadius * (1 - geod.Flattening * (1 - geod.Flattening * (np.sin(np.radians(latitude_degrees))**2)))
    
#     return radius

def convert_j2000_to_geographic(x, y, z, event_time):
    """
    Converts Cartesian coordinates in the J2000 reference frame (ECI) to geographic coordinates (ECEF) (latitude, longitude, altitude).

    Args:
        x (float): The x-coordinate in kilometers.
        y (float): The y-coordinate in kilometers.
        z (float): The z-coordinate in kilometers.
        event_time (float): The event time in seconds since the J2000 epoch.

    Returns:
        tuple: A tuple containing:
            - lat (float): Latitude in degrees.
            - lon (float): Longitude in degrees.
            - alt (float): Altitude in **meters**.
    """
    iso_time = convert_seconds_to_iso(event_time)
    cartesian = CartesianRepresentation(x * u.km, y * u.km, z * u.km)

    # GCRS coordinate (Geocentric Celestial Reference System)
    gcrs = GCRS(cartesian, obstime=Time(iso_time))

    # Convert it to an Earth-fixed frame: ITRS (International Terrestrial Reference System)
    itrs = gcrs.transform_to(ITRS(obstime=Time(iso_time)))

    el = EarthLocation.from_geocentric(itrs.x, itrs.y, itrs.z)

    # conversion to geodetic
    lon, lat, alt = el.to_geodetic()

    # Convert units for return
    lat_deg = lat.to(u.deg).value  # Latitude in degrees
    lon_deg = lon.to(u.deg).value  # Longitude in degrees
    alt_m = alt.to(u.m).value  # Altitude in meters

    return lat_deg, lon_deg, alt_m

# def convert_j2000_to_wgs84(x, y, z, event_time):
#     """
#     Converts Cartesian coordinates in the J2000 reference frame to WGS84 geographic coordinates (latitude, longitude, altitude).

#     Args:
#         x (float): The x-coordinate in kilometers (in J2000 frame).
#         y (float): The y-coordinate in kilometers (in J2000 frame).
#         z (float): The z-coordinate in kilometers (in J2000 frame).
#         event_time (float): The event time in seconds since the J2000 epoch.

#     Returns:
#         tuple: A tuple containing:
#             - lat (float): Latitude in degrees.
#             - lon (float): Longitude in degrees.
#             - alt (float): Altitude in meters.
#     """
#     # Convert Cartesian coordinates from km to meters for ECEF transformation
#     x_meters = x * 1000  # Convert kilometers to meters
#     y_meters = y * 1000  # Convert kilometers to meters
#     z_meters = z * 1000  # Convert kilometers to meters

#     # Define transformer from ECEF (Earth-Centered, Earth-Fixed) to WGS84 geographic coordinates
#     transformer = Transformer.from_crs("EPSG:4978", "EPSG:4326")  # ECEF to WGS84

#     # Transform ECEF coordinates (X, Y, Z) to WGS84 (lat, lon, alt)
#     lat, lon, alt = transformer.transform(x_meters, y_meters, z_meters)

#     return lat, lon, alt

def load_excel_as_two_arrays(file_path):
    """
    Function to load an Excel file as two arrays:
    1. One for rows 1 to 4 as strings.
    2. One for rows 5 onwards as floats.
    
    Parameters:
    - file_path: str : Path to the Excel file
    
    Returns:
    - string_array: np.ndarray : NumPy array containing the first 4 rows as strings
    - numeric_array: np.ndarray : NumPy array containing the data from row 5 onwards as floats
    """
    # Load the entire Excel file into a pandas DataFrame (do not specify dtype yet)
    df = pd.read_excel(file_path, header=None)
    
    # Split the DataFrame into two parts
    string_part = df.iloc[:4, :]  # Rows 1 to 4 (index 0 to 3)
    numeric_part = df.iloc[4:, :]  # Rows 5 onwards (index 4 onwards)
    
    # Convert the string part to a NumPy array (keep as strings)
    string_array = string_part.to_numpy(dtype=str)

    # Convert the numeric part to a NumPy array of floats, coerce errors to NaN
    numeric_array = numeric_part.apply(pd.to_numeric, errors='coerce').to_numpy(dtype=float)

    return string_array, numeric_array

def find_column_index(string_array, column_name):
    """
    Function to find the index of a column based on the column name (found in row 2).
    
    Parameters:
    - string_array: np.ndarray : NumPy array containing string data (first 4 rows)
    - column_name: str : The name of the column to search for in row 2 (index 1)
    
    Returns:
    - col_index: int : The index of the column (if found)
    """
    
    row_2 = string_array[1, :]  # Row 2 corresponds to index 1
    try:
        col_index = np.where(row_2 == column_name)[0][0]  # Find the first match
        return col_index
    except IndexError:
        raise ValueError(f"Column '{column_name}' not found in row 2.")

def find_first_and_last_nonzero(column_name, string_array, numeric_array):
    """
    Function to find the first and last non-zero values in a numeric column.
    
    Parameters:
    - column_name: string : name of the column to look into.
    - string_array: np.ndarray : NumPy array containing string data (first 4 rows)
    - numeric_array: np.ndarray : NumPy array containing the data from row 5 onwards as floats
    
    Returns:
    - first_index: int : Index of the first non-zero value
    - last_index: int : Index of the last non-zero value
    - first_value: float : First non-zero value
    - last_value: float : Last non-zero value
    """

    # Find the index of the specified column in the string array (row 2)
    col_index = find_column_index(string_array, column_name)

    # Extract the corresponding column from the numeric array
    numeric_column = numeric_array[:, col_index]

    # Find indices where the values are non-zero
    non_zero_indices = np.nonzero(numeric_column)[0]
    
    if non_zero_indices.size == 0:
        raise ValueError("No non-zero values found in the column.")
    
    first_index = non_zero_indices[0]  # First non-zero index
    last_index = non_zero_indices[-1]  # Last non-zero index
    
    first_value = numeric_column[first_index]
    last_value = numeric_column[last_index]
    
    return first_index, last_index, first_value, last_value

def get_time(row_index, string_array, numeric_array):
    """
    Function to find the time of an event given its row index.
    
    Parameters:
    - row_index: int : index representing the row number which contains the event value
    - string_array: np.ndarray : NumPy array containing string data (first 4 rows)
    - numeric_array: np.ndarray : NumPy array containing the data from row 5 onwards as floats
    
    Returns:
    - event_time: float: timestamp of the event
    """    
    # Specify the column name to find timestamp column
    column_name = "flight_time"
    time_col_index = find_column_index(string_array, column_name)
    time_value = numeric_array[row_index, time_col_index]

    return time_value

def get_altitude(row_index, string_array, numeric_array):
    """
    Function to find the altitude of an event given its row index.
    
    Parameters:
    - row_index: int : index representing the row number which contains the event value
    - string_array: np.ndarray : NumPy array containing string data (first 4 rows)
    - numeric_array: np.ndarray : NumPy array containing the data from row 5 onwards as floats
    
    Returns:
    - event_time: float: ALTITUDE of the event
    """    
    # Specify the column name to find ALTITUDE column
    column_name = "altitude~Rocket@Earth" # Altitude of Rocket at Earth
    altitude_col_index = find_column_index(string_array, column_name)
    altitude_value = numeric_array[row_index, altitude_col_index]

    return altitude_value

def get_mass(row_index, string_array, numeric_array):
    """
    Function to find the mass of the rocket at the given row (timestamp).
    Generally to be used to get the dry mass of each stage by comparing the mass just before stage separation with the mass immediatly after.

    Parameters:
    - row_index: int : index representing the row number which contains the event value
    - string_array: np.ndarray : NumPy array containing string data (first 4 rows)
    - numeric_array: np.ndarray : NumPy array containing the data from row 5 onwards as floats
    
    Returns:
    - event_time: float: MASS of the event
    """
    # Specify the column name to find MASS column
    column_name = "mass_total~Rocket" # Altitude of Rocket at Earth
    mass_col_index = find_column_index(string_array, column_name)
    mass_value = float(numeric_array[row_index, mass_col_index])*1e3 # convert Mg (megagrams) to Kg

    return mass_value

def get_stage_dry_mass(row_index, string_array, numeric_array):
    """
    Function to find the dry mass mass of a rocket stage.
    Generally to be used by the drag propagators.
    There could be an error (very low) due to the propellant mass immediatly burned at second or third engine ignition. In this case, the dry mass considered could be overestimated (by grams)

    Parameters:
    - row_index: int : index representing the row number which contains the event value
    - string_array: np.ndarray : NumPy array containing string data (first 4 rows)
    - numeric_array: np.ndarray : NumPy array containing the data from row 5 onwards as floats
    
    Returns:
    - event_time: float: MASS of the event
    """
    # Specify the column name to find stage dry mass
    dry_mass = get_mass(row_index, string_array, numeric_array) - get_mass(row_index+1, string_array, numeric_array)
    return dry_mass # kg already

def find_multiple_phase_transitions(column_name, string_array, numeric_array, tolerance=1e-2):
    """
    Generalized function to detect multiple constant phases followed by a transition to decreasing values.
    
    Parameters:
    - column_name: string : name of the column to look into.
    - string_array: np.ndarray : NumPy array containing string data (first 4 rows)
    - numeric_array: np.ndarray : NumPy array containing the data from row 5 onwards as floats
    - tolerance: float : A small value to account for floating-point comparison issues (default: 1e-2).

    Returns:
    - transition_indices: List[int] : List of indices where transitions between constant values occur.
    - constant_values: List[float] : List of constant values for each phase.
    """

    # Find the index of the specified column in the string array (row 2)
    col_index = find_column_index(string_array, column_name)

    # Extract the corresponding column from the numeric array
    numeric_column = numeric_array[:, col_index]

    transition_indices = []
    constant_values = []

    # Step 1: Start by assuming the first value is the first constant phase
    current_constant_value = numeric_column[0]
    constant_values.append(current_constant_value)

    phase_started = False

    for i in range(1, len(numeric_column)):
        # Detect if a new phase starts (a decrease from the current constant phase)
        if abs(numeric_column[i] - current_constant_value) > tolerance:
            # If the value decreases, we enter a new phase
            if numeric_column[i] < current_constant_value:
                # Mark the transition point (new constant phase)
                transition_indices.append(i)
                current_constant_value = numeric_column[i]
                constant_values.append(current_constant_value)

                # Now, we are in a new phase, and it may also decrease again
                phase_started = True
            else:
                # If the value doesn't decrease, ignore it (no valid transition)
                phase_started = False
        else:
            # We are still in the current constant phase
            phase_started = True

    # If no final decreasing phase is found, just return the collected transitions
    return transition_indices, constant_values

def find_max(column_name, string_array, numeric_array):
    """
    Function to find the maximum value in a numeric column and its index.
    
    Parameters:
    - column_name: string : name of the column to look into.
    - string_array: np.ndarray : NumPy array containing string data (first 4 rows)
    - numeric_array: np.ndarray : NumPy array containing the data from row 5 onwards as floats

    Returns:
    - max_index: int : The index of the maximum value in the column.
    - max_value: float : The maximum value in the column.
    """

    # Find the index of the specified column in the string array (row 2)
    col_index = find_column_index(string_array, column_name)

    # Extract the corresponding column from the numeric array
    numeric_column = numeric_array[:, col_index]

    max_value = np.max(numeric_column)  # Find the maximum value
    max_index = np.argmax(numeric_column)  # Find the index of the maximum value
    
    return max_index, max_value

import csv

# Initialize a list to store state vectors and event names
state_vectors_list = []

def reset_state_vectors():
    """
    Function to reset the state vectors list before collecting new data.
    """
    global state_vectors_list
    state_vectors_list = []  # Clear the list

def get_state_vector(row_index, string_array, numeric_array, event_name):
    """
    Function to find the state vector (x, y, z position and velocity) of an event given its row index,
    and append it to a global list for later saving to a CSV file.
    
    Parameters:
    - row_index: int : Index representing the row number which contains the event value.
    - string_array: np.ndarray : NumPy array containing string data (first 4 rows).
    - numeric_array: np.ndarray : NumPy array containing the data from row 5 onwards as floats.
    - event_name: str : The name of the event/column to include in the list.
    
    Returns:
    - state_vector: np.ndarray : 1x6 NumPy array containing [x, y, z, vx, vy, vz].
    """
    
    # Define column names for position, velocity, and flight time
    position_columns = ["x~Rocket#J2000@Earth", "y~Rocket#J2000@Earth", "z~Rocket#J2000@Earth"]  # km
    velocity_columns = ["vx~Rocket#J2000@Earth", "vy~Rocket#J2000@Earth", "vz~Rocket#J2000@Earth"]  # km/s
    flight_time_column = "flight_time"  # Column for flight time in seconds

    # Find the indices for position, velocity, and flight time columns
    position_indices = [find_column_index(string_array, col_name) for col_name in position_columns]
    velocity_indices = [find_column_index(string_array, col_name) for col_name in velocity_columns]
    flight_time_index = find_column_index(string_array, flight_time_column)

    # Extract the position, velocity, and flight time values for the given row index
    position_values = numeric_array[row_index, position_indices]  # Position in km
    velocity_values = numeric_array[row_index, velocity_indices]  # Velocity in km/s
    flight_time = numeric_array[row_index, flight_time_index]  # Flight time in seconds

    # Combine flight time, position, and velocity into a single array
    state_vector_with_time = np.hstack((flight_time, position_values, velocity_values))

    # Append the state vector with flight time and event name to the global list
    state_vectors_list.append(np.append(state_vector_with_time, event_name).tolist())  # Convert to list

    return state_vector_with_time

def save_state_vectors_to_csv(output_csv_path):
    """
    Save all the state vectors and corresponding event names stored in the list to a CSV file.
    
    Parameters:
    - output_csv_path: str : Path to save the state vector list to a CSV file.
    """
    # Specify the header
    header = ['Time (s)', 'X (km)', 'Y (km)', 'Z (km)', 'Vx (km/s)', 'Vy (km/s)', 'Vz (km/s)', "Event"]
    
    # Open the file in write mode and write the data
    with open(output_csv_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(header)
        # Write the state vectors and event names
        writer.writerows(state_vectors_list)

    print(f"All state vectors saved to {output_csv_path}")

def calculate_visibility_radius(altitude, r_earth=6371e3, max_visibility_radius=700e3, max_visibility_altitude=150e3):
    """
    Calculates the visibility radius based on the given altitude. Has constraints of maximum visibility radius and altitude.
    Might need enhancing in the future.

    Args:
        altitude (float): Altitude in m (because KML plotting is in m).
        r_earth (float): Earth's radius in km (default is 6371e3 m).
        max_visibility_radius (float): Maximum visibility radius, generally difficult to estimate, dependent on multiple arguments which are not taken into account (atmospheric scattering, lightning conditions, object size and brightness, weather conditions...). Default set to 700e3 m.
        max_visibility_altitude (float): Maximum altitude for which an object can be seen from ground level. Generally difficult to estimate, dependent on multiple arguments which are not taken into account (atmospheric scattering, lightning conditions, object size and brightness, weather conditions...). Default set to 150e3 m.

    Returns:
        float: Visibility radius in meters.
    """
    # set radius to 0 if the altitude is above the visible altitude
    if altitude > max_visibility_altitude:
        visibility_radius = 0
    else:
        # uses formula for distance to the horizon, might need fixing (https://aty.sdsu.edu/explain/atmos_refr/horizon.html)
        visibility_radius = 0.5*math.sqrt(r_earth * altitude * 2)
    
    # set radius to the max allowed in case it would have been larger
    if visibility_radius > max_visibility_radius:
        visibility_radius = max_visibility_radius

    return visibility_radius


# # example of usage
# if __name__ == "__main__":
#     file_path = '/home/fabiomeloni/flight_safety/traiettoria.xlsx'
    
#     # Load the Excel file as two separate arrays
#     string_array, numeric_array = load_excel_as_two_arrays(file_path)
    
#     # Specify the column name you are looking for
#     column_name = "thrust~Engine_1_Up:Rocket"
    
#     # Find the index of the specified column in the string array (row 2)
#     col_index = find_column_index(string_array, column_name)
    
#     # Extract the corresponding column from the numeric array
#     numeric_column = numeric_array[:, col_index]
    
#     # Find the first and last non-zero values in the numeric column
#     first_index, last_index, first_value, last_value = find_first_and_last_nonzero(numeric_column)
    
#     # Print the results
#     print(f"First non-zero value at row index: {first_index + 5}, value: {first_value}")
#     print(f"Last non-zero value at row index: {last_index + 5}, value: {last_value}")

#     # get time, altitude, state vector
#     ignition_s1_time = get_time(first_index)
#     print(f"Index of S1 ignition {first_index + 5}, value: {ignition_s1_time}")