# Identify the type of mission (where do we launch, orbit, inclination). Then the key events:
#   ignition S1
#   ignition S2
#   ignition S3
#   max q
#   meco (main engine cut-off)
#   seco (second engine cut-off)
#   stage separation 1/2
#   fairing separation
#   payload capability assuming 200kg of dry mass for kick stage
# Have as an output the time, position and altitude of the key event and their relative impact point
# Having in a separate folder the state vector at each event (stage and fairing separation)
# Optional: could you generate kmz or kml files for visualization in google earth of the trajectories and the line of instantaneous impact point
# The “interesting” trajectory as a feature, will you be able to identify it?
# The size of the trajectory is not constant, same as the info available. In order to have a lean code that will be used for different application, consider this small feature and don’t extract column X thinking it will be the same info all the time 

from open_excel import load_excel_as_two_arrays

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

from functions_def import find_first_and_last_nonzero
from functions_def import find_column_index
from functions_def import get_time

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
ignition_s1_time = get_time(first_index, string_array, numeric_array) # start of S1 thrust
meco_time = get_time(last_index, string_array, numeric_array) # end of S1 thrust (main engine cut-off)
print(f"Index of S1 ignition {first_index + 5}, timestamp: {ignition_s1_time} s")
print(f"Index of MECO {last_index + 5}, timestamp: {meco_time} s")