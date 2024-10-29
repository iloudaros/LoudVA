import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
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
mape_results_energy_default = []
mape_results_latency_default = []
mape_results_energy_tuned = []
mape_results_latency_tuned = []

# Hyperparameter grid for tuning
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [3, 6, 9],
    'learning_rate': [0.01, 0.1, 0.2],
    'subsample': [0.7, 0.8, 1.0]
}

for split_ratio in split_ratios:
    # Split the data
    X_train, X_test, y_train_energy, y_test_energy = train_test_split(features, target_energy, test_size=split_ratio, random_state=42)
    _, _, y_train_latency, y_test_latency = train_test_split(features, target_latency, test_size=split_ratio, random_state=42)

    # Default model for energy prediction
    model_energy_default = XGBRegressor()
    model_energy_default.fit(X_train, y_train_energy)
    y_pred_energy_default = model_energy_default.predict(X_test)
    mape_energy_default = mean_absolute_percentage_error(y_test_energy, y_pred_energy_default) * 100
    mape_results_energy_default.append(mape_energy_default)

    # Default model for latency prediction
    model_latency_default = XGBRegressor()
    model_latency_default.fit(X_train, y_train_latency)
    y_pred_latency_default = model_latency_default.predict(X_test)
    mape_latency_default = mean_absolute_percentage_error(y_test_latency, y_pred_latency_default) * 100
    mape_results_latency_default.append(mape_latency_default)

    # Grid search for energy prediction
    grid_search_energy = GridSearchCV(estimator=XGBRegressor(), param_grid=param_grid, scoring='neg_mean_absolute_percentage_error', cv=3, verbose=1)
    grid_search_energy.fit(X_train, y_train_energy)
    best_model_energy = grid_search_energy.best_estimator_
    y_pred_energy_tuned = best_model_energy.predict(X_test)
    mape_energy_tuned = mean_absolute_percentage_error(y_test_energy, y_pred_energy_tuned) * 100
    mape_results_energy_tuned.append(mape_energy_tuned)

    # Grid search for latency prediction
    grid_search_latency = GridSearchCV(estimator=XGBRegressor(), param_grid=param_grid, scoring='neg_mean_absolute_percentage_error', cv=3, verbose=1)
    grid_search_latency.fit(X_train, y_train_latency)
    best_model_latency = grid_search_latency.best_estimator_
    y_pred_latency_tuned = best_model_latency.predict(X_test)
    mape_latency_tuned = mean_absolute_percentage_error(y_test_latency, y_pred_latency_tuned) * 100
    mape_results_latency_tuned.append(mape_latency_tuned)

# Plot results
plt.figure(figsize=(14, 6))

plt.subplot(1, 2, 1)
plt.plot(split_ratios * 100, mape_results_energy_default, marker='o', color='#0165a0', linestyle='-', label='Default')
plt.plot(split_ratios * 100, mape_results_energy_tuned, marker='o', color='#f4d792', linestyle='-', label='Tuned')
plt.xlabel('Test Set Percentage (%)')
plt.ylabel('MAPE (Energy) %')
plt.title('Energy Prediction MAPE: Default vs. Tuned')
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(split_ratios * 100, mape_results_latency_default, marker='o', color='#0165a0', linestyle='-', label='Default')
plt.plot(split_ratios * 100, mape_results_latency_tuned, marker='o', color='#f4d792', linestyle='-', label='Tuned')
plt.xlabel('Test Set Percentage (%)')
plt.ylabel('MAPE (Latency) %')
plt.title('Latency Prediction MAPE: Default vs. Tuned')
plt.legend()

plt.tight_layout()
plt.show()
