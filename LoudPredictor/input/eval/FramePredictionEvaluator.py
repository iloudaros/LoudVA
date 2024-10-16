import csv
import argparse
import numpy as np
import matplotlib.pyplot as plt

def read_log_file(log_filename, is_prediction=False):
    seconds = []
    frames_per_second = []
    events_per_second = []

    with open(log_filename, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            seconds.append(int(row['Second']))
            frames_per_second.append(float(row['Predicted Frames Per Second'] if is_prediction else row['Frames Per Second']))
            events_per_second.append(float(row['Predicted Events Per Second'] if is_prediction else row['Events Per Second']))

    return seconds, frames_per_second, events_per_second

def evaluate_predictions(actual_log_filename, prediction_log_filename, plot=False):
    actual_seconds, actual_frames, actual_events = read_log_file(actual_log_filename)
    prediction_seconds, predicted_frames, predicted_events = read_log_file(prediction_log_filename, is_prediction=True)

    # Ensure both logs have the same length by trimming the actual data
    actual_frames = actual_frames[len(actual_frames) - len(predicted_frames):]
    actual_events = actual_events[len(actual_events) - len(predicted_events):]

    # Calculate errors
    mae_frames = np.mean(np.abs(np.array(actual_frames) - np.array(predicted_frames)))
    rmse_frames = np.sqrt(np.mean((np.array(actual_frames) - np.array(predicted_frames))**2))

    # Avoid division by zero in MAPE calculation
    actual_frames_array = np.array(actual_frames)
    non_zero_frames_mask = actual_frames_array != 0
    mape_frames = np.mean(np.abs((actual_frames_array[non_zero_frames_mask] - np.array(predicted_frames)[non_zero_frames_mask]) / actual_frames_array[non_zero_frames_mask])) * 100

    mae_events = np.mean(np.abs(np.array(actual_events) - np.array(predicted_events)))
    rmse_events = np.sqrt(np.mean((np.array(actual_events) - np.array(predicted_events))**2))

    actual_events_array = np.array(actual_events)
    non_zero_events_mask = actual_events_array != 0
    mape_events = np.mean(np.abs((actual_events_array[non_zero_events_mask] - np.array(predicted_events)[non_zero_events_mask]) / actual_events_array[non_zero_events_mask])) * 100

    print(f"Frames - MAE: {mae_frames:.2f}, RMSE: {rmse_frames:.2f}, MAPE: {mape_frames:.2f}%")
    print(f"Events - MAE: {mae_events:.2f}, RMSE: {rmse_events:.2f}, MAPE: {mape_events:.2f}%")

    if plot:
        plt.figure(figsize=(12, 6))
        plt.plot(actual_seconds, actual_frames, label='Actual Frames Per Second', color='#0165a0', linestyle='-', linewidth=2)
        plt.plot(prediction_seconds, predicted_frames, label='Predicted Frames Per Second', color='green', linestyle='--', linewidth=2)
        plt.plot(actual_seconds, actual_events, label='Actual Events Per Second', color='#f4d792', linestyle='-', linewidth=2)
        plt.plot(prediction_seconds, predicted_events, label='Predicted Events Per Second', color='orange', linestyle='--', linewidth=2)
        plt.xlabel('Seconds')
        plt.ylabel('Count')
        plt.title('Actual vs Predicted Frames and Events Per Second')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evaluate frame and event predictions.')
    parser.add_argument('--actual_log_filename', type=str, default='frame_monitor_log.csv', help='Path to the actual frame monitor log CSV file')
    parser.add_argument('--prediction_log_filename', type=str, default='frame_prediction_log.csv', help='Path to the prediction log CSV file')
    parser.add_argument('--plot', action='store_true', help='Enable plotting of evaluation results')
    args = parser.parse_args()

    evaluate_predictions(args.actual_log_filename, args.prediction_log_filename, plot=args.plot)
