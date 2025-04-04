include .environment #for our credentials, making it easy to reuse and add to .gitignore
ANSIBLE_DIRECTORY = ./ansible
ANSIBLE_PLAYBOOK_DIR = ${ANSIBLE_DIRECTORY}/playbooks
ANSIBLE_OPTS = -f 6 -i ${ANSIBLE_DIRECTORY}/inventory.ini -e "ansible_become_pass=${PASS}"
model=$(shell tr -d '\0' < /proc/device-tree/model)


.PHONY: sync_time download_triton initialise_Jetsons system_setup start_triton


playground:
	mkdir -p measurements/performance/$(shell date +'%Y-%m-%d_%H-%M-%S')






###### System Initialization and Setup #######
### To be run on the Controller ###

sync_time: 
	@echo "____Setting Correct Time and Date on Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_PLAYBOOK_DIR}/sync_time.yaml

print_time:
	@echo "____What time is it?____"
	@ansible ${ANSIBLE_OPTS} Workers -a "date" -u iloudaros

download_triton:
	@echo "____Downloading and Sending triton to the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_PLAYBOOK_DIR}/download_triton.yaml -u iloudaros

install_dependecies:
	@echo "____Installing Dependencies on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_PLAYBOOK_DIR}/install_dependencies.yaml

create_model_repository:
	@echo "____Creating Model Directory on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_PLAYBOOK_DIR}/create_model_repository.yaml

clone_LoudVA:
	@echo "____Cloning LoudVA to the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_PLAYBOOK_DIR}/clone_LoudVA.yaml

initialise_Jetsons: sync_time install_dependecies download_triton clone_LoudVA create_model_repository

triton_client_dependencies:
	@echo "Install Triton Client Dependencies..."
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

	@echo "Creating directories for each version of Triton client..."
	mkdir -p ~/tritonserver2_19
	tar zxvf ~/tritonserver2_19.tgz -C ~/tritonserver2_19 
	mkdir -p ~/tritonserver2_34
	tar zxvf ~/tritonserver2_34.tgz -C ~/tritonserver2_34

	@echo "Running python wheels for each version of Triton client..."
	python3 -m pip install --upgrade ~/tritonserver2_19/clients/python/tritonclient-2.19.0-py3-none-any.whl[all]
	python3 -m pip install --upgrade ~/tritonserver2_34/clients/python/tritonclient-2.34.0-py3-none-any.whl[all]

LoudController_dependencies:
	@echo "Installing Dependencies for LoudController..."
	pip3 install flask gunicorn pandas matplotlib scikit-learn scipy xgboost

controller_setup: triton_client_dependencies LoudController_dependencies

controller_download_triton:
	wget https://github.com/triton-inference-server/server/releases/download/v2.19.0/tritonserver2.19.0-jetpack4.6.1.tgz
	mv tritonserver2.19.0-jetpack4.6.1.tgz ~/tritonserver2_19.tgz	
	wget https://github.com/triton-inference-server/server/releases/download/v2.34.0/tritonserver2.34.0-jetpack5.1.tgz
	mv tritonserver2.34.0-jetpack5.1.tgz ~/tritonserver2_34.tgz

install_tao:
	@echo "____Installing TAO on The Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_PLAYBOOK_DIR}/install_tao.yaml

set_environment:
	@echo "____Setting Environment Variables on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_PLAYBOOK_DIR}/set_environment.yaml

configure_triton:
	@echo "____Enabling Dynamic Batching on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_PLAYBOOK_DIR}/configure_triton.yaml

system_setup: initialise_Jetsons set_environment controller_setup

	@echo "✅ : System Setup Complete"

update_workers:
	@echo "____Updating the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_PLAYBOOK_DIR}/update_workers.yaml

print_flags:
	@echo "____Printing Flags from the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_PLAYBOOK_DIR}/print_flags.yaml

################################################















