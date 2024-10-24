include .environment #for our credentials, making it easy to reuse and add to .gitignore
ANSIBLE_DIRECTORY = ./ansible
ANSIBLE_OPTS = -f 6 -i ${ANSIBLE_DIRECTORY}/inventory.ini -e "ansible_become_pass=${PASS}"
model=$(shell tr -d '\0' < /proc/device-tree/model)


.PHONY: sync_time download_triton initialise_Jetsons system_setup start_triton


playground:
	mkdir -p ~/LoudVA/measurements/performance/$(shell date +'%Y-%m-%d_%H-%M-%S')






###### System Initialization and Setup #######
### To be run on LoudGateway ###

sync_time: 
	@echo "____Setting Correct Time and Date on Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/sync_time.yaml

print_time:
	@echo "____What time is it?____"
	@ansible ${ANSIBLE_OPTS} Workers -a "date" -u iloudaros

download_triton:
	@echo "____Downloading and Sending triton to the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/download_triton.yaml -u iloudaros

install_dependecies:
	@echo "____Installing Dependencies on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/install_dependencies.yaml

create_model_repository:
	@echo "____Creating Model Directory on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/create_model_repository.yaml

clone_LoudVA:
	@echo "____Cloning LoudVA to the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/clone_LoudVA.yaml

initialise_Jetsons: sync_time install_dependecies download_triton clone_LoudVA create_model_repository

client_setup: 
	@echo "____Setting up Triton Client on LoudGateway____"
	#### Install Triton Client Dependencies ####
	sudo apt-get install -y --no-install-recommends \
        curl \
        pkg-config \
        python3 \
        python3-pip \
        python3-dev
	pip3 install --upgrade wheel setuptools cython testresources
	pip3 install --upgrade grpcio-tools numpy future attrdict pillow 
	pip3 install --upgrade image six requests flake8
	pip install protobuf==3.20
	pip3 install flask


	#### Create directories for for each version of Triton client ####
	mkdir -p ~/tritonserver2_19
	tar zxvf ~/tritonserver2_19.tgz -C ~/tritonserver2_19
	mkdir -p ~/tritonserver2_34
	tar zxvf ~/tritonserver2_34.tgz -C ~/tritonserver2_34
	
	#### Run python wheels for each version of Triton client ####
	
	python3 -m pip install --upgrade ~/tritonserver2_19/clients/python/tritonclient-2.19.0-py3-none-any.whl[all]
	python3 -m pip install --upgrade ~/tritonserver2_34/clients/python/tritonclient-2.34.0-py3-none-any.whl[all]

client_download_triton:
	wget https://github.com/triton-inference-server/server/releases/download/v2.19.0/tritonserver2.19.0-jetpack4.6.1.tgz
	mv tritonserver2.19.0-jetpack4.6.1.tgz ~/tritonserver2_19.tgz	
	wget https://github.com/triton-inference-server/server/releases/download/v2.34.0/tritonserver2.34.0-jetpack5.1.tgz
	mv tritonserver2.34.0-jetpack5.1.tgz ~/tritonserver2_34.tgz

install_tao:
	@echo "____Installing TAO on The Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/install_tao.yaml

set_environment:
	@echo "____Setting Environment Variables on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/set_environment.yaml

configure_triton:
	@echo "____Enabling Dynamic Batching on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/configure_triton.yaml

system_setup: initialise_Jetsons set_environment client_setup

	@echo "✅ : System Setup Complete"

update_workers:
	@echo "____Updating the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/update_workers.yaml

print_flags:
	@echo "____Printing Flags from the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/print_flags.yaml

################################################














################ Quick Access ##################
### To be run on LoudGateway ###
start_triton: configure_triton
	@echo "____Starting Triton on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/start_triton.yaml 

start_triton_gpumetrics:
	@echo "____Starting Triton on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/start_triton_gpumetrics.yaml

stop_triton:
	@echo "____Stopping Triton on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/stop_triton.yaml

start_LoudVA_server:
	@echo "____Starting LoudVA server____"
	@cd ~/LoudVA/LoudVA && gunicorn -w 4 'LoudVA:app'

start_LoudVA: start_triton start_LoudVA_server
	@echo "LoudVA Started"

reboot_workers: stop_triton
	@echo "____Rebooting the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/reboot.yaml
	@echo "Jetsons Rebooted"
	@make sync_time

