import numpy as np
import matplotlib.pyplot as plt
import csv
import argparse
import os

def evaluate_predictions(generator_log, predictor_log):
    # Load generator log
    with open(generator_log, 'r') as file:
        reader = csv.DictReader(file)
        generator_data = [row for row in reader]

    # Load predictor log
    with open(predictor_log, 'r') as file:
        reader = csv.DictReader(file)
        predictor_data = [row for row in reader]

    actual_intervals = np.array([float(row['Actual Interval']) for row in predictor_data])
    predicted_intervals = np.array([float(row['Predicted Interval']) for row in predictor_data])

    # Calculate Mean Absolute Error (MAE)
    mae = np.mean(np.abs(actual_intervals - predicted_intervals))
    print(f"Mean Absolute Error (MAE): {mae:.2f} s")

    # Calculate Root Mean Square Error (RMSE)
    rmse = np.sqrt(np.mean((actual_intervals - predicted_intervals) ** 2))
    print(f"Root Mean Square Error (RMSE): {rmse:.2f} s")

    # Calculate Mean Absolute Percentage Error (MAPE)
    epsilon = np.finfo(float).eps
    mape = np.mean(np.abs((actual_intervals - predicted_intervals) / (actual_intervals + epsilon))) * 100
    print(f"Mean Absolute Percentage Error (MAPE): {mape:.2f}%")

    # Plot actual vs predicted intervals
    plt.figure(figsize=(10, 5))

    # Define colors using hex values
    actual_color = '#0165a0'  # Dark blue
    predicted_color = '#f4d792'  # Light yellow

    plt.plot(actual_intervals, label='Actual Intervals', marker='o', color=actual_color, linestyle='-', linewidth=2)
    plt.plot(predicted_intervals, label='Predicted Intervals', marker='x', color=predicted_color, linestyle='--', linewidth=2)
    plt.xlabel('Event Index')
    plt.ylabel('Time Interval (s)')
    plt.title('Actual vs Predicted Time Intervals')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evaluate predictions against actual intervals.')
    
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add arguments with default values
    parser.add_argument('--generator_log', type=str, default=os.path.join(script_dir, 'event_log.csv'),
                        help='Path to the generator log CSV file (default: event_log.csv in the script directory)')
    parser.add_argument('--predictor_log', type=str, default=os.path.join(script_dir, '../interval_prediction_log.csv'),
                        help='Path to the predictor log CSV file (default: prediction_log.csv in the script directory)')
    
    args = parser.parse_args()
    
    evaluate_predictions(args.generator_log, args.predictor_log)