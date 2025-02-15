import pandas as pd
import matplotlib.pyplot as plt
import argparse
import heapq
from datetime import datetime

def parse_time(time_str):
    try:
        return datetime.utcfromtimestamp(float(time_str))
    except ValueError:
        return pd.to_datetime(time_str)

def create_timeline(csv_path, output_path='timeline.png', start_time=None, end_time=None):
    # Read and process data
    df = pd.read_csv(csv_path)
    time_cols = ['Arrival Time', 'Queue Exit Time', 'Completion Time']
    df[time_cols] = df[time_cols].apply(lambda x: pd.to_datetime(x, unit='s'))
    
    # Sort by arrival time and assign rows
    df = df.sort_values('Arrival Time').reset_index(drop=True)
    heap = []
    row_map = {}
    
    for i, row in df.iterrows():
        arrival = row['Arrival Time']
        completion = row['Completion Time']
        
        # Reuse rows where possible
        if heap and heap[0][0] <= arrival:
            _, row_num = heapq.heappop(heap)
            heapq.heappush(heap, (completion, row_num))
            row_map[i] = row_num
        else:
            row_num = len(heap)
            heapq.heappush(heap, (completion, row_num))
            row_map[i] = row_num
    
    df['Row'] = df.index.map(row_map)
    
    # Filter by time range
    if start_time or end_time:
        start = start_time or df['Arrival Time'].min()
        end = end_time or df['Completion Time'].max()
        mask = ((df['Completion Time'] >= start) & 
                (df['Arrival Time'] <= end))
        df = df[mask].reset_index(drop=True)
    
    # Dynamic figure sizing
    max_row = df['Row'].max() if not df.empty else 0
    fig_height = max(8, (max_row + 1) * 0.5)
    
    # Create plot
    plt.figure(figsize=(14, fig_height))
    
    # Plot each request
    for _, row in df.iterrows():
        y = row['Row']
        plt.plot([row['Arrival Time'], row['Queue Exit Time'], row['Completion Time']],
                 [y, y, y], color='gray', alpha=0.4, linestyle='--', linewidth=1.5)
        
        markers = [
            (row['Arrival Time'], 'green', 'o', 'Arrival'),
            (row['Queue Exit Time'], 'blue', 's', 'Queue Exit'),
            (row['Completion Time'], 'red', 'X', 'Completion')
        ]
        
        for time, color, marker, label in markers:
            plt.scatter(time, y, color=color, marker=marker, s=120, 
                       edgecolor='black', label=label if _ == 0 else "")

    # Format axes
    plt.yticks(range(max_row + 1), fontsize=10)
    plt.xticks(rotation=45, fontsize=10)
    plt.xlabel('Time', fontsize=12)
    plt.ylabel('Recycled Rows', fontsize=12)
    plt.title('Request Timeline with Row Recycling', fontsize=14)
    
    # Set time bounds
    if start_time or end_time:
        plt.xlim(left=start_time, right=end_time)
    
    # Final touches
    plt.grid(True, axis='x', linestyle='--', alpha=0.6)
    plt.margins(y=0.03)
    plt.gca().xaxis_date()
    
    handles, labels = plt.gca().get_legend_handles_labels()
    plt.legend(dict(zip(labels, handles)).values(), 
               dict(zip(labels, handles)).keys(),
               loc='upper right', bbox_to_anchor=(1.15, 1))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate timeline with row recycling')
    parser.add_argument('input_csv', help='Path to input CSV file')
    parser.add_argument('-o', '--output', default='timeline.png', 
                       help='Output file path (default: timeline.png)')
    parser.add_argument('-s', '--start', help='Start time (timestamp or datetime)')
    parser.add_argument('-e', '--end', help='End time (timestamp or datetime)')
    
    args = parser.parse_args()
    start_time = parse_time(args.start) if args.start else None
    end_time = parse_time(args.end) if args.end else None
    
    create_timeline(args.input_csv, args.output, start_time, end_time)
    print(f"Compact timeline saved to {args.output}")
