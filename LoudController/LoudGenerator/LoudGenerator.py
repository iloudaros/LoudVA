import random
import matplotlib.pyplot as plt
import csv
import time

class LoudGenerator:
    def __init__(self, num_cameras, max_entries=5, max_time_active=20, min_time_active=5, last_entry_time=50):
        self.num_cameras = num_cameras
        self.max_entries = max_entries
        self.max_time_active = max_time_active
        self.min_time_active = min_time_active
        self.last_entry_time = last_entry_time
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

    def simulate_frames(self, simulation_duration=60):
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
        return events, last_exit_time

    def plot_events(self, events, last_exit_time, live=False, log_filename='event_log.csv'):
        if live:
            plt.ion()
        else:
            plt.ioff()

        fig, ax = plt.subplots(figsize=(12, 6))
        cumulative_frames = 0
        colors = plt.get_cmap('tab10', self.num_cameras)
        camera_times = [[] for _ in range(self.num_cameras)]
        camera_frame_counts = [[] for _ in range(self.num_cameras)]

        for i, event in enumerate(events):
            if live and i > 0:
                time.sleep(event[0] - events[i-1][0])

            cumulative_frames += event[1]
            camera_index = event[2]
            camera_times[camera_index].append(event[0])
            camera_frame_counts[camera_index].append(event[1])

            if live:
                ax.clear()
                for cam_idx in range(self.num_cameras):
                    camera_config = self.cameras[cam_idx]
                    ax.scatter(camera_times[cam_idx], camera_frame_counts[cam_idx], color=colors(cam_idx),
                               label=f'Camera {cam_idx + 1} (FPS: {camera_config["fps"]}, Period: {camera_config["period"]}s)', alpha=0.6)

                ax.set_xlabel('Time (s)')
                ax.set_ylabel('Frames')
                ax.set_title('Real-Time Arrival of Frame Events')
                ax.legend(loc='upper right')
                ax.grid(True)
                ax.text(0.02, 0.95, f'Total Frames: {cumulative_frames}', transform=ax.transAxes,
                        fontsize=12, verticalalignment='top', bbox=dict(facecolor='white', alpha=0.8))

                plt.draw()
                plt.pause(0.01)

            if event[0] >= last_exit_time:
                print("All cameras have exited.")
                break

        if not live:
            ax.clear()
            for cam_idx in range(self.num_cameras):
                camera_config = self.cameras[cam_idx]
                ax.scatter(camera_times[cam_idx], camera_frame_counts[cam_idx], color=colors(cam_idx),
                           label=f'Camera {cam_idx + 1} (FPS: {camera_config["fps"]}, Period: {camera_config["period"]}s)', alpha=0.6)

            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Frames')
            ax.set_title('Arrival of Frame Events')
            ax.legend(loc='upper right')
            ax.grid(True)
            ax.text(0.02, 0.95, f'Total Frames: {cumulative_frames}', transform=ax.transAxes,
                    fontsize=12, verticalalignment='top', bbox=dict(facecolor='white', alpha=0.8))

            plt.show()

        if live:
            plt.ioff()
            plt.show()

        with open(log_filename, 'w', newline='') as csvfile:
            fieldnames = ['Time', 'Frames After Filter', 'Camera Index']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for event in events:
                writer.writerow({'Time': event[0], 'Frames After Filter': event[1], 'Camera Index': event[2]})


if __name__ == '__main__':
    num_cameras = 6
    simulator = LoudGenerator(num_cameras)
    simulated_events, last_exit_time = simulator.simulate_frames()
    simulator.plot_events(simulated_events, last_exit_time, live=True, log_filename='event_log.csv')