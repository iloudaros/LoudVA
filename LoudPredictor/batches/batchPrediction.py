import numpy as np
import matplotlib.pyplot as plt
from collections import deque
import csv
import os
import argparse

class SimpleMovingAveragePredictor:
    def __init__(self, window_size=5):
        self.window_size = window_size
        self.time_intervals = deque(maxlen=window_size)

    def update(self, new_time):
        if self.time_intervals:
            interval = new_time - self.time_intervals[-1]
            self.time_intervals.append(new_time)
            return interval
        else:
            self.time_intervals.append(new_time)
            return None

    def predict_next_interval(self):
        if len(self.time_intervals) < 2:
            return None
        intervals = np.diff(self.time_intervals)
        return np.mean(intervals) if len(intervals) > 0 else None

def run_predictor(events, log_filename='prediction_log.csv', plot=False):
    predictor = SimpleMovingAveragePredictor(window_size=5)
    prediction_log = []

    if plot:
        plt.ion()
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.set_title('Predicted vs Actual Intervals', fontsize=16)
        ax.set_xlabel('Event Index', fontsize=12)
        ax.set_ylabel('Time Interval (s)', fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.7)

    actual_intervals = []
    predicted_intervals = []

    # Define colors using hex values
    actual_color = '#0165a0'  # Dark blue
    predicted_color = '#f4d792'  # Light yellow

    for i, event in enumerate(events):
        interval = predictor.update(event[0])
        next_interval = predictor.predict_next_interval()

        if interval is not None and next_interval is not None:
            actual_intervals.append(interval)
            predicted_intervals.append(next_interval)
            prediction_log.append((interval, next_interval))

            if plot:
                ax.clear()
                ax.plot(actual_intervals, label='Actual Intervals', marker='o', color=actual_color, linestyle='-', linewidth=2)
                ax.plot(predicted_intervals, label='Predicted Intervals', marker='x', color=predicted_color, linestyle='--', linewidth=2)
                ax.set_title('Predicted vs Actual Intervals', fontsize=16)
                ax.set_xlabel('Event Index', fontsize=12)
                ax.set_ylabel('Time Interval (s)', fontsize=12)
                ax.legend(fontsize=12)
                ax.grid(True, linestyle='--', alpha=0.7)
                plt.draw()
                plt.pause(0.01)

    if plot:
        plt.ioff()
        plt.show()

    # Determine the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(script_dir, log_filename)

    with open(log_path, 'w', newline='') as csvfile:
        fieldnames = ['Actual Interval', 'Predicted Interval']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for actual, predicted in prediction_log:
            writer.writerow({'Actual Interval': actual, 'Predicted Interval': predicted})


if __name__ == '__main__':
    import sys

    # Add the LoudGenerator directory to the system path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
    sibling_folder_path = os.path.join(parent_dir, 'LoudGenerator')
    sys.path.append(sibling_folder_path)

    import LoudGenerator as generator

    # Set up argument parser
    parser = argparse.ArgumentParser(description='Run the predictor.')
    parser.add_argument('--num_cameras', type=int, default=10, help='Number of cameras to simulate')
    parser.add_argument('--plot', action='store_true', help='Enable plotting of prediction results')
    args = parser.parse_args()

    num_cameras = args.num_cameras
    cameras = generator.generate_cameras(num_cameras)
    simulated_events, last_exit_time = generator.simulate_frames(cameras)
    run_predictor(simulated_events, log_filename='prediction_log.csv', plot=args.plot)
