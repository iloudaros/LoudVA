#!/usr/bin/python3 -u
### Performance Test ###
# 
# We use this script to test the effect of the power mode (or GPU clk speed) of the Jetson on the performance of the triton server, with the dynamic batching feature enabled.
# - We will use the `perf_analyzer` tool to measure the throughput of the server with different power modes.
# - We will use the `nvpmodel` tool to change the power mode of the Jetson.
# 
# (To be run on the Jetsons via the performance_profiling ansible playbook.)

import ihelper as i
i.return_to_defaults("nx")

# Test parameters
minimum_concurrency = 1
maximum_concurrency = 18
check_modes = 1
check_freqs = 0
timeout_enabled = 1
retries_allowed = 100

# The supported power modes for the Jetson Xavier NX
power_modes = [0, 1, 2, 3, 4, 5, 6, 7, 8]

# These are the supported frequencies for the GPU on the Jetson Xavier NX
#[114750000, 204000000, 306000000, 408000000, 510000000, 599250000, 701250000, 752250000, 803250000, 854250000, 905250000, 956250000, 1007250000, 1058250000, 1109250000] 
gpu_freqs = [ 114750000, 204000000, 306000000, 408000000, 510000000, 599250000, 701250000, 752250000, 803250000, 854250000, 905250000, 956250000, 1007250000, 1058250000, 1109250000] 

# Create the system profile
i.profiling(check_modes = check_modes,
            check_freqs = check_freqs,
            power_modes = power_modes,
            gpu_freqs = gpu_freqs,
            minimum_concurrency = minimum_concurrency,
            maximum_concurrency = maximum_concurrency,
            timeout_enabled = timeout_enabled,
            retries_allowed = retries_allowed,
            board = "nx")