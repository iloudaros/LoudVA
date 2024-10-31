import csv
import argparse
import os
import numpy as np
import matplotlib.pyplot as plt

class MovingAveragePredictor:
    def __init__(self, window_size=5):
        self.window_size = window_size
        self.frames_window = []
        self.events_window = []

    def update(self, frames, events):
        if len(self.frames_window) >= self.window_size:
            self.frames_window.pop(0)
        if len(self.events_window) >= self.window_size:
            self.events_window.pop(0)

        self.frames_window.append(frames)
        self.events_window.append(events)

    def predict_next(self):
        if len(self.frames_window) < self.window_size or len(self.events_window) < self.window_size:
            return None, None

        predicted_frames = np.mean(self.frames_window)
        predicted_events = np.mean(self.events_window)

        return predicted_frames, predicted_events

def read_monitor_log(log_filename):
    seconds = []
    frames_per_second = []
    events_per_second = []

    with open(log_filename, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            seconds.append(int(row['Second']))
            frames_per_second.append(int(row['Frames Per Second']))
            events_per_second.append(int(row['Events Per Second']))

    return seconds, frames_per_second, events_per_second

def run_frame_predictor(log_filename, window_size=5, plot=False, prediction_log_filename='frame_prediction_log.csv'):
    seconds, frames_per_second, events_per_second = read_monitor_log(log_filename)
    predictor = MovingAveragePredictor(window_size=window_size)

    predicted_frames = []
    predicted_events = []

    for frames, events in zip(frames_per_second, events_per_second):
        predictor.update(frames, events)
        pred_frames, pred_events = predictor.predict_next()

        if pred_frames is not None and pred_events is not None:
            predicted_frames.append(pred_frames)
            predicted_events.append(pred_events)

    # Adjust the seconds list to match the length of predicted data
    prediction_start_index = window_size - 1
    prediction_seconds = seconds[prediction_start_index:]

    # Write predictions to CSV
    script_dir = os.path.dirname(os.path.abspath(__file__))
    prediction_log_path = os.path.join(script_dir, prediction_log_filename)

    with open(prediction_log_path, 'w', newline='') as csvfile:
        fieldnames = ['Second', 'Predicted Frames Per Second', 'Predicted Events Per Second']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for second, pred_frames, pred_events in zip(prediction_seconds, predicted_frames, predicted_events):
            writer.writerow({
                'Second': second,
                'Predicted Frames Per Second': pred_frames,
                'Predicted Events Per Second': pred_events
            })

    print(f"Predictions logged to {prediction_log_path}")

    if plot:
        # Plot for Frames Per Second
        plt.figure(figsize=(12, 6))
        plt.plot(seconds, frames_per_second, label='Actual Frames Per Second', color='#0165a0', linestyle='-', linewidth=2)
        plt.plot(prediction_seconds, predicted_frames, label='Predicted Frames Per Second', color='#f4d792', linestyle='--', linewidth=2)
        plt.xlabel('Seconds')
        plt.ylabel('Frames Per Second')
        plt.title('Actual vs Predicted Frames Per Second')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.show()

        # Plot for Events Per Second
        plt.figure(figsize=(12, 6))
        plt.plot(seconds, events_per_second, label='Actual Events Per Second', color='#0165a0', linestyle='-', linewidth=2)
        plt.plot(prediction_seconds, predicted_events, label='Predicted Events Per Second', color='#f4d792', linestyle='--', linewidth=2)
        plt.xlabel('Seconds')
        plt.ylabel('Events Per Second')
        plt.title('Actual vs Predicted Events Per Second')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Predict frame and event rates per second using a moving average.')
    parser.add_argument('--log_filename', type=str, default='frame_monitor_log.csv', help='Path to the frame monitor log CSV file')
    parser.add_argument('--window_size', type=int, default=5, help='Window size for the moving average')
    parser.add_argument('--plot', action='store_true', help='Enable plotting of prediction results')
    parser.add_argument('--prediction_log_filename', type=str, default='frame_prediction_log.csv', help='Filename for the prediction log')
    args = parser.parse_args()

    run_frame_predictor(args.log_filename, window_size=args.window_size, plot=args.plot, prediction_log_filename=args.prediction_log_filename)