################ Quick Access ##################
### To be run on the Controller ###
start_triton: #configure_triton
	@echo "____Starting Triton on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_PLAYBOOK_DIR}/start_triton.yaml 
	@echo "Triton Started"

start_triton_gpumetrics:
	@echo "____Starting Triton on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_PLAYBOOK_DIR}/start_triton_gpumetrics.yaml

stop_triton:
	@echo "____Stopping Triton on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_PLAYBOOK_DIR}/stop_triton.yaml

start_LoudController_gunicorn:
	@echo "____Starting Control Node____"
	@screen -dmS LoudController bash -c 'cd LoudController && gunicorn --worker-class gevent -w 4 "LoudController:app"'
	@echo "LoudController Started. Use 'screen -r LoudController' to view the logs"

start_LoudController:
	@if screen -list | grep -q "LoudController"; then \
		echo "LoudController is already running."; \
	else \
		echo "____Starting Control Node in debug mode____"; \
		screen -dmS LoudController bash -c 'python3 LoudController/LoudController.py > LoudController.log 2>&1'; \
		echo "LoudController Started. Use 'screen -r LoudController' to view the logs"; \
		curl \
			-d "LoudController started" \
			-H "Title: LoudVA" \
			-H "Tags: white_check_mark" \
			${NOTIFICATION_URL}; \
	fi


stop_LoudController:
	@echo "____Stopping Control Node____"
	-screen -S LoudController -X quit
	@echo "LoudController Stopped"

restart_LoudController: stop_LoudController start_LoudController

start_WorkerController:
	@echo "____Starting Worker Controller____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_PLAYBOOK_DIR}/start_WorkerController.yaml

stop_WorkerController:
	@echo "____Stopping Worker Controller____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_PLAYBOOK_DIR}/stop_WorkerController.yaml

start_workers: start_triton start_WorkerController
	@echo "Workers Started"
	@curl \
		-d "Workers Online. Triton and WorkerController started." \
		-H "Title: LoudVA" \
		-H "Tags: white_check_mark" \
		${NOTIFICATION_URL}

start: start_workers start_LoudController 
	@echo "LoudVA Started"
	

stop: stop_triton stop_WorkerController stop_LoudController 
	@echo "LoudVA Stopped"

reboot_workers: stop_triton
	@echo "____Rebooting the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_PLAYBOOK_DIR}/reboot.yaml
	@echo "Jetsons Rebooted"
	@make sync_time
	@curl \
		-d "Workers Rebooted" \
		-H "Title: LoudVA" \
		-H "Tags: white_check_mark" \
		${NOTIFICATION_URL}

default_power_mode:
	@echo "____Setting the Jetsons to Default Power Mode____"
	@ansible ${ANSIBLE_OPTS} Workers -a "nvpmodel -m 0" -u iloudaros --become

send_makefile:
	@echo "____Sending Makefile to the Jetsons____"
	@ansible ${ANSIBLE_OPTS} Workers -m copy -a "src=~/LoudVA/makefile dest=/home/iloudaros/LoudVA/makefile" -u iloudaros --become

add_specs_to_profiling:
	python3 scripts/python/add_specs.py measurements/archive/Representative/Profiling.csv data/devices/gpu_specs.csv LoudController/LoudPredictor/costs/agnostic/data.csv

generate_event_log:
	cd LoudController/LoudGenerator && python3 LoudGenerator.py

### To be run on the Jetsons ###

model:
	@echo ${model}

# Min and Max GPU Frequencies
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

watch_measurements_log:
	watch -n 1 cat measurements/log

watch_triton_log:
	watch -n 1 cat ../tritonserver/triton.log

jetpack_version:
	sudo apt-cache show nvidia-jetpack
	echo "Remember to check the linux version from https://docs.nvidia.com/jetson/archives/index.html"

################################################















############### Tests and Checks ###############
### To be run on the Controller ###
ping_workers:
	@echo "____Pinging the Jetsons____"
	@ansible ${ANSIBLE_OPTS} all -m ping