default_power_mode:
	@echo "____Setting the Jetsons to Default Power Mode____"
	@ansible ${ANSIBLE_OPTS} LoudJetsons -a "nvpmodel -m 0" -u iloudaros --become

send_makefile:
	@echo "____Sending Makefile to the Jetsons____"
	@ansible ${ANSIBLE_OPTS} Workers -m copy -a "src=~/LoudVA/makefile dest=/home/iloudaros/LoudVA/makefile" -u iloudaros --become


add_specs_to_profiling:
	python3 scripts/python/add_specs.py measurements/archive/Representative/profiling.csv devices/gpu_specs.csv LoudPredictor/costs/agnostic/data.csv

### To be run on the Jetsons ###

model:
	@echo ${model}

GPU_MIN_FREQ = 76800000 
GPU_MAX_FREQ = 921600000
change_gpu_freq:
	@if [ "${model}" = "NVIDIA Jetson Nano Developer Kit" ]; then \
		sudo sh -c 'echo '${GPU_MIN_FREQ}' > /sys/devices/57000000.gpu/devfreq/57000000.gpu/min_freq'; \
		sudo sh -c 'echo '${GPU_MAX_FREQ}' > /sys/devices/57000000.gpu/devfreq/57000000.gpu/max_freq'; \
	elif [ "${model}" = "NVIDIA Jetson Xavier NX Developer Kit" ]; then \
		sudo sh -c 'echo '${GPU_MIN_FREQ}' > /sys/devices/17000000.gv11b/devfreq/17000000.gv11b/min_freq'; \
		sudo sh -c 'echo '${GPU_MAX_FREQ}' > /sys/devices/17000000.gv11b/devfreq/17000000.gv11b/max_freq'; \
	elif [ "${model}" = "Jetson-AGX" ]; then \
		sudo sh -c 'echo '${GPU_MIN_FREQ}' > /sys/devices/17000000.gv11b/devfreq/17000000.gv11b/min_freq'; \
		sudo sh -c 'echo '${GPU_MAX_FREQ}' > /sys/devices/17000000.gv11b/devfreq/17000000.gv11b/max_freq'; \
	else \
		echo "This is not a Jetson"; \
	fi

current_gpu_freq:
	@echo "Model: ${model}"
	@echo "Current GPU Frequency"
	@if [ "${model}" = "NVIDIA Jetson Nano Developer Kit" ]; then \
		cat /sys/devices/57000000.gpu/devfreq/57000000.gpu/cur_freq; \
	elif [ "${model}" = "NVIDIA Jetson Xavier NX Developer Kit" ]; then \
		cat /sys/devices/17000000.gv11b/devfreq/17000000.gv11b/cur_freq; \
	elif [ "${model}" = "Jetson-AGX" ]; then \
		cat /sys/devices/17000000.gv11b/devfreq/17000000.gv11b/cur_freq; \
	else \
		echo "This is not a Jetson"; \
	fi

	
	@echo "Upper Boundary"
	@if [ "${model}" = "NVIDIA Jetson Nano Developer Kit" ]; then \
		cat /sys/devices/57000000.gpu/devfreq/57000000.gpu/max_freq; \
	elif [ "${model}" = "NVIDIA Jetson Xavier NX Developer Kit" ]; then \
		cat /sys/devices/17000000.gv11b/devfreq/17000000.gv11b/max_freq; \
	elif [ "${model}" = "Jetson-AGX" ]; then \
		cat /sys/devices/17000000.gv11b/devfreq/17000000.gv11b/max_freq; \
	else \
		echo "This is not a Jetson"; \
	fi
	
	@echo "Lower Boundary"
	@if [ "${model}" = "NVIDIA Jetson Nano Developer Kit" ]; then \
		cat /sys/devices/57000000.gpu/devfreq/57000000.gpu/min_freq; \
	elif [ "${model}" = "NVIDIA Jetson Xavier NX Developer Kit" ]; then \
		cat /sys/devices/17000000.gv11b/devfreq/17000000.gv11b/min_freq; \
	elif [ "${model}" = "Jetson-AGX" ]; then \
		cat /sys/devices/17000000.gv11b/devfreq/17000000.gv11b/min_freq; \
	else \
		echo "This is not a Jetson"; \
	fi

