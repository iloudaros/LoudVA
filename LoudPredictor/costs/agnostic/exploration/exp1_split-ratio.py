import pandas as pd
from sklearn.model_selection import train_test_split
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

# Define split ratios
split_ratios = np.arange(0.1, 1.0, 0.1)
mape_results_energy = []
mape_results_latency = []

for split_ratio in split_ratios:
    # Split the data
    X_train, X_test, y_train_energy, y_test_energy = train_test_split(features, target_energy, test_size=split_ratio, random_state=42)
    _, _, y_train_latency, y_test_latency = train_test_split(features, target_latency, test_size=split_ratio, random_state=42)

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

# Plot results
plt.figure(figsize=(12, 6))

plt.subplot(1, 2, 1)
plt.bar(split_ratios * 100, mape_results_energy, width=5, color='#0165a0', edgecolor='black')
plt.xlabel('Test Set Percentage (%)')
plt.ylabel('MAPE (Energy) %')
plt.title('Energy Prediction Error vs. Test Set Size')

plt.subplot(1, 2, 2)
plt.bar(split_ratios * 100, mape_results_latency, width=5, color='#f4d792', edgecolor='black')
plt.xlabel('Test Set Percentage (%)')
plt.ylabel('MAPE (Latency) %')
plt.title('Latency Prediction Error vs. Test Set Size')

plt.tight_layout()
plt.show()