check_LoudController:
	@echo "____Checking LoudController____"
	@if curl --max-time 2 -s http://127.0.0.1:8000/ | grep -q "Welcome to LoudVA!"; then \
		echo "✅ LoudController is running on port 8000"; \
	elif curl --max-time 2 -s http://127.0.0.1:5000/ | grep -q "Welcome to LoudVA!"; then \
		echo "✅ LoudController is running in Debug mode (port 5000)"; \
	else \
		echo "❌ LoudController check failed on both ports"; \
	fi


check_triton: 
	@echo "____Checking Triton on the Jetsons____"
	@echo "🔍 Sending an inference request to all Jetson devices..." && \
	( \
	rm -f /tmp/LJ0 /tmp/LJ1 /tmp/LJ2 /tmp/AGX /tmp/NX0 /tmp/NX1; \
	python3 ~/tritonserver2_19/clients/python/image_client.py -m inception_graphdef -c 3 -s INCEPTION data/images/brown_bear.jpg --url 192.168.0.120:8000 --protocol HTTP > /dev/null 2>&1 && echo 1 > /tmp/LJ0 || echo 0 > /tmp/LJ0 & \
	python3 ~/tritonserver2_19/clients/python/image_client.py -m inception_graphdef -c 3 -s INCEPTION data/images/brown_bear.jpg --url 192.168.0.121:8000 --protocol HTTP > /dev/null 2>&1 && echo 1 > /tmp/LJ1 || echo 0 > /tmp/LJ1 & \
	python3 ~/tritonserver2_19/clients/python/image_client.py -m inception_graphdef -c 3 -s INCEPTION data/images/brown_bear.jpg --url 192.168.0.122:8000 --protocol HTTP > /dev/null 2>&1 && echo 1 > /tmp/LJ2 || echo 0 > /tmp/LJ2 & \
	python3 ~/tritonserver2_34/clients/python/image_client.py -m inception_graphdef -c 3 -s INCEPTION data/images/brown_bear.jpg --url 147.102.37.108:8000 --protocol HTTP > /dev/null 2>&1 && echo 1 > /tmp/AGX || echo 0 > /tmp/AGX & \
	python3 ~/tritonserver2_34/clients/python/image_client.py -m inception_graphdef -c 3 -s INCEPTION data/images/brown_bear.jpg --url 192.168.0.110:8000 --protocol HTTP > /dev/null 2>&1 && echo 1 > /tmp/NX0 || echo 0 > /tmp/NX0 & \
	python3 ~/tritonserver2_34/clients/python/image_client.py -m inception_graphdef -c 3 -s INCEPTION data/images/brown_bear.jpg --url 147.102.37.122:8000 --protocol HTTP > /dev/null 2>&1 && echo 1 > /tmp/NX1 || echo 0 > /tmp/NX1 & \
	wait; \
	if [ $$(cat /tmp/LJ0) -eq 1 ]; then echo "✅ LoudJetson0: Triton server is running successfully."; else echo "❌ LoudJetson0: Triton server check failed."; fi; \
	if [ $$(cat /tmp/LJ1) -eq 1 ]; then echo "✅ LoudJetson1: Triton server is running successfully."; else echo "❌ LoudJetson1: Triton server check failed."; fi; \
	if [ $$(cat /tmp/LJ2) -eq 1 ]; then echo "✅ LoudJetson2: Triton server is running successfully."; else echo "❌ LoudJetson2: Triton server check failed."; fi; \
	if [ $$(cat /tmp/AGX) -eq 1 ]; then echo "✅ agx-xavier-00: Triton server is running successfully."; else echo "❌ agx-xavier-00: Triton server check failed."; fi; \
	if [ $$(cat /tmp/NX0) -eq 1 ]; then echo "✅ xavier-nx-00: Triton server is running successfully."; else echo "❌ xavier-nx-00: Triton server check failed."; fi; \
	if [ $$(cat /tmp/NX1) -eq 1 ]; then echo "✅ xavier-nx-01: Triton server is running successfully."; else echo "❌ xavier-nx-01: Triton server check failed."; fi; \
	) && \
	echo "🔍 Triton server checks completed."

