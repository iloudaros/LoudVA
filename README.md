# LoudVA

This repository contains the source code for the LoudVA thesis project, a system for orchestrating distributed inference workloads across a heterogeneous cluster of NVIDIA Jetson devices. The system is designed to intelligently schedule tasks to optimize for performance, energy consumption, and latency constraints.

## Key Contributions

This project makes the following key contributions:

1.  **Distributed Heterogeneous Inference System**: A complete, end-to-end system for managing inference tasks across a cluster of mixed NVIDIA Jetson devices (Nano, Xavier NX, AGX Xavier) using the Triton Inference Server.

2.  **Intelligent Energy-Aware Scheduling**: The core of the project is the `LoudScheduler`, a custom scheduler that dynamically assigns inference requests to the most suitable device. It optimizes for both **energy efficiency** and **latency constraints**, making real-time decisions based on device profiles and incoming workload.

3.  **Performance and Energy Prediction**: A machine learning model (`LoudCostPredictor`) that predicts the latency and energy consumption of different device configurations (GPU frequency, batch size). This allows the system to make informed scheduling decisions even for configurations that have not been profiled, enabling generalization to new devices and workloads.

4.  **Comprehensive Automation**: The entire system is managed through a powerful combination of a `Makefile` and `Ansible` playbooks. This allows for one-command setup, deployment, configuration, and operational control of the entire cluster, significantly simplifying management.

5.  **Extensive Experimentation & Profiling Framework**: The repository includes a full suite of scripts for:
    -   **Performance Profiling**: Systematically measuring performance, power, and energy across different hardware settings.
    -   **Experimentation**: Running automated, repeatable experiments to compare the custom scheduler against other common strategies (e.g., Round Robin, Fixed Batch Size) under various simulated workloads.

## System Architecture

LoudVA uses a controller-worker architecture:
-   **LoudController**: A central control node that receives inference requests via a Flask API (`LoudServer`) and uses an intelligent scheduler (`LoudScheduler`) to dispatch tasks.
-   **Worker Nodes (Jetsons)**: Edge devices running NVIDIA's Triton Inference Server and a lightweight `WorkerController` to allow for dynamic control of hardware settings like GPU frequency.

## Directory Structure

| Path                      | Description                                                                                                      |
| :------------------------ | :--------------------------------------------------------------------------------------------------------------- |
| **`LoudController/`**     | The core application with the API server, scheduler, device models, and predictors.                              |
| ├─ `altSchedulers/`       | Alternative scheduling algorithms for comparison.                                                                |
| ├─ `Experiments/`         | Scripts for running various performance and scheduling experiments.                                              |
| **`WorkerController/`**   | Lightweight Flask app deployed on each worker to manage device settings.                                         |
| **`ansible/`**            | Ansible playbooks for automating the setup and management of worker nodes.                                       |
| **`scripts/`**            | Helper scripts for setup, data processing, and system management.                                                |
| **`measurements/`**       | Raw and processed data from performance, power, and energy profiling.                                            |
| **`results/`**            | Output directory for experiment logs and reports.                                                                |
| **`model_repository/`**   | Machine learning models configured for the Triton Inference Server.                                              |
| **`makefile`**            | The main entry point for installing, running, and managing the entire system.                                    |


## Publications
This project appears in the following publications:

### [Leveraging DVFS for Energy-Efficient and QoS-aware Edge Video Analytics](https://dl.acm.org/doi/abs/10.1145/3721889.3721925)
We present a novel scheduling framework for energy-efficient video analytics at the edge. The proposed approach dynamically adjusts GPU frequency and batch size to optimize inference execution while ensuring QoS compliance. It integrates a priority queue for QoS-aware scheduling and leverages offline profiling and ML-based estimation to select energy-optimal configurations. Based on these configurations, it employs a priority-based scheduler with greedy batching and adaptive waiting strategies to efficiently dispatch inference requests. Experimental evaluation conducted on an NVIDIA Jetson Xavier AGX device demonstrates a ~ 28% improvement in frames served per joule compared to a baseline with no scheduler. This outperforms a static batch scheduler (32 frames per batch) by ~ 15% and a time-triggered scheduler (batch formation every 200 ms) by ~ 29%, while introducing minimal increase in QoS violations (5%) relative to the best-performing policy.


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

