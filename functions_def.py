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


# example of usage
if __name__ == "__main__":
    file_path = '/home/fabiomeloni/flight_safety/traiettoria.xlsx'
    
    # Load the Excel file as two separate arrays
    string_array, numeric_array = load_excel_as_two_arrays(file_path)
    
    # Specify the column name you are looking for
    column_name = "thrust~Engine_1_Up:Rocket"
    
    # Find the index of the specified column in the string array (row 2)
    col_index = find_column_index(string_array, column_name)
    
    # Extract the corresponding column from the numeric array
    numeric_column = numeric_array[:, col_index]
    
    # Find the first and last non-zero values in the numeric column
    first_index, last_index, first_value, last_value = find_first_and_last_nonzero(numeric_column)
    
    # Print the results
    print(f"First non-zero value at row index: {first_index + 5}, value: {first_value}")
    print(f"Last non-zero value at row index: {last_index + 5}, value: {last_value}")

    # get time, altitude, state vector
    ignition_s1_time = get_time(first_index)
    print(f"Index of S1 ignition {first_index + 5}, value: {ignition_s1_time}")