check_WorkerController:
	@echo "____Checking WorkerController____"
	@echo "🔍 Sending a request to check if the WorkerController is running on all specified hosts..." && \
	( \
	rm -f /tmp/LJ0 /tmp/LJ1 /tmp/LJ2 /tmp/AGX /tmp/NX0 /tmp/NX1; \
	curl -s --max-time 2 http://192.168.0.120:5000/ > /tmp/LJ0 & \
	curl -s --max-time 2 http://192.168.0.121:5000/ > /tmp/LJ1 & \
	curl -s --max-time 2 http://192.168.0.122:5000/ > /tmp/LJ2 & \
	curl -s --max-time 2 http://147.102.37.108:5000/ > /tmp/AGX & \
	curl -s --max-time 2 http://192.168.0.110:5000/ > /tmp/NX0 & \
	curl -s --max-time 2 http://147.102.37.122:5000/ > /tmp/NX1 & \
	wait; \
	if [ -s /tmp/LJ0 ] && [ $$(cat /tmp/LJ0) = 'running' ]; then echo "✅ LoudJetson0: WorkerController is running successfully."; else echo "❌ LoudJetson0: WorkerController check failed."; fi; \
	if [ -s /tmp/LJ1 ] && [ $$(cat /tmp/LJ1) = 'running' ]; then echo "✅ LoudJetson1: WorkerController is running successfully."; else echo "❌ LoudJetson1: WorkerController check failed."; fi; \
	if [ -s /tmp/LJ2 ] && [ $$(cat /tmp/LJ2) = 'running' ]; then echo "✅ LoudJetson2: WorkerController is running successfully."; else echo "❌ LoudJetson2: WorkerController check failed."; fi; \
	if [ -s /tmp/AGX ] && [ $$(cat /tmp/AGX) = 'running' ]; then echo "✅ agx-xavier-00: WorkerController is running successfully."; else echo "❌ agx-xavier-00: WorkerController check failed."; fi; \
	if [ -s /tmp/NX0 ] && [ $$(cat /tmp/NX0) = 'running' ]; then echo "✅ xavier-nx-00: WorkerController is running successfully."; else echo "❌ xavier-nx-00: WorkerController check failed."; fi; \
	if [ -s /tmp/NX1 ] && [ $$(cat /tmp/NX1) = 'running' ]; then echo "✅ xavier-nx-01: WorkerController is running successfully."; else echo "❌ xavier-nx-01: WorkerController check failed."; fi; \
	) && \
	echo "🔍 WorkerController checks completed."

check_resources_LoudController:
	@echo "____Checking Resources on the Controller____"
	@curl -s http://localhost:5000/resources

is_triton_running:
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_PLAYBOOK_DIR}/is_triton_running.yaml

check_triton_client:
	@echo "____Checking Triton Client____"
	@python3 LoudController/triton_client.py -m inception_graphdef -b 4 -c 1 -s INCEPTION data/images/ --url 147.102.37.122:8000 --protocol HTTP

check: check_LoudController check_triton check_triton_client check_WorkerController
	@echo "\n🔍 Final Test : Test_LoudVA.py"
	python3 /home/louduser/LoudVA/tests/Test_LoudVA.py
	@echo "Check Complete"

simulate_workload:
	@echo "____Simulating Workload____"
	@python3 LoudController/Experiments/Simulate_Workload.py --random-latency

performance_profiling: update_workers is_triton_running
	@echo "____Beginning The performance profiling____"
	@echo "(This will take a while)"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_PLAYBOOK_DIR}/performance_profiling.yaml -u iloudaros
	@echo "✅ : Performance Profiling Complete"
	@curl \
		-d "Performance Profiling complete" \
		-H "Title: LoudVA" \
		-H "Tags: white_check_mark" \
		${NOTIFICATION_URL}

