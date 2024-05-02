#!/usr/bin/python3 -u
### Performance Test ###
# 
# We use this script to test the effect of the power mode (or GPU clk speed) of the Jetson on the performance of the triton server, with the dynamic batching feature enabled.
# - We will use the `perf_analyzer` tool to measure the throughput of the server with different power modes.
# - We will use the `nvpmodel` tool to change the power mode of the Jetson.
# 
# (To be run on the Jetsons via the performance_profiling ansible playbook.)

import os
import ihelper as i
i.return_to_defaults("agx")

# This is a dictionary where we will store frequencies and modes and the concurrency that needed retries and the number of retries
retried_modes = {}
retried_freqs = {}

# Test parameters
minimum_concurrency = 1
maximum_concurrency = 128
check_modes = 1
check_freqs = 1
timeout_enabled = 1
retries_allowed = 100

# The supported power modes for the Jetson AGX Xavier
power_modes = [0, 1, 2, 3, 4, 5, 6, 7] 

# These are the supported frequencies for the GPU on the Jetson AGX Xavier
#[114750000, 216750000, 318750000, 420750000, 522750000, 624750000, 675750000, 828750000, 905250000, 1032750000, 1198500000, 1236750000, 1338750000, 1377000000]
gpu_freqs = [ 114750000, 216750000, 318750000, 420750000, 522750000, 624750000, 675750000, 828750000, 905250000, 1032750000, 1198500000, 1236750000, 1338750000, 1377000000]

# Create the system profile
i.profiling(check_modes = check_modes,
            check_freqs = check_freqs,
            power_modes = power_modes,
            gpu_freqs = gpu_freqs,
            minimum_concurrency = minimum_concurrency,
            maximum_concurrency = maximum_concurrency,
            timeout_enabled = timeout_enabled,
            retries_allowed = retries_allowed,
            board = "agx")