3D_scaling:
	sudo sh -c 'echo 1 > /sys/devices/57000000.gpu/enable_3d_scaling'

available_frequencies:
	@echo "Model: ${model}"
	@if [ "${model}" = "NVIDIA Jetson Nano Developer Kit" ]; then \
		cat /sys/devices/57000000.gpu/devfreq/57000000.gpu/available_frequencies; \
	elif [ "${model}" = "NVIDIA Jetson Xavier NX Developer Kit" ]; then \
		cat /sys/devices/17000000.gv11b/devfreq/17000000.gv11b/available_frequencies; \
	elif [ "${model}" = "Jetson-AGX" ]; then \
		cat /sys/devices/17000000.gv11b/devfreq/17000000.gv11b/available_frequencies; \
	else \
		echo "This is not a Jetson"; \
	fi

edit_nvpmodel:
	sudo code /etc/nvpmodel/nvpmodel_t210_jetson-nano.conf

cat_nvpmodel:
	cat /etc/nvpmodel/nvpmodel_t210_jetson-nano.conf

watch_log:
	watch -n 1 cat ~/LoudVA/measurements/log

jetpack_version:
	sudo apt-cache show nvidia-jetpack
	echo "Remember to check the linux version from https://docs.nvidia.com/jetson/archives/index.html"


### To be run on the client ###
check_api:
	@curl 127.0.0.1:5000
################################################










############### Tests and Checks ###############
### To be run on LoudGateway ###

# ping the Jetsons
ping_workers:
	@echo "____Pinging the Jetsons____"
	@ansible ${ANSIBLE_OPTS} all -m ping


check_triton: is_triton_running
	@(python3 ~/tritonserver2_19/clients/python/image_client.py -m inception_graphdef -c 3 -s INCEPTION data/images/brown_bear.jpg --url 192.168.0.120:8000 --protocol HTTP && echo "LoudJetson0:✅") &
	@(python3 ~/tritonserver2_19/clients/python/image_client.py -m inception_graphdef -c 3 -s INCEPTION data/images/brown_bear.jpg --url 192.168.0.121:8000 --protocol HTTP && echo "LoudJetson1:✅") &
	@(python3 ~/tritonserver2_19/clients/python/image_client.py -m inception_graphdef -c 3 -s INCEPTION data/images/brown_bear.jpg --url 192.168.0.122:8000 --protocol HTTP && echo "LoudJetson2:✅") &
	@(python3 ~/tritonserver2_34/clients/python/image_client.py -m inception_graphdef -c 3 -s INCEPTION data/images/brown_bear.jpg --url 192.168.0.112:8000 --protocol HTTP && echo "agx-xavier-00:✅") &
	@(python3 ~/tritonserver2_34/clients/python/image_client.py -m inception_graphdef -c 3 -s INCEPTION data/images/brown_bear.jpg --url 192.168.0.110:8000 --protocol HTTP && echo "xavier-nx-00:✅") &
	@(python3 ~/tritonserver2_34/clients/python/image_client.py -m inception_graphdef -c 3 -s INCEPTION data/images/brown_bear.jpg --url 192.168.0.111:8000 --protocol HTTP && echo "xavier-nx-01:✅")

is_triton_running:
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/is_triton_running.yaml

performance_profiling: update_workers is_triton_running
	@echo "____Beginning The performance profiling____"
	@echo "(This will take a while)"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/performance_profiling.yaml -u iloudaros
	@echo "✅ : Performance Profiling Complete"
	@curl \
		-d "Performance Profiling complete" \
		-H "Title: LoudVA" \
		-H "Tags: white_check_mark" \
		${NOTIFICATION_URL}

eval_LoudIntervalPredictor:
	@echo "____Evaluating the Predictor____"
	python3 LoudPredictor/input/LoudIntervalPredictor.py --plot
	python3 LoudPredictor/input/eval/IntervalPredictionEvaluator.py --generator_log LoudGenerator/event_log.csv --predictor_log LoudPredictor/input/interval_prediction_log.csv

eval_LoudFramePredictor:
	@echo "____Evaluating the Predictor____"
	python3 LoudPredictor/input/LoudFramePredictor.py --log_filename LoudMonitor/frame_monitor_log.csv --plot
	python3 LoudPredictor/input/eval/FramePredictionEvaluator.py --actual_log_filename LoudMonitor/frame_monitor_log.csv --prediction_log_filename LoudPredictor/input/frame_prediction_log.csv

