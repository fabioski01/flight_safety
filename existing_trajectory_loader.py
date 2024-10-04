import pandas as pd
import numpy as np
import csv
from functions_def import load_excel_as_two_arrays, get_state_vector, save_state_vectors_to_csv, reset_state_vectors
from tqdm import tqdm  # Import tqdm for the progress bar

# Main function to convert Excel to CSV
def trajectory_from_excel_to_csv(excel_file_path, output_csv_path, event_name):
    # Load Excel data
    string_array, numeric_array = load_excel_as_two_arrays(excel_file_path)
    
    # Reset state vector list
    reset_state_vectors()
    
    # Loop through all rows from the numeric array with progress bar
    for row_index in tqdm(range(numeric_array.shape[0]), desc="Processing rows"):
        # Extract the state vector (time, position, velocity) for the current row
        get_state_vector(row_index, string_array, numeric_array, event_name)
    
    # Save the extracted state vectors to the output CSV file
    save_state_vectors_to_csv(output_csv_path)

# Usage
if __name__ == "__main__":
    excel_file_path = '/home/fabiomeloni/flight_safety/traiettoria.xlsx'  # Change to your actual Excel file path
    output_csv_path = "state_vector_full_trajectory.csv"  # Change to your desired CSV output path
    event_name = 'full_trajectory'  # Set the event name you want to associate with this trajectory

    # Convert Excel to CSV
    trajectory_from_excel_to_csv(excel_file_path, output_csv_path, event_name)