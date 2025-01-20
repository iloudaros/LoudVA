import os
import sys
import argparse
import csv
from collections import defaultdict
import matplotlib.pyplot as plt

def calculate_frame_and_event_rates(events, simulation_duration):
    frame_counts = defaultdict(int)
    event_counts = defaultdict(int)

    for event in events:
        time, frames, _ = event
        second = int(time)  # Convert time to integer seconds
        frame_counts[second] += frames
        event_counts[second] += 1

    # Calculate total frames and events per second
    total_frames_per_second = {second: frame_counts[second] for second in range(simulation_duration)}
    total_events_per_second = {second: event_counts[second] for second in range(simulation_duration)}

    return total_frames_per_second, total_events_per_second

def run_frame_monitor(events, simulation_duration, log_filename='frame_monitor_log.csv', plot=False):
    total_frames_per_second, total_events_per_second = calculate_frame_and_event_rates(events, simulation_duration)

    # Determine the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(script_dir, log_filename)

    # Write results to CSV
    with open(log_path, 'w', newline='') as csvfile:
        fieldnames = ['Second', 'Frames Per Second', 'Events Per Second']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for second in range(simulation_duration):
            writer.writerow({
                'Second': second,
                'Frames Per Second': total_frames_per_second.get(second, 0),
                'Events Per Second': total_events_per_second.get(second, 0)
            })

    print(f"Frame and event rates logged to {log_path}")

    # Plotting
    if plot:
        seconds = list(range(simulation_duration))
        frames = [total_frames_per_second.get(second, 0) for second in seconds]
        events = [total_events_per_second.get(second, 0) for second in seconds]

        plt.figure(figsize=(12, 6))
        plt.plot(seconds, frames, label='Frames Per Second', color='#0165a0', linestyle='-', linewidth=2)
        plt.plot(seconds, events, label='Events Per Second', color='#f4d792', linestyle='--', linewidth=2)
        plt.xlabel('Seconds')
        plt.ylabel('Count')
        plt.title('Frames and Events Per Second')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.show()

if __name__ == '__main__':
    # Add the LoudGenerator directory to the system path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
    sibling_folder_path = os.path.join(parent_dir, 'LoudGenerator')
    sys.path.append(sibling_folder_path)

    import LoudGenerator as generator

    # Set up argument parser
    parser = argparse.ArgumentParser(description='Monitor frames and events per second.')
    parser.add_argument('--num_cameras', type=int, default=10, help='Number of cameras to simulate')
    parser.add_argument('--simulation_duration', type=int, default=120, help='Duration of the simulation in seconds')
    parser.add_argument('--plot', action='store_true', help='Enable plotting of frame and event results')
    args = parser.parse_args()

    num_cameras = args.num_cameras
    simulation_duration = args.simulation_duration
    cameras = generator.generate_cameras(num_cameras)
    simulated_events, last_exit_time = generator.simulate_frames(cameras)

    run_frame_monitor(simulated_events, simulation_duration, log_filename='frame_monitor_log.csv', plot=args.plot)
