import random
import matplotlib.pyplot as plt
import time
import csv

def generate_cameras(num_cameras, max_entries=5, max_time_active=20, min_time_active=5, last_entry_time=100):
    cameras = []
    for _ in range(num_cameras):
        fps = random.choice([10, 15, 30])
        period = random.choice([0.5, 1, 3, 5, 10])

        # Generate random entry and exit times
        entries = []
        for _ in range(random.randint(1, max_entries)):
            entry_time = random.uniform(0, last_entry_time)  # Random entry time
            exit_time = entry_time + random.uniform(min_time_active, max_time_active)  # Active for 5 to 20 seconds
            entries.append((entry_time, exit_time))

        cameras.append({
            'fps': fps,
            'period': period,
            'entries': entries
        })
    return cameras

def simulate_frames(cameras, simulation_duration=40):
    events = []
    last_exit_time = 0
    for camera_index, camera in enumerate(cameras):
        for entry_time, exit_time in camera['entries']:
            last_exit_time = max(last_exit_time, exit_time)
            time = entry_time
            while time < exit_time and time < simulation_duration:
                # Randomly change the filtering percentage each period
                filtering_percentage = random.uniform(0.51, 0.97)

                # Calculate the number of frames generated in the period
                frames_generated = camera['fps'] * camera['period']
                # Calculate the number of frames after filtering
                frames_after_filter = max(int(frames_generated * (1 - filtering_percentage)),1)
                # Add the event to the list with the camera index
                events.append((time, frames_after_filter, camera_index))
                # Move to the next period
                time += camera['period']
    events.sort(key=lambda x: x[0])
    return events, last_exit_time

def plot_events(events, num_cameras, cameras, last_exit_time, live=False, log_filename='event_log.csv'):
    if live:
        plt.ion()  # Turn on interactive mode for live plotting
    else:
        plt.ioff()  # Ensure interactive mode is off for static plotting

    fig, ax = plt.subplots(figsize=(12, 6))
    cumulative_frames = 0

    # Generate distinct colors for each camera using the updated method
    colors = plt.get_cmap('tab10', num_cameras)

    # Initialize lists to store times and frame counts for each camera
    camera_times = [[] for _ in range(num_cameras)]
    camera_frame_counts = [[] for _ in range(num_cameras)]

    for i, event in enumerate(events):
        if live and i > 0:
            # Simulate real-time by sleeping until the next event time
            time.sleep(event[0] - events[i-1][0])

        cumulative_frames += event[1]
        camera_index = event[2]
        camera_times[camera_index].append(event[0])
        camera_frame_counts[camera_index].append(event[1])

        if live:
            ax.clear()
            # Plot all camera events
            for cam_idx in range(num_cameras):
                camera_config = cameras[cam_idx]
                ax.scatter(camera_times[cam_idx], camera_frame_counts[cam_idx], color=colors(cam_idx),
                           label=f'Camera {cam_idx + 1} (FPS: {camera_config["fps"]}, Period: {camera_config["period"]}s)', alpha=0.6)

            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Frames')
            ax.set_title('Real-Time Arrival of Frame Events')
            ax.legend(loc='upper right')
            ax.grid(True)

            # Update the text annotation with the cumulative frame count
            ax.text(0.02, 0.95, f'Total Frames: {cumulative_frames}', transform=ax.transAxes,
                    fontsize=12, verticalalignment='top', bbox=dict(facecolor='white', alpha=0.8))

            plt.draw()
            plt.pause(0.01)  # Pause to update the plot

        # Check if all cameras have exited
        if event[0] >= last_exit_time:
            print("All cameras have exited.")
            break

    # For static plotting, plot all data points at once
    if not live:
        ax.clear()
        for cam_idx in range(num_cameras):
            camera_config = cameras[cam_idx]
            ax.scatter(camera_times[cam_idx], camera_frame_counts[cam_idx], color=colors(cam_idx),
                       label=f'Camera {cam_idx + 1} (FPS: {camera_config["fps"]}, Period: {camera_config["period"]}s)', alpha=0.6)

        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Frames')
        ax.set_title('Arrival of Frame Events')
        ax.legend(loc='upper right')
        ax.grid(True)

        # Update the text annotation with the cumulative frame count
        ax.text(0.02, 0.95, f'Total Frames: {cumulative_frames}', transform=ax.transAxes,
                fontsize=12, verticalalignment='top', bbox=dict(facecolor='white', alpha=0.8))

        plt.show()  # Keep the plot window open after static plotting

    # If live, keep the plot open after the simulation
    if live:
        plt.ioff()  # Turn off interactive mode
        plt.show()  # Keep the plot window open until manually closed

    # Export the event log to a CSV file
    with open(log_filename, 'w', newline='') as csvfile:
        fieldnames = ['Time', 'Frames After Filter', 'Camera Index']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for event in events:
            writer.writerow({'Time': event[0], 'Frames After Filter': event[1], 'Camera Index': event[2]})




# Run
num_cameras = 10
cameras = generate_cameras(num_cameras)
simulated_events, last_exit_time = simulate_frames(cameras)

plot_events(simulated_events, num_cameras, cameras, last_exit_time, live=True, log_filename='event_log.csv')