eval_LoudIntervalPredictor:
	@echo "____Evaluating the Predictor____"
	python3 LoudController/LoudPredictor/input/LoudIntervalPredictor.py --plot
	python3 LoudController/LoudPredictor/input/eval/IntervalPredictionEvaluator.py --generator_log LoudController/LoudGenerator/event_log.csv --predictor_log LoudController/LoudPredictor/input/interval_prediction_log.csv

eval_LoudFramePredictor:
	@echo "____Evaluating the Predictor____"
	python3 LoudController/LoudPredictor/input/LoudFramePredictor.py --log_filename LoudController/LoudMonitor/frame_monitor_log.csv --plot
	python3 LoudController/LoudPredictor/input/eval/FramePredictionEvaluator.py --actual_log_filename LoudController/LoudMonitor/frame_monitor_log.csv --prediction_log_filename LoudController/LoudPredictor/input/frame_prediction_log.csv

eval_specific_LoudCostPredictors:
	@echo "____Evaluating the Predictors____"
	@cd LoudController/LoudPredictor/costs/specific && python3 LCP-agx.py &
	@cd LoudController/LoudPredictor/costs/specific && python3 LCP-nano.py &
	@cd LoudController/LoudPredictor/costs/specific && python3 LCP-nx.py 

eval_agnostic_LoudCostPredictor: add_specs_to_profiling
	@echo "____Evaluating the Predictor____"
	@cd LoudController/LoudPredictor/costs/agnostic && python3 LoudCostPredictor.py

notify:
	@curl \
		-d "Testing Notification" \
		-H "Title: LoudVA" \
		-H "Tags: white_check_mark" \
		${NOTIFICATION_URL}

tegrastats_log_name = 2025-04-04_12:15:29_id9_loud_tegrastats

remote_start_tegrastats:
	@echo "____Starting tegrastats on the Jetsons____"
	@ansible ${ANSIBLE_OPTS} Workers -a "sudo tegrastats --interval 200 --logfile /home/iloudaros/${tegrastats_log_name} --start" -u iloudaros --become

remote_stop_tegrastats:
	@echo "____Stopping tegrastats on the Jetsons____"
	@ansible ${ANSIBLE_OPTS} Workers -a "sudo tegrastats --stop" -u iloudaros --become

retrieve_tegrastats:
	@echo "____Retrieving tegrastats from the Jetsons____"
	@ansible ${ANSIBLE_OPTS} Workers -m fetch -a "src=/home/iloudaros/${tegrastats_log_name} dest=measurements/power" -u iloudaros --become

remote_delete_tegrastats:
	@echo "____Deleting tegrastats on the Jetsons____"
	@ansible ${ANSIBLE_OPTS} Workers -a "rm /home/iloudaros/${tegrastats_log_name}" -u iloudaros --become


### To be run on the Jetsons ###
CONCURRENCY_FLOOR = 50
CONCURRENCY_LIMIT = 60

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

measure_network:
	@echo "Starting the measurement."
	@bash scripts/shell/measure_network.sh -i 147.102.37.108:8000 -o ./measurements/network -s 1 -e 64
	@echo "Finished measuring."
	@python3 scripts/python/extract_network_cost.py ./measurements/network -o ./measurements/network/network_cost.csv


################################################















############### Experiments ###############
experiment_1:
	@echo "____Running Experiment 1____"
	@python3 LoudController/Experiments/Experiment_1.py
	@curl \
		-d "Experiment 1: Complete" \
		-H "Title: LoudVA" \
		-H "Tags: white_check_mark" \
		${NOTIFICATION_URL}


