import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_percentage_error
import matplotlib.pyplot as plt
import numpy as np

# Load the data
data = pd.read_csv('../data.csv')

# Convert object types to appropriate numerical types
# Assuming these columns are supposed to be numerical, convert them
data['Batch Size'] = pd.to_numeric(data['Batch Size'], errors='coerce')
data['Frequency'] = pd.to_numeric(data['Frequency'], errors='coerce')
data['GPU Max Frequency (MHz)'] = pd.to_numeric(data['GPU Max Frequency (MHz)'], errors='coerce')
data['GPU Min Frequency (MHz)'] = pd.to_numeric(data['GPU Min Frequency (MHz)'], errors='coerce')
data['GPU Number of Cores'] = pd.to_numeric(data['GPU Number of Cores'], errors='coerce')
data['Memory Speed (GB/s)'] = pd.to_numeric(data['Memory Speed (GB/s)'], errors='coerce')
data['Memory Size (GB)'] = pd.to_numeric(data['Memory Size (GB)'], errors='coerce')
data['Tensor Cores'] = pd.to_numeric(data['Tensor Cores'], errors='coerce')

# Features and target variables
features = data[['Batch Size', 'Frequency', 'Throughput', 'GPU Max Frequency (MHz)', 'GPU Min Frequency (MHz)', 'GPU Number of Cores', 'Memory Speed (GB/s)', 'Memory Size (GB)', 'Tensor Cores']]
target_energy = data['Energy']
target_latency = data['Latency']

# Identify unique devices
devices = data['Directory'].unique()

# Define introduction ratios
introduce_ratios = np.arange(0.0, 1.1, 0.1)  # Start from 0.0 to include the case where no data is introduced

# Create a figure for subplots
num_devices = len(devices)
fig, axes = plt.subplots(num_devices, 2, figsize=(14, 6 * num_devices))
fig.suptitle('MAPE vs. Device Data Introduction', fontsize=16)

for i, device_to_test in enumerate(devices):
    # Separate the data for the current device
    train_data = data[data['Directory'] != device_to_test]
    test_data = data[data['Directory'] == device_to_test]

    X_train_base = train_data[['Batch Size', 'Frequency', 'Throughput', 'GPU Max Frequency (MHz)', 'GPU Min Frequency (MHz)', 'GPU Number of Cores', 'Memory Speed (GB/s)', 'Memory Size (GB)', 'Tensor Cores']]
    y_train_energy_base = train_data['Energy']
    y_train_latency_base = train_data['Latency']

    X_test = test_data[['Batch Size', 'Frequency', 'Throughput', 'GPU Max Frequency (MHz)', 'GPU Min Frequency (MHz)', 'GPU Number of Cores', 'Memory Speed (GB/s)', 'Memory Size (GB)', 'Tensor Cores']]
    y_test_energy = test_data['Energy']
    y_test_latency = test_data['Latency']

    mape_results_energy = []
    mape_results_latency = []

    for ratio in introduce_ratios:
        if ratio == 0.0:
            # Use no data from the unseen device
            X_train_additional = pd.DataFrame(columns=X_train_base.columns)
            y_train_energy_additional = pd.Series(dtype='float64')
            y_train_latency_additional = pd.Series(dtype='float64')
        elif ratio < 1.0:
            # Introduce a portion of the removed device's data
            X_train_additional, _, y_train_energy_additional, _ = train_test_split(X_test, y_test_energy, test_size=1-ratio, random_state=42)
            _, _, y_train_latency_additional, _ = train_test_split(X_test, y_test_latency, test_size=1-ratio, random_state=42)
        else:
            # Use the entire device's data
            X_train_additional = X_test
            y_train_energy_additional = y_test_energy
            y_train_latency_additional = y_test_latency

        # Combine the base training data with the additional data
        if not X_train_additional.empty:
            X_train = pd.concat([X_train_base, X_train_additional])
            y_train_energy = pd.concat([y_train_energy_base, y_train_energy_additional])
            y_train_latency = pd.concat([y_train_latency_base, y_train_latency_additional])
        else:
            X_train = X_train_base
            y_train_energy = y_train_energy_base
            y_train_latency = y_train_latency_base

        # Train the model for energy prediction
        model_energy = XGBRegressor()
        model_energy.fit(X_train, y_train_energy)

        # Train the model for latency prediction
        model_latency = XGBRegressor()
        model_latency.fit(X_train, y_train_latency)

        # Predict and evaluate
        y_pred_energy = model_energy.predict(X_test)
        y_pred_latency = model_latency.predict(X_test)

        # Calculate MAPE
        mape_energy = mean_absolute_percentage_error(y_test_energy, y_pred_energy) * 100
        mape_latency = mean_absolute_percentage_error(y_test_latency, y_pred_latency) * 100

        mape_results_energy.append(mape_energy)
        mape_results_latency.append(mape_latency)

    # Plot results for the current device
    axes[i, 0].plot(introduce_ratios * 100, mape_results_energy, marker='o', color='#0165a0', linestyle='-')
    axes[i, 0].set_title(f'Energy MAPE for {device_to_test}')
    axes[i, 0].set_xlabel('Percentage of Device Data Introduced (%)')
    axes[i, 0].set_ylabel('MAPE (Energy) %')

    axes[i, 1].plot(introduce_ratios * 100, mape_results_latency, marker='o', color='#f4d792', linestyle='-')
    axes[i, 1].set_title(f'Latency MAPE for {device_to_test}')
    axes[i, 1].set_xlabel('Percentage of Device Data Introduced (%)')
    axes[i, 1].set_ylabel('MAPE (Latency) %')

plt.tight_layout(rect=[0, 0.03, 1, 0.95])  # Adjust layout to make space for the main title
plt.show()
