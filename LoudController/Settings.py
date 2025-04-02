# LoudController settings
default_latency = 20.0 

# Frequency scaling settings
scaling_logic_period = 2
frequency_scaling_idle_limit = 4

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
batching_wait_strictness = 4 
batching_max_wait_time = 5
fixed_batch_size = 8 # Used for the fixed batch size scheduler
batching_interval = 1 # Used for the fixed interval scheduler

# Debugging
debug = False

# Scheduler settings
scheduler_wait_time = 0.01
scheduler = 'round_robin' # Options: ['loud', 'random', 'round_robin', 'kind_round_robin', 'stress', 'transparent', 'interval', 'fixed_batch']
safety_margin = 0.2 # The manual decrease in every latency constraint to account for unpredictable delays.
calculate_network_cost = True
single_device = False