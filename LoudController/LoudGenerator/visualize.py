import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_event_log(log_file_path):
    # Read the CSV file
    df = pd.read_csv(log_file_path)
    
    # Create figure with 2 subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), height_ratios=[2, 1])
    
    # Get number of unique cameras for color mapping
    num_cameras = len(df['Camera Index'].unique())
    colors = plt.get_cmap('tab10', num_cameras)
    
    # Plot camera events
    for camera_idx in range(num_cameras):
        camera_data = df[df['Camera Index'] == camera_idx]
        ax1.scatter(camera_data['Time'], 
                   camera_data['Frames After Filter'],
                   color=colors(camera_idx),
                   label=f'Camera {camera_idx + 1}',
                   alpha=0.6)
    
    # Calculate and display total frames
    total_frames = df['Frames After Filter'].sum()
    ax1.text(0.02, 0.95, f'Total Frames: {total_frames}',
             transform=ax1.transAxes,
             fontsize=12, verticalalignment='top',
             bbox=dict(facecolor='white', alpha=0.8))
    
    # Format first subplot
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Frames')
    ax1.set_title('Arrival of Frame Events')
    ax1.legend(loc='upper right')
    ax1.grid(True)
    
    # Plot throughput
    ax2.plot(df['Time'], df['Throughput'], 'r-', label='Throughput (frames/s)')
    
    # Format second subplot
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Frames/s')
    ax2.set_title('Overall Throughput')
    ax2.legend(loc='upper right')
    ax2.grid(True)
    
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    # Replace this path with the path to your event log file
    log_file_path = '/home/louduser/LoudVA/LoudController/LoudGenerator/event_log.csv'
    plot_event_log(log_file_path)
