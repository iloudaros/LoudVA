# LoudController settings
max_latency = 5.0
safety_margin = 0.5
default_latency = 1.0

# Frequency scaling settings
scaling_logic_period = 2
frequency_scaling_idle_limit = 4

# Triton server settings
model_name = 'inception_graphdef'
number_of_classes = 1
model_version = '1'
scaling = 'INCEPTION'

# Profiling or Predicting
use_prediction = True
fill_missing_profile_data = True

# Health check settings
health_check_interval = 15
health_checks_enabled = False

# Batching 
max_batch_size = 200
min_batch_size = 1
batching_wait_looseness = 2 
batching_max_wait_time = 5
fixed_batch_size = 4 # Used for the fixed batch size scheduler
batching_interval = 1 # Used for the fixed interval scheduler

# Debugging
debug = False

# Scheduler settings
scheduler_wait_time = 0.01
scheduler = 'loud' # Options: ['loud', 'random', 'round_robin', 'stress', 'transparent', 'interval', 'fixed_batch']
