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

from open_excel import load_excel
from functions_def import find_first_and_last_nonzero

file_path = '/home/fabiomeloni/flight_safety/traiettoria.xlsx'
df = load_excel(file_path)
print(df.shape)  # Check dimensions
print(df.head())  # Check first few rows

# Specify the column name
column_name = "thrust~Engine_1_Up:Rocket"

# Find the first and last non-zero indices
first_index, last_index = find_first_and_last_nonzero(df, column_name)

print(f"First non-zero value at row index: {first_index}")
print(f"Last non-zero value at row index: {last_index}")