"""
TASK:

Identify the type of mission (where do we launch, orbit, inclination). Then the key events:
 - ignition S1
 - ignition S2
 - ignition S3
 - max q
 - meco (main engine cut-off)
 - seco (second engine cut-off)
 - stage separation 1/2
 - fairing separation
 - payload capability assuming 200kg of dry mass for kick stage

Have as an output the time, position and altitude of the key event and their relative impact point.

Having in a separate folder the state vector at each event (stage and fairing separation).

Optional: could you generate kmz or kml files for visualization in google earth of the trajectories 
and the line of instantaneous impact point.

The “interesting” trajectory as a feature, will you be able to identify it?
The size of the trajectory is not constant, same as the info available. In order to have a lean code 
that will be used for different application, consider this small feature and do not extract column X
thinking it will be the same info all the time.
"""

from functions_def import load_excel_as_two_arrays

file_path = '/home/fabiomeloni/flight_safety/traiettoria.xlsx'

# Load the Excel file as two separate arrays
string_array, numeric_array = load_excel_as_two_arrays(file_path)

# Ignition S1 engine based on thrust of engine 1, and main engine cut-off (MECO)

from functions_def import find_first_and_last_nonzero
from functions_def import find_column_index
from functions_def import get_time
from functions_def import get_altitude
from functions_def import get_state_vector
from functions_def import save_state_vectors_to_csv
from functions_def import reset_state_vectors
from impact_with_drag_propagator import propagate_trajectory_with_drag
from existing_trajectory_loader import trajectory_from_excel_to_csv
from j2000_to_kml import propagate_and_convert

# Specify the column name you are looking for
column_name = "thrust~Engine_1_Up:Rocket"

# Find the first and last non-zero values in the numeric column
first_index, last_index, first_value, last_value = find_first_and_last_nonzero(column_name, string_array, numeric_array)

# get time, altitude, state vector
# time
ignition_s1_time = get_time(first_index, string_array, numeric_array) # start of S1 thrust
meco_time = get_time(last_index, string_array, numeric_array) # end of S1 thrust (main engine cut-off)

# altitude
ignition_s1_altitude = get_altitude(first_index, string_array, numeric_array) # start of S1 thrust
meco_altitude = get_altitude(last_index, string_array, numeric_array) # end of S1 thrust (main engine cut-off)

# state vector
# Specify the path to save the CSV
output_csv_path = "state_vectors.csv"
reset_state_vectors()
ignition_s1_state = get_state_vector(first_index, string_array, numeric_array, "ignition_s1") # start of S1 thrust
meco_state = get_state_vector(last_index, string_array, numeric_array, "meco") # end of S1 thrust (main engine cut-off)
save_state_vectors_to_csv(output_csv_path)

print(f"S1 ignition index: {first_index + 5},    timestamp: {ignition_s1_time} s,                altitude: {ignition_s1_altitude} km,   state vector: {ignition_s1_state} km-km/s")
print(f"MECO index: {last_index + 5},         timestamp: {meco_time} s,   altitude: {meco_altitude} km,     state vector: {meco_state} km-km/s")

# Ignition S2 engine based on thrust of engine 2, and second engine cut-off (SECO)

# Specify the column name you are looking for
column_name = "thrust~Engine_2_Linear:Rocket"

# Find the first and last non-zero values in the numeric column
first_index, last_index, first_value, last_value = find_first_and_last_nonzero(column_name, string_array, numeric_array)

# get time, altitude, state vector
# time
ignition_s2_time = get_time(first_index, string_array, numeric_array) # start of S2 thrust
seco_time = get_time(last_index, string_array, numeric_array) # end of S2 thrust (second engine cut-off)

# altitude
ignition_s2_altitude = get_altitude(first_index, string_array, numeric_array) # start of S2 thrust
seco_altitude = get_altitude(last_index, string_array, numeric_array) # end of S2 thrust (second engine cut-off)

# state vector
ignition_s2_state = get_state_vector(first_index, string_array, numeric_array, "ignition_s2") # start of S2 thrust
seco_state = get_state_vector(last_index, string_array, numeric_array, "seco") # end of S2 thrust (second engine cut-off)
save_state_vectors_to_csv(output_csv_path)

print(f"S2 ignition index: {first_index + 5},    timestamp: {ignition_s2_time} s,    altitude: {ignition_s2_altitude} km,   state vector: {ignition_s2_state} km-km/s")
print(f"SECO index: {last_index + 5},           timestamp: {seco_time} s,    altitude: {seco_altitude} km,   state vector: {seco_state} km-km/s")

# Ignition S3 engine based on thrust of engine 3, and third engine cut-off (TECO)

# Specify the column name you are looking for
column_name = "thrust~Engine_3_Linear:Rocket"

# Find the first and last non-zero values in the numeric column
first_index, last_index, first_value, last_value = find_first_and_last_nonzero(column_name, string_array, numeric_array)

# get time, altitude, state vector
# time
ignition_s3_time = get_time(first_index, string_array, numeric_array) # start of S3 thrust
teco_time = get_time(last_index, string_array, numeric_array) # end of S3 thrust (second engine cut-off)

# altitude
ignition_s3_altitude = get_altitude(first_index, string_array, numeric_array) # start of S3 thrust
teco_altitude = get_altitude(last_index, string_array, numeric_array) # end of S3 thrust (second engine cut-off)

# state vector
ignition_s3_state = get_state_vector(first_index, string_array, numeric_array, "ignition_s3") # start of S3 thrust
teco_state = get_state_vector(last_index, string_array, numeric_array, "teco") # end of S3 thrust (second engine cut-off)
save_state_vectors_to_csv(output_csv_path)

print(f"S3 ignition index: {first_index + 5},     timestamp: {ignition_s3_time} s,    altitude: {ignition_s3_altitude} km,   state vector: {ignition_s3_state} km-km/s")
print(f"TECO index: {last_index + 5},           timestamp: {teco_time} s,    altitude: {teco_altitude},      state vector: {teco_state} km-km/s")

# Stage Separation S1/S2, Fairing Separation during S2, and Separation S2/S3

from functions_def import find_multiple_phase_transitions

# Specify the column name you are looking for
column_name = "dimension_x~Rocket" # looking at the length of the launcher to see when the separation happens (and the length decreases)

# Find the transitions between constant phases and decreasing values
transition_indices, constant_values = find_multiple_phase_transitions(column_name, string_array, numeric_array)

s1s2_separation_index = transition_indices[0] # separation of S1 and S2
s2fairing_separation_index = transition_indices[1] # separation of fairing during S2 flight
s2s3_separation_index = transition_indices[2] # separation of S2 and S3

s1s2_separation_value = constant_values[0] # BEFORE separation of S1 and S2
s2fairing_separation_value = constant_values[1] # BEFORE separation of fairing during S2 flight, AFTER S1 separation
s2s3_separation_value = constant_values[2] # BEFORE separation of S2 and S3, AFTER s2 fairing separation
s3_final_value = constant_values[3] # AFTER separation of S3
 
# get time, altitude, state vector
# time
s1s2_separation_time = get_time(s1s2_separation_index, string_array, numeric_array) # S1-S2 separation time
s2fairing_separation_time = get_time(s2fairing_separation_index, string_array, numeric_array) # fairing separation time
s2s3_separation_time = get_time(s2s3_separation_index, string_array, numeric_array) # S2-S3 separation time

# altitude
s1s2_separation_altitude = get_altitude(s1s2_separation_index, string_array, numeric_array) # S1-S2 separation altitude
s2fairing_separation_altitude = get_altitude(s2fairing_separation_index, string_array, numeric_array) # fairing separation altitude
s2s3_separation_altitude = get_altitude(s2s3_separation_index, string_array, numeric_array) # S2-S3 separation altitude

# state vector
s1s2_separation_state = get_state_vector(s1s2_separation_index, string_array, numeric_array, "s1s2_separation") # S1-S2 separation state vector
s2fairing_separation_state = get_state_vector(s2fairing_separation_index, string_array, numeric_array, "s2fairing_separation") # fairing separation state vector
s2s3_separation_state = get_state_vector(s2s3_separation_index, string_array, numeric_array, "s2s3_separation") # S2-S3 separation state vector
save_state_vectors_to_csv(output_csv_path)

# the +5 for the infdex is due to the first 4 rows of the excel being occupied by headings
print(f"S1/S2 separation index: {s1s2_separation_index + 5},                  timestamp: {s1s2_separation_time} s,    altitude: {s1s2_separation_altitude} km, Previous S1 rocket length: {s1s2_separation_value} m,                 New S2 rocket length: {s2fairing_separation_value} m,                 state vector: {s2fairing_separation_state} km-km/s")
print(f"Fairing separation (during S2) index: {s2fairing_separation_index + 5},    timestamp: {s2fairing_separation_time} s,    altitude: {s2fairing_separation_altitude} km, Previous S2 rocket length with fairing: {s2fairing_separation_value} m,    New S2 rocket length without fairing: {s2s3_separation_value} m,  state vector: {s2s3_separation_state} km-km/s")
print(f"S2/S3 separation index: {s2s3_separation_index + 5},                  timestamp: {s2s3_separation_time} s,    altitude: {s2s3_separation_altitude} km, Previous S2 rocket length without fairing: {s2s3_separation_value} m,  New S3 rocket length: {s3_final_value} m,     state vector: {s2s3_separation_state} km-km/s")

