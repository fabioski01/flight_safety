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

if __name__ == "__main__":
    file_path = '/home/fabiomeloni/flight_safety/traiettoria.xlsx'
    
    # Load the Excel file as two separate arrays
    string_array, numeric_array = load_excel_as_two_arrays(file_path)

    # Display the first array (strings, rows 1 to 4)
    print("String array (first 4 rows):")
    print(string_array)

    # Display the second array (numerical values, row 5 onwards)
    print("\nNumeric array (from row 5 onwards):")
    print(numeric_array[:5])  # Display first few rows for inspection

    # Print the shapes of both arrays
    print("\nShape of string array:", string_array.shape)
    print("Shape of numeric array:", numeric_array.shape)
