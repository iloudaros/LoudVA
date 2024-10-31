import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_percentage_error
import matplotlib.pyplot as plt
import numpy as np

# Load the data
data = pd.read_csv('../data.csv')

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

    mape_results_energy = []
    mape_results_latency = []

    # Initial step: Train with no data from the unseen device
    model_energy = XGBRegressor()
    model_energy.fit(X_train_base, y_train_energy_base)
    y_pred_energy = model_energy.predict(X_test)
    mape_energy = mean_absolute_percentage_error(y_test_energy, y_pred_energy) * 100
    mape_results_energy.append(mape_energy)

    model_latency = XGBRegressor()
    model_latency.fit(X_train_base, y_train_latency_base)
    y_pred_latency = model_latency.predict(X_test)
    mape_latency = mean_absolute_percentage_error(y_test_latency, y_pred_latency) * 100
    mape_results_latency.append(mape_latency)

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
        X_train = pd.concat([X_train_base, X_train_additional])
        y_train_energy = pd.concat([y_train_energy_base, y_train_energy_additional])
        y_train_latency = pd.concat([y_train_latency_base, y_train_latency_additional])

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
    axes[i, 0].plot(range(0, num_samples_to_introduce * (num_steps + 1), num_samples_to_introduce),
                    mape_results_energy, marker='o', color='#0165a0', linestyle='-')
    axes[i, 0].set_title(f'Energy MAPE for {device_to_test}')
    axes[i, 0].set_xlabel('Number of Device Data Points Introduced')
    axes[i, 0].set_ylabel('MAPE (Energy) %')

    axes[i, 1].plot(range(0, num_samples_to_introduce * (num_steps + 1), num_samples_to_introduce),
                    mape_results_latency, marker='o', color='#f4d792', linestyle='-')
    axes[i, 1].set_title(f'Latency MAPE for {device_to_test}')
    axes[i, 1].set_xlabel('Number of Device Data Points Introduced')
    axes[i, 1].set_ylabel('MAPE (Latency) %')

plt.tight_layout(rect=[0, 0.03, 1, 0.95])  # Adjust layout to make space for the main title
plt.show()
