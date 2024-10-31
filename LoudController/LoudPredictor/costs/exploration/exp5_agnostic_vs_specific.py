import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_percentage_error
import matplotlib.pyplot as plt
import numpy as np

# Load the data
data = pd.read_csv('data.csv')

# Features and target variables
features = data[['Batch Size', 'Frequency', 'Throughput', 'GPU Max Frequency (MHz)', 'GPU Min Frequency (MHz)', 'GPU Number of Cores', 'Memory Speed (GB/s)', 'Memory Size (GB)', 'Tensor Cores']]
target_energy = data['Energy']
target_latency = data['Latency']

# Identify unique devices
devices = data['Directory'].unique()

# Define the number of samples to introduce at each step
num_samples_to_introduce = 10  # You can adjust this number based on your dataset size

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

    mape_results_energy_combined = []
    mape_results_latency_combined = []
    mape_results_energy_unseen_only = []
    mape_results_latency_unseen_only = []

    # Initial step: Train with no data from the unseen device
    model_energy = XGBRegressor()
    model_energy.fit(X_train_base, y_train_energy_base)
    y_pred_energy = model_energy.predict(X_test)
    mape_energy = mean_absolute_percentage_error(y_test_energy, y_pred_energy) * 100
    mape_results_energy_combined.append(mape_energy)

    model_latency = XGBRegressor()
    model_latency.fit(X_train_base, y_train_latency_base)
    y_pred_latency = model_latency.predict(X_test)
    mape_latency = mean_absolute_percentage_error(y_test_latency, y_pred_latency) * 100
    mape_results_latency_combined.append(mape_latency)

    # Calculate the number of steps based on the number of samples in the test set
    num_steps = len(X_test) // num_samples_to_introduce

    for step in range(1, num_steps + 1):
        # Determine the number of samples to use in this step
        num_samples = step * num_samples_to_introduce

        # Randomly select the samples from the test set
        X_train_additional = X_test.sample(n=num_samples, random_state=42)
        y_train_energy_additional = y_test_energy.loc[X_train_additional.index]
        y_train_latency_additional = y_test_latency.loc[X_train_additional.index]

        # Combine the base training data with the additional data
        X_train_combined = pd.concat([X_train_base, X_train_additional])
        y_train_energy_combined = pd.concat([y_train_energy_base, y_train_energy_additional])
        y_train_latency_combined = pd.concat([y_train_latency_base, y_train_latency_additional])

        # Train the model for energy prediction with combined data
        model_energy_combined = XGBRegressor()
        model_energy_combined.fit(X_train_combined, y_train_energy_combined)

        # Train the model for latency prediction with combined data
        model_latency_combined = XGBRegressor()
        model_latency_combined.fit(X_train_combined, y_train_latency_combined)

        # Predict and evaluate with combined data
        y_pred_energy_combined = model_energy_combined.predict(X_test)
        y_pred_latency_combined = model_latency_combined.predict(X_test)

        # Calculate MAPE with combined data
        mape_energy_combined = mean_absolute_percentage_error(y_test_energy, y_pred_energy_combined) * 100
        mape_latency_combined = mean_absolute_percentage_error(y_test_latency, y_pred_latency_combined) * 100

        mape_results_energy_combined.append(mape_energy_combined)
        mape_results_latency_combined.append(mape_latency_combined)

        # Train the model for energy prediction with only unseen data
        model_energy_unseen_only = XGBRegressor()
        model_energy_unseen_only.fit(X_train_additional, y_train_energy_additional)

        # Train the model for latency prediction with only unseen data
        model_latency_unseen_only = XGBRegressor()
        model_latency_unseen_only.fit(X_train_additional, y_train_latency_additional)

        # Predict and evaluate with only unseen data
        y_pred_energy_unseen_only = model_energy_unseen_only.predict(X_test)
        y_pred_latency_unseen_only = model_latency_unseen_only.predict(X_test)

        # Calculate MAPE with only unseen data
        mape_energy_unseen_only = mean_absolute_percentage_error(y_test_energy, y_pred_energy_unseen_only) * 100
        mape_latency_unseen_only = mean_absolute_percentage_error(y_test_latency, y_pred_latency_unseen_only) * 100

        mape_results_energy_unseen_only.append(mape_energy_unseen_only)
        mape_results_latency_unseen_only.append(mape_latency_unseen_only)

    # Plot results for the current device
    x_values = range(0, num_samples_to_introduce * (num_steps + 1), num_samples_to_introduce)
    axes[i, 0].plot(x_values, mape_results_energy_combined, marker='o', color='#0165a0', linestyle='-', label='Combined')
    axes[i, 0].plot(x_values[1:], mape_results_energy_unseen_only, marker='x', color='#f4d792', linestyle='--', label='Unseen Only')
    axes[i, 0].set_title(f'Energy MAPE for {device_to_test}')
    axes[i, 0].set_xlabel('Number of Device Data Points Introduced')
    axes[i, 0].set_ylabel('MAPE (Energy) %')
    axes[i, 0].legend()

    axes[i, 1].plot(x_values, mape_results_latency_combined, marker='o', color='#0165a0', linestyle='-', label='Combined')
    axes[i, 1].plot(x_values[1:], mape_results_latency_unseen_only, marker='x', color='#f4d792', linestyle='--', label='Unseen Only')
    axes[i, 1].set_title(f'Latency MAPE for {device_to_test}')
    axes[i, 1].set_xlabel('Number of Device Data Points Introduced')
    axes[i, 1].set_ylabel('MAPE (Latency) %')
    axes[i, 1].legend()

plt.tight_layout(rect=[0, 0.03, 1, 0.95])  # Adjust layout to make space for the main title
plt.show()