report: stop_LoudController
	@python3 scripts/python/generate_report.py --top-folder /home/louduser/LoudVA/experiment_results_keep --network-cost-csv /home/louduser/LoudVA/measurements/network/network_cost.csv 
#--exclude-ids 0

aggregate_results:
	@python3 scripts/python/aggregate_results.py  /home/louduser/LoudVA/experiment_results_keep/experiment_report.csv

report_and_plot: report aggregate_results plot_aggregated_results

experiment_2:
	@echo "____Running Experiment 2____"
	@python3 LoudController/Experiments/Experiment_2.py
	@curl \
		-d "Experiment 2: Complete" \
		-H "Title: LoudVA" \
		-H "Tags: white_check_mark" \
		${NOTIFICATION_URL} 

experiment_3: stop_LoudController
	@echo "____Running Experiment 3____"
	@python3 LoudController/Experiments/Experiment_3.py
	@curl \
		-d "Experiment 3: Complete" \
		-H "Title: LoudVA" \
		-H "Tags: white_check_mark" \
		${NOTIFICATION_URL} 

experiments: experiment_1 experiment_2
	@echo "Experiments Complete"

################################################















############## Plots ################
visualize_events:
	@python3 LoudController/LoudGenerator/visualize.py



LoudScheduler_logs = "/home/louduser/LoudVA/experiment_results_copy/loud_prof/2025-02-07_22:51:05_id0_loud_prof_request_log.csv,/home/louduser/LoudVA/experiment_results_copy/loud_prof/2025-02-07_22:51:05_id0_loud_tegrastats"

FixedBatch_logs = "2025-01-30_04:44:12_round_robin_request_log.csv,measurements/power/agx-xavier-00/home/iloudaros/2025-01-30_04:44:12_round_robin_tegrastats"

Interval_logs = "2025-01-30_05:26:40_random_request_log.csv,measurements/power/agx-xavier-00/home/iloudaros/2025-01-30_05:26:40_random_tegrastats"

Trasnparent_logs = ""

StressScheduler_logs = "2025-01-30_10:26:15_stress_request_log.csv,measurements/power/agx-xavier-00/home/iloudaros/2025-01-30_10:26:15_stress_tegrastats"


plot_activity:
	@python3 plots/LoudVA_activity.py --logs ${LoudScheduler_logs} --plot-latency --plot-power --align-zero --subplots

gantt_request_log:
	@python3 plots/gantt.py /home/louduser/LoudVA/experiment_results/loud_pred/2025-02-15_04:07:40_id0_loud_pred_request_log.csv -o /home/louduser/LoudVA/experiment_results/loud_pred/lala.pdf

plot_freqs:
	@python3 plots/LoudVA_activity.py --logs ${LoudScheduler_logs} ${RoundRobinScheduler_logs} ${RandomScheduler_logs} --plot-gpu-freq --align-zero --subplots

plot_stress:
	@python3 plots/LoudVA_activity.py --logs ${StressScheduler_logs} --plot-latency --plot-temperature --align-zero 

plot_aggregated_results:
	@python3 plots/plot_aggregated_results.py /home/louduser/LoudVA/experiment_results_keep/experiment_report_aggregated.csv


################################################















################## Clean Up ####################
delete_LoudVA:
	@echo "____Deleting LoudVA from the Jetsons____"
	@ansible ${ANSIBLE_OPTS} Workers -a "rm -r /home/iloudaros/LoudVA" -u iloudaros --become

delete_triton:
	@echo "____Removing Triton from the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_PLAYBOOK_DIR}/delete_triton.yaml

delete_flags:
	@echo "____Deleting Flags from the Jetsons____"
	@ansible ${ANSIBLE_OPTS} Workers -a "rm /tmp/ansible/flags/triton_running.flag" -u iloudaros --become

clean: delete_LoudVA delete_triton 
	@echo "✅ : Clean Up Complete"

	
delete_measurements:
	@echo "Deleting..."
	@rm -r measurements/*
	@touch measurements/.gitkeep