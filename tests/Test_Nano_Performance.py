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
i.return_to_defaults("nano")

# Test parameters
minimum_concurrency = 1
maximum_concurrency = 13
check_modes = 1
check_freqs = 1
timeout_enabled = 1
retries_allowed = 100

# The supported power modes for the Jetson Nano
power_modes = [0,1] 

# These are the supported frequencies for the GPU on the Jetson Nano
#[76800000, 153600000, 230400000, 307200000, 384000000, 460800000, 537600000, 614400000, 691200000, 768000000, 844800000, 921600000] 
gpu_freqs = [ 153600000, 230400000, 307200000, 384000000, 460800000, 537600000, 614400000, 691200000, 768000000, 844800000, 921600000] 

# Create the system profile
i.profiling(check_modes = check_modes,
            check_freqs = check_freqs,
            power_modes = [0,1],
            gpu_freqs = [153600000, 921600000],
            minimum_concurrency = minimum_concurrency,
            maximum_concurrency = maximum_concurrency,
            timeout_enabled = timeout_enabled,
            retries_allowed = retries_allowed,
            board = "nano")