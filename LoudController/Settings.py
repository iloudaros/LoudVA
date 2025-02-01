# LoudController settings
max_latency = 5.0
safety_margin = 0.5
default_latency = 1.0

# Triton server settings
model_name = 'inception_graphdef'
number_of_classes = 1
model_version = '1'
scaling = 'INCEPTION'

# Profiling or Predicting
use_prediction = False
fill_missing_profile_data = True

# Health check settings
health_check_interval = 15
health_checks_enabled = False

# Batching 
max_batch_size = 200
min_batch_size = 1
batching_wait_looseness = 2 
batching_max_wait_time = 5
fixed_batch_size = 4

# Debugging
debug = False

# Scheduler settings
scheduler_wait_time = 0.01
scheduler = 'stress' # Options: 'loud', 'random', 'round_robin', 'stress'
