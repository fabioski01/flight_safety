import pandas as pd
import numpy as np

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
    return dry_mass

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