import pandas as pd
import argparse
import sys

def convert_frequencies_to_hz(input_file, output_file):
    """
    Reads a CSV file, converts frequency columns from MHz to Hz,
    and saves the result to a new CSV file.

    Args:
        input_file (str): The path to the input CSV file.
        output_file (str): The path where the output CSV file will be saved.
    """
    try:
        # Load the data from the input CSV file into a pandas DataFrame
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        sys.exit(1)

    # Define the columns that need to be converted from MHz to Hz
    mhz_columns = ['GPU Max Frequency (MHz)', 'GPU Min Frequency (MHz)']

    # Convert MHz to Hz for the specified columns
    # 1 MHz = 1,000,000 Hz
    for col in mhz_columns:
        if col in df.columns:
            # Create a new column name with '(Hz)'
            new_col_name = col.replace('(MHz)', '(Hz)')
            # Perform the conversion
            df[new_col_name] = df[col] * 1000000
            # Drop the old column
            df.drop(columns=[col], inplace=True)
        else:
            print(f"Warning: Column '{col}' not found in the input file.")

    try:
        # Save the updated DataFrame to a new CSV file without the index
        df.to_csv(output_file, index=False)
        print(f"Successfully processed the file.")
        print(f"The updated data has been saved to '{output_file}'")
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")
        sys.exit(1)

if __name__ == '__main__':
    # Set up the argument parser
    parser = argparse.ArgumentParser(
        description="Convert frequency columns in a CSV file from MHz to Hz."
    )
    
    # Add the input and output file arguments
    parser.add_argument(
        "input_file",
        help="The path to the input CSV file."
    )
    parser.add_argument(
        "output_file",
        help="The path to save the converted output CSV file."
    )
    
    # Parse the arguments from the command line
    args = parser.parse_args()
    
    # Call the main function with the provided arguments
    convert_frequencies_to_hz(args.input_file, args.output_file)