# Maximum Dynamic Pressure (Q) Event

from functions_def import find_max

column_name = "dynamic_pressure~Rocket"
max_index, max_value = find_max(column_name, string_array, numeric_array)

maxQ_time = get_time(max_index, string_array, numeric_array)
maxQ_altitude = get_altitude(max_index, string_array, numeric_array)
maxQ_state = get_state_vector(max_index, string_array, numeric_array, "maxQ")
save_state_vectors_to_csv(output_csv_path)

print(f"Maximum value of Dynamic Pressure: {max_value} Pa, excel row index: {max_index+5}, timestamp: {maxQ_time} s, altitude: {maxQ_altitude} km, state vector: {maxQ_state} km-km/s")

# Payload Capability assuming 200 kg of dry-mass for the kick-stage (S3)

column_names = ["mass_total~Rocket", "PROP_MASS~Stage_3:Rocket"] # total mass of rocket (Mg) in column221 HM, propellant mass of stage 3 of rocket (Kg) in column 252 IR
row_indexes = [find_column_index(string_array, column_name) for column_name in column_names] # first is the total, second is the s3 prop propellant mass
final_masses = [numeric_array[-1, row_index] for row_index in row_indexes] # first is the final total mass, second is the final s3 propellant mass
kick_stage_dry_mass = 200 # kg, from assumption, in reality it should be around 350 kg
payload_mass = final_masses[0]*1e3 - (kick_stage_dry_mass + final_masses[1]) # final total mass (in Mg converted to kg) minus the dry mass and the final propellant mass
print(f"total final mass: {final_masses[0]*1e3} kg, final propellant mass: {final_masses[1]} kg, assumed s3 inert mass: {kick_stage_dry_mass} kg, resulting payload mass: {payload_mass} kg")

#### Propagating state vectors for separation trajectories, and loading full trajectory of rocket to csv
# Example usage S1-S2
event_name = 's1s2_separation'  # Define the event name you want to propagate from
propagate_trajectory_with_drag(event_name, surface_area=28.1175, mass=((1.79408515641864E+01 - 1.23e1)*1e3)) 
# eg for S1 length is 8.15 and diameter is 3.45m, Cd is ~1 for Reynolds <2*10^5 Then it falls to 0.2-0.3. For flow speed=0.8km/s the Re=7*10^6, which would be Re=0.3 S1 dry mass which is improvisely subtracted from total rocket mass (Mg to Kg)

# Example usage S2-S3
event_name = 's2s3_separation'  # Define the event name you want to propagate from
propagate_trajectory_with_drag(event_name, surface_area=7.18, mass=((3.01735153404769E+00 -  1.08735152707548E+00)*1e3)) 
# eg for S2 length is 3.338m and diameter is 2.15m, mass is S2 dry mass which is improvisely subtracted from total rocket mass (Mg to Kg)

# Example usage S2-fairing
event_name = 's2fairing_separation'  # Define the event name you want to propagate from
propagate_trajectory_with_drag(event_name, surface_area=17.2, mass = (( 1.04228914258135E+01 - 1.01628914258135E+01)*1e3)) 
# eg for fairing length L3 is 8m and diameter is 2.15m, mass is fairing dry mass which is improvisely subtracted from total rocket mass (Mg to Kg)

# Full trajectory
excel_file_path = '/home/fabiomeloni/flight_safety/traiettoria.xlsx'  # Change to your actual Excel file path
output_csv_path = "state_vector_full_trajectory.csv"  # Change to your desired CSV output path
event_name = 'full_trajectory'  # Set the event name you want to associate with this trajectory
# Convert Excel to CSV
trajectory_from_excel_to_csv(excel_file_path, output_csv_path, event_name)
print(f"Full trajectory successfully converted to {output_csv_path}")

#### Exporting KML for trajectories
event_names = ['drag_s1s2_separation', 'drag_s2fairing_separation', 'drag_s2s3_separation', 'full_trajectory']
csv_filenames = []
for event_name in event_names:
    if event_name == 'full_trajectory':
        csv_filename = f"state_vector_{event_name}.csv"
    else:
        csv_filename = f"propagated_state_vector_{event_name}.csv"  # Make sure this file exists
    csv_filenames.append(csv_filename)
for event_name, csv_filename in zip(event_names, csv_filenames):
    propagate_and_convert(csv_filename, event_name)
    # print(f'exported KML of {event_name} as {csv_filename}')