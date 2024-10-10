import pandas as pd
import numpy as np
import csv
from functions_def import load_excel_as_two_arrays, get_state_vector, save_state_vectors_to_csv, reset_state_vectors
import os # for file pathing

# Main function to convert Excel to CSV
def trajectory_from_excel_to_csv(excel_file_path, event_name, trajectory_astos_name):
    # Create the folder for the CSV file
    folder_name = f"csv_files_{trajectory_astos_name}"
    os.makedirs(folder_name, exist_ok=True)
    
    # Define the output file path within the folder
    output_filename = os.path.join(folder_name, f"state_vector_{event_name}.csv")
    
    # Load Excel data
    string_array, numeric_array = load_excel_as_two_arrays(excel_file_path)
    
    # Reset state vector list
    reset_state_vectors()
    # Loop through all rows from the numeric array
    for row_index in range(numeric_array.shape[0]):
        # Extract the state vector (time, position, velocity) for the current row
        get_state_vector(row_index, string_array, numeric_array, event_name)
    
    # Save the extracted state vectors to the output CSV file
    save_state_vectors_to_csv(output_filename)

# Usage
# if __name__ == "__main__":
#     excel_file_path = '/home/fabiomeloni/flight_safety/traiettoria.xlsx'  # Change to your actual Excel file path
#     output_csv_path = "state_vector_full_trajectory.csv"  # Change to your desired CSV output path
#     event_name = 'full_trajectory'  # Set the event name you want to associate with this trajectory

#     # Convert Excel to CSV
#     trajectory_from_excel_to_csv(excel_file_path, output_csv_path, event_name)