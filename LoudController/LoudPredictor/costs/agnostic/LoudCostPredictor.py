import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt
import numpy as np

class LoudCostPredictor:
    def __init__(self, data_path):
        self.data = pd.read_csv(data_path)
        self.features = self.data[['Batch Size', 'Frequency', 'Throughput', 'GPU Max Frequency (MHz)',
                                   'GPU Min Frequency (MHz)', 'GPU Number of Cores', 'Memory Speed (GB/s)',
                                   'Memory Size (GB)', 'Tensor Cores']]
        self.target_energy = self.data['Energy']
        self.target_latency = self.data['Latency']
        self.model_energy = None
        self.model_latency = None

    def split_data(self, test_size=0.2, random_state=42):
        X_train, X_test, y_train_energy, y_test_energy = train_test_split(
            self.features, self.target_energy, test_size=test_size, random_state=random_state)
        _, _, y_train_latency, y_test_latency = train_test_split(
            self.features, self.target_latency, test_size=test_size, random_state=random_state)
        return X_train, X_test, y_train_energy, y_test_energy, y_train_latency, y_test_latency

    def train_models(self):
        X_train, _, y_train_energy, _, y_train_latency, _ = self.split_data()
        
        self.model_energy = XGBRegressor()
        self.model_energy.fit(X_train, y_train_energy)

        self.model_latency = XGBRegressor()
        self.model_latency.fit(X_train, y_train_latency)

    def evaluate_models(self):
        _, X_test, _, y_test_energy, _, y_test_latency = self.split_data()

        y_pred_energy = self.model_energy.predict(X_test)
        y_pred_latency = self.model_latency.predict(X_test)

        mae_energy = mean_absolute_error(y_test_energy, y_pred_energy)
        rmse_energy = np.sqrt(mean_squared_error(y_test_energy, y_pred_energy))
        mape_energy = self.mean_absolute_percentage_error(y_test_energy, y_pred_energy)

        mae_latency = mean_absolute_error(y_test_latency, y_pred_latency)
        rmse_latency = np.sqrt(mean_squared_error(y_test_latency, y_pred_latency))
        mape_latency = self.mean_absolute_percentage_error(y_test_latency, y_pred_latency)

        print(f"Energy Prediction - MAE: {mae_energy}, RMSE: {rmse_energy}, MAPE: {mape_energy:.2f}%")
        print(f"Latency Prediction - MAE: {mae_latency}, RMSE: {rmse_latency}, MAPE: {mape_latency:.2f}%")

    @staticmethod
    def mean_absolute_percentage_error(y_true, y_pred):
        return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

    def plot_results(self):
        _, X_test, _, y_test_energy, _, y_test_latency = self.split_data()

        y_pred_energy = self.model_energy.predict(X_test)
        y_pred_latency = self.model_latency.predict(X_test)

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

    def predict(self, input_features):
        """
        Predict energy and latency for given input features.

        :param input_features: A DataFrame or a single row with the same structure as the training features
        :return: Tuple of (predicted_energy, predicted_latency)
        """
        if not isinstance(input_features, pd.DataFrame):
            input_features = pd.DataFrame([input_features], columns=self.features.columns)

        predicted_energy = self.model_energy.predict(input_features)
        predicted_latency = self.model_latency.predict(input_features)

        return predicted_energy[0], predicted_latency[0]


if __name__ == '__main__':
    data_path = 'data.csv'  # Path to your CSV file
    model = LoudCostPredictor(data_path)
    
    model.train_models()
    model.evaluate_models()

    # Example input for prediction
    input_features = {
        'Batch Size': 32,
        'Frequency': 1000000000,
        'Throughput': 50,
        'GPU Max Frequency (MHz)': 1377000000,
        'GPU Min Frequency (MHz)': 76800000,
        'GPU Number of Cores': 64,
        'Memory Speed (GB/s)': 25.6,
        'Memory Size (GB)': 8,
        'Tensor Cores': 512
    }
    
    predicted_energy, predicted_latency = model.predict(input_features)
    print(f"Predicted Energy: {predicted_energy}, Predicted Latency: {predicted_latency}")

    model.plot_results()


