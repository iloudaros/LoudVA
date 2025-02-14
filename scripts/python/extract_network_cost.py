import numpy as np
np.bool = bool  # Workaround for old pandas versions

import pandas as pd
import glob
import re
import os
import argparse

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Calculate network costs from Triton performance CSVs')
    parser.add_argument('input_dir', nargs='?', default=os.getcwd(),
                      help='Input directory containing CSV files (default: current directory)')
    parser.add_argument('-o', '--output', default='network_cost.csv',
                      help='Output CSV filename (default: network_cost.csv)')
    return parser.parse_args()

def extract_batch_size(filename):
    """Extracts batch size from filenames following *_<number>.csv pattern"""
    match = re.search(r'_(\d+)\.csv$', filename)
    return int(match.group(1)) if match else None

def calculate_network_cost(row):
    """Calculates total network cost from relevant columns"""
    return row['Client Send'] + row['Network+Server Send/Recv'] + row['Client Recv']

def main():
    args = parse_arguments()
    
    # Verify input directory exists
    if not os.path.isdir(args.input_dir):
        raise NotADirectoryError(f"Input directory not found: {args.input_dir}")

    # Find all CSV files with batch number suffix
    files = glob.glob(os.path.join(args.input_dir, '*_*.csv'))
    if not files:
        raise FileNotFoundError(f"No matching CSV files found in {args.input_dir}")

    processed_data = []

    for file in files:
        batch_size = extract_batch_size(os.path.basename(file))
        if batch_size is None:
            continue
            
        df = pd.read_csv(file)
        df['Network Cost (μs)'] = df.apply(calculate_network_cost, axis=1)
        df['Batch Size'] = batch_size
        
        # Select and reorder relevant columns
        df = df[['Batch Size', 'Network Cost (μs)', 'Concurrency', 'Inferences/Second', 
                 'Client Send', 'Network+Server Send/Recv',
                 'Client Recv', 'p50 latency', 'p90 latency', 'p95 latency', 'p99 latency']]
        
        processed_data.append(df)

    # Combine all data and sort by batch size then concurrency
    final_df = pd.concat(processed_data).sort_values(['Batch Size', 'Concurrency'])

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save to CSV with European format
    final_df.to_csv(args.output, index=False, sep=',', decimal='.')

if __name__ == '__main__':
    main()
