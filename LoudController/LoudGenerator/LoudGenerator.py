import random
import matplotlib.pyplot as plt
import csv
import time

class LoudGenerator:
    def __init__(self, num_cameras, max_entries=5, max_time_active=200, min_time_active=5, last_entry_time=200, max_overall_throughput=None):
        self.num_cameras = num_cameras
        self.max_entries = max_entries
        self.max_time_active = max_time_active
        self.min_time_active = min_time_active
        self.last_entry_time = last_entry_time
        self.max_overall_throughput = max_overall_throughput
        self.cameras = self.generate_cameras()

    def generate_cameras(self):
        cameras = []
        for _ in range(self.num_cameras):
            fps = random.choice([10, 15, 30])
            period = random.choice([0.5, 1, 3, 5, 10])
            entries = []
            for _ in range(random.randint(1, self.max_entries)):
                entry_time = random.uniform(0, self.last_entry_time)
                exit_time = entry_time + random.uniform(self.min_time_active, self.max_time_active)
                entries.append((entry_time, exit_time))
            cameras.append({'fps': fps, 'period': period, 'entries': entries})
        return cameras

    def simulate_frames(self, simulation_duration=300):
        events = []
        last_exit_time = 0
        for camera_index, camera in enumerate(self.cameras):
            for entry_time, exit_time in camera['entries']:
                last_exit_time = max(last_exit_time, exit_time)
                time = entry_time
                while time < exit_time and time < simulation_duration:
                    filtering_percentage = random.uniform(0.51, 0.97)
                    frames_generated = camera['fps'] * camera['period']
                    frames_after_filter = max(int(frames_generated * (1 - filtering_percentage)), 1)
                    events.append((time, frames_after_filter, camera_index))
                    time += camera['period']
        events.sort(key=lambda x: x[0])
        
        if self.max_overall_throughput is not None:
            events = self.adjust_throughput(events)
            
        return events, last_exit_time

    def adjust_throughput(self, events, window_size=1):
        """
        Adjust events to ensure max_overall_throughput is not exceeded.
        """
        if not events:
            return events

        adjusted_events = []
        current_window = []
        current_window_start = events[0][0]

        for event in events:
            time, frames, camera_index = event
            
            # Remove events from window that are outside the current time window
            while current_window and current_window[0][0] < time - window_size:
                current_window.pop(0)
            
            # Add current event to window
            current_window.append(event)
            
            # Calculate current throughput in window
            window_frames = sum(e[1] for e in current_window)
            current_throughput = window_frames / window_size
            
            if current_throughput > self.max_overall_throughput:
                # Calculate reduction factor
                reduction_factor = self.max_overall_throughput / current_throughput
                # Adjust frames for current event
                adjusted_frames = max(1, int(frames * reduction_factor))
                adjusted_events.append((time, adjusted_frames, camera_index))
            else:
                adjusted_events.append(event)

        return adjusted_events

    def calculate_throughput(self, events, window_size=5):
        """
        Calculate throughput for all events using a sliding window.
        """
        if not events:
            return [], []

        throughput_times = []
        throughput_values = []
        
        for i, (current_time, _, _) in enumerate(events):
            window_start = max(0, current_time - window_size)
            # Sum frames in current window
            window_frames = sum(frame for t, frame, _ in events[:i+1] 
                              if window_start <= t <= current_time)
            throughput = window_frames / window_size
            throughput_times.append(current_time)
            throughput_values.append(throughput)

        return throughput_times, throughput_values

    def plot_events(self, events, last_exit_time, plot=True, live=False, log_filename='event_log.csv'):
        if live:
            plt.ion()
        else:
            plt.ioff()

        # Create figure with 2 subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), height_ratios=[2, 1])
        cumulative_frames = 0
        colors = plt.get_cmap('tab10', self.num_cameras)
        camera_times = [[] for _ in range(self.num_cameras)]
        camera_frame_counts = [[] for _ in range(self.num_cameras)]
        
        # For throughput calculation
        window_size = 5  # seconds for moving average
        all_times = [event[0] for event in events]
        all_frames = [event[1] for event in events]
        throughput_times = []
        throughput_values = []

        for i, event in enumerate(events):
            if live and i > 0:
                time.sleep(event[0] - events[i-1][0])

            cumulative_frames += event[1]
            camera_index = event[2]
            camera_times[camera_index].append(event[0])
            camera_frame_counts[camera_index].append(event[1])

            # Calculate throughput
            current_time = event[0]
            window_start = max(0, current_time - window_size)
            window_frames = sum(frame for t, frame, _ in events[:i+1] 
                              if window_start <= t <= current_time)
            throughput = window_frames / window_size
            throughput_times.append(current_time)
            throughput_values.append(throughput)

            if live:
                ax1.clear()
                ax2.clear()
                
                # Plot camera events
                for cam_idx in range(self.num_cameras):
                    camera_config = self.cameras[cam_idx]
                    ax1.scatter(camera_times[cam_idx], camera_frame_counts[cam_idx], 
                              color=colors(cam_idx),
                              label=f'Camera {cam_idx + 1} (FPS: {camera_config["fps"]}, Period: {camera_config["period"]}s)', 
                              alpha=0.6)

                # Plot throughput
                ax2.plot(throughput_times, throughput_values, 'r-', label='Throughput (frames/s)')
                
                self._format_plots(ax1, ax2, cumulative_frames)
                plt.draw()
                plt.pause(0.01)

            if event[0] >= last_exit_time:
                print("All cameras have exited.")
                break

        if not live:
            ax1.clear()
            ax2.clear()
            
            # Plot final camera events
            for cam_idx in range(self.num_cameras):
                camera_config = self.cameras[cam_idx]
                ax1.scatter(camera_times[cam_idx], camera_frame_counts[cam_idx], 
                          color=colors(cam_idx),
                          label=f'Camera {cam_idx + 1} (FPS: {camera_config["fps"]}, Period: {camera_config["period"]}s)', 
                          alpha=0.6)

            # Plot final throughput
            ax2.plot(throughput_times, throughput_values, 'r-', label='Throughput (frames/s)')
            
            self._format_plots(ax1, ax2, cumulative_frames)

            if plot:
                plt.tight_layout()
                plt.show()

        if live:
            plt.ioff()
            plt.show()

        # Save to CSV
        with open(log_filename, 'w', newline='') as csvfile:
            fieldnames = ['Time', 'Frames After Filter', 'Camera Index', 'Throughput']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for i, event in enumerate(events):
                writer.writerow({
                    'Time': event[0], 
                    'Frames After Filter': event[1], 
                    'Camera Index': event[2],
                    'Throughput': throughput_values[i] if i < len(throughput_values) else 0
                })

    def _format_plots(self, ax1, ax2, cumulative_frames):
        # Format first subplot (camera events)
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Frames')
        ax1.set_title('Arrival of Frame Events')
        ax1.legend(loc='upper right')
        ax1.grid(True)
        ax1.text(0.02, 0.95, f'Total Frames: {cumulative_frames}', 
                transform=ax1.transAxes,
                fontsize=12, verticalalignment='top', 
                bbox=dict(facecolor='white', alpha=0.8))

        # Format second subplot (throughput)
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Frames/s')
        ax2.set_title('Overall Throughput')
        ax2.legend(loc='upper right')
        ax2.grid(True)


if __name__ == '__main__':
    num_cameras = 2
    max_overall_throughput = 40
    simulator = LoudGenerator(num_cameras, max_overall_throughput=max_overall_throughput)
    simulated_events, last_exit_time = simulator.simulate_frames()
    simulator.plot_events(simulated_events, last_exit_time, plot=False, live=False, log_filename='/home/louduser/LoudVA/LoudController/LoudGenerator/event_log.csv')