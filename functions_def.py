import pandas as pd
import numpy as np

# def load_excel_as_two_arrays(file_path):
#     """
#     Function to load an Excel file as two arrays:
#     1. One for rows 1 to 4 as strings.
#     2. One for rows 5 onwards as floats.
    
#     Parameters:
#     - file_path: str : Path to the Excel file
    
#     Returns:
#     - string_array: np.ndarray : NumPy array containing the first 4 rows as strings
#     - numeric_array: np.ndarray : NumPy array containing the data from row 5 onwards as floats
#     """
#     df = pd.read_excel(file_path, header=None)
#     string_part = df.iloc[:4, :]  # Rows 1 to 4 (index 0 to 3)
#     numeric_part = df.iloc[4:, :]  # Rows 5 onwards (index 4 onwards)
    
#     string_array = string_part.to_numpy(dtype=str)
#     numeric_array = numeric_part.apply(pd.to_numeric, errors='coerce').to_numpy(dtype=float)

#     return string_array, numeric_array

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

def find_first_and_last_nonzero(numeric_column):
    """
    Function to find the first and last non-zero values in a numeric column.
    
    Parameters:
    - numeric_column: np.ndarray : 1D NumPy array representing a column of numeric values
    
    Returns:
    - first_index: int : Index of the first non-zero value
    - last_index: int : Index of the last non-zero value
    - first_value: float : First non-zero value
    - last_value: float : Last non-zero value
    """
    # Find indices where the values are non-zero
    non_zero_indices = np.nonzero(numeric_column)[0]
    
    if non_zero_indices.size == 0:
        raise ValueError("No non-zero values found in the column.")
    
    first_index = non_zero_indices[0]  # First non-zero index
    last_index = non_zero_indices[-1]  # Last non-zero index
    
    first_value = numeric_column[first_index]
    last_value = numeric_column[last_index]
    
    return first_index, last_index, first_value, last_value

def get_time(row_index):
    """
    Function to find the time of an event given its row index.
    
    Parameters:
    - row_index: int : index representing the row number which contains the event value
    
    Returns:
    - event_time: float: timestamp of the event
    """    
    # Specify the column name to find timestamp column
    column_name = "thrust~Engine_1_Up:Rocket"
    time_col_index = find_column_index(string_array, column_name)

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