eval_specific_LoudCostPredictors:
	@echo "____Evaluating the Predictors____"
	@cd LoudPredictor/costs/specific && python3 LCP-agx.py &
	@cd LoudPredictor/costs/specific && python3 LCP-nano.py &
	@cd LoudPredictor/costs/specific && python3 LCP-nx.py 

eval_agnostic_LoudCostPredictor: add_specs_to_profiling
	@echo "____Evaluating the Predictor____"
	@cd LoudPredictor/costs/agnostic && python3 LoudCostPredictor.py

### To be run on the Jetsons ###
CONCURRENCY_FLOOR = 1
CONCURRENCY_LIMIT = 20

MEASUREMENT_MODE = count_windows #time_windows or count_windows

## used with time_windows with option --measurement-interval
MEASUREMENT_INTERVAL = 5000

## used with count_windows with option --measurement-request-count
MEASUREMENT_COUNT = 10000

## determine when a measurement is considered successful
STABILITY_THRESHOLD = 10

measure_performance:
	~/tritonserver/clients/bin/perf_analyzer -s ${STABILITY_THRESHOLD} -m inception_graphdef --concurrency-range ${CONCURRENCY_FLOOR}:${CONCURRENCY_LIMIT} --measurement-mode ${MEASUREMENT_MODE} --measurement-request-count${MEASUREMENT_COUNT}

measure_performance_csv:
	~/tritonserver/clients/bin/perf_analyzer -s ${STABILITY_THRESHOLD} -m inception_graphdef --concurrency-range ${CONCURRENCY_FLOOR}:${CONCURRENCY_LIMIT} --measurement-mode ${MEASUREMENT_MODE} -f measurements/performance/performance_measurements.csv


MEASUREMENT_INTERVAL2 = 500 #in ms
measure_idle_power:
	@sudo tegrastats --interval ${MEASUREMENT_INTERVAL2} --start --logfile measurements/power/idle_tegra_log_${MEASUREMENT_INTERVAL2} && sleep 10 && sudo tegrastats --stop
	@sudo bash scripts/shell/clean_measurements.sh measurements/power/idle_tegra_log_${MEASUREMENT_INTERVAL2} measurements/power/idle_power_measurement_${MEASUREMENT_INTERVAL2}
	@bash scripts/shell/mean_median.sh measurements/power/idle_power_measurement_${MEASUREMENT_INTERVAL2}
	@echo "Check measurements/power/idle_power_measurement_${MEASUREMENT_INTERVAL2} for the power measurements"

measure_performance_and_power:
	@sudo tegrastats --interval ${MEASUREMENT_INTERVAL2} --start --logfile measurements/power/tegra_log && /home/iloudaros/tritonserver/clients/bin/perf_analyzer -s ${STABILITY_THRESHOLD} -m inception_graphdef --concurrency-range ${CONCURRENCY_FLOOR}:${CONCURRENCY_LIMIT} --measurement-mode ${MEASUREMENT_MODE} -f measurements/performance/performance_measurements.csv && sudo tegrastats --stop
	@sudo bash scripts/shell/clean_measurements.sh measurements/power/tegra_log measurements/power/power_measurement
	@bash scripts/shell/mean_median.sh measurements/power/power_measurement
	@echo "Check measurements/power/power_measurement_stats for the power measurements"
################################################










################## Clean Up ####################
delete_LoudVA:
	@echo "____Deleting LoudVA from the Jetsons____"
	@ansible ${ANSIBLE_OPTS} Workers -a "rm -r /home/iloudaros/LoudVA" -u iloudaros --become

delete_triton:
	@echo "____Removing Triton from the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/delete_triton.yaml

delete_flags:
	@echo "____Deleting Flags from the Jetsons____"
	@ansible ${ANSIBLE_OPTS} Workers -a "rm /tmp/ansible/flags/triton_running.flag" -u iloudaros --become

clean: delete_LoudVA delete_triton 
	@echo "✅ : Clean Up Complete"

	
delete_measurements:
	@echo "Deleting..."
	@rm -r ~/LoudVA/measurements/*
	@touch ~/LoudVA/measurements/.gitkeep