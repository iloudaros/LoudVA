import pandas as pd
import argparse

def merge_csv_files(performance_csv, specs_csv, output_csv):
    # Load the performance data CSV
    performance_data = pd.read_csv(performance_csv)

    # Load the specs data CSV
    specs_data = pd.read_csv(specs_csv)

    # Merge the two dataframes on the 'Directory' column
    merged_data = pd.merge(performance_data, specs_data, left_on='Directory', right_on='Device')

    # Drop the redundant 'Device' column from the specs data
    merged_data.drop(columns=['Device'], inplace=True)

    # Save the merged data to a new CSV file
    merged_data.to_csv(output_csv, index=False)
    print(f"Merged data saved to {output_csv}")

def main():
    parser = argparse.ArgumentParser(description="Merge performance and specs CSV files.")
    parser.add_argument('performance_csv', type=str, help='Path to the performance data CSV file.')
    parser.add_argument('specs_csv', type=str, help='Path to the specs data CSV file.')
    parser.add_argument('output_csv', type=str, help='Path to the output merged CSV file.')

    args = parser.parse_args()

    merge_csv_files(args.performance_csv, args.specs_csv, args.output_csv)

if __name__ == "__main__":
    main()
