import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
import matplotlib.pyplot as plt
import numpy as np

# Load the data
data = pd.read_csv('../../../measurements/archive/Representative/profiling.csv')

# Filter the data to keep only rows where 'Directory' is 'Nano'
data = data[data['Directory'] == 'Nano']

print(data.head())

# Features and target variables
features = data[['Batch Size', 'Frequency', 'Throughput']]
target_energy = data['Energy']
target_latency = data['Latency']

# Split the data
X_train, X_test, y_train_energy, y_test_energy = train_test_split(features, target_energy, test_size=0.2, random_state=42)
_, _, y_train_latency, y_test_latency = train_test_split(features, target_latency, test_size=0.2, random_state=42)

# Train the model for energy prediction
model_energy = XGBRegressor()
model_energy.fit(X_train, y_train_energy)

# Train the model for latency prediction
model_latency = XGBRegressor()
model_latency.fit(X_train, y_train_latency)

# Predict and evaluate
y_pred_energy = model_energy.predict(X_test)
y_pred_latency = model_latency.predict(X_test)

# Define MAPE function
def mean_absolute_percentage_error(y_true, y_pred):
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

# Calculate metrics
mae_energy = mean_absolute_error(y_test_energy, y_pred_energy)
rmse_energy = root_mean_squared_error(y_test_energy, y_pred_energy)
mape_energy = mean_absolute_percentage_error(y_test_energy, y_pred_energy)

mae_latency = mean_absolute_error(y_test_latency, y_pred_latency)
rmse_latency = root_mean_squared_error(y_test_latency, y_pred_latency)
mape_latency = mean_absolute_percentage_error(y_test_latency, y_pred_latency)

print(f"Energy Prediction - MAE: {mae_energy}, RMSE: {rmse_energy}, MAPE: {mape_energy:.2f}%")
print(f"Latency Prediction - MAE: {mae_latency}, RMSE: {rmse_latency}, MAPE: {mape_latency:.2f}%")

# Plot results
plt.figure(figsize=(12, 6))

plt.subplot(1, 2, 1)
plt.scatter(y_test_energy, y_pred_energy, alpha=0.5)
plt.plot([y_test_energy.min(), y_test_energy.max()], [y_test_energy.min(), y_test_energy.max()], 'k--', lw=2)
plt.xlabel('Actual Energy Consumption')
plt.ylabel('Predicted Energy Consumption')
plt.title('Energy Prediction')

plt.subplot(1, 2, 2)
plt.scatter(y_test_latency, y_pred_latency, alpha=0.5)
plt.plot([y_test_latency.min(), y_test_latency.max()], [y_test_latency.min(), y_test_latency.max()], 'k--', lw=2)
plt.xlabel('Actual Latency')
plt.ylabel('Predicted Latency')
plt.title('Latency Prediction')

plt.tight_layout()
plt.show()
