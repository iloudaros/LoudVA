include .environment #for our credentials, making it easy to reuse and add to .gitignore
ANSIBLE_DIRECTORY = ./ansible
ANSIBLE_PLAYBOOK_DIR = ${ANSIBLE_DIRECTORY}/playbooks
ANSIBLE_OPTS = -f 6 -i ${ANSIBLE_DIRECTORY}/inventory.ini -e "ansible_become_pass=${PASS}"
model=$(shell tr -d '\0' < /proc/device-tree/model)


.PHONY: sync_time download_triton initialise_Jetsons system_setup start_triton


###### System Initialization and Setup #######
### To be run on the Controller ###
install_ansible:
	sudo apt update
	sudo apt install software-properties-common
	sudo add-apt-repository --yes --update ppa:ansible/ansible
	sudo apt install ansible

sync_time: 
	@echo "____Setting Correct Time and Date on Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_PLAYBOOK_DIR}/sync_time.yaml

print_time:
	@echo "____What time is it?____"
	@ansible ${ANSIBLE_OPTS} Workers -a "date" -u iloudaros

download_triton:
	@echo "____Downloading and Sending triton to the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_PLAYBOOK_DIR}/download_triton.yaml -u iloudaros

install_dependencies:
	@echo "____Installing Dependencies on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_PLAYBOOK_DIR}/install_dependencies.yaml

create_model_repository:
	@echo "____Creating Model Directory on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_PLAYBOOK_DIR}/create_model_repository.yaml

clone_LoudVA:
	@echo "____Cloning LoudVA to the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_PLAYBOOK_DIR}/clone_LoudVA.yaml

initialise_Jetsons: sync_time install_dependencies download_triton clone_LoudVA create_model_repository

triton_client_dependencies:
	@echo "Install Triton Client Dependencies..."

	# 1) Create and activate a virtual environment
	python3 -m venv .venv

	# 2) Upgrade pip, wheel, setuptools inside venv
	#    Then install all required Python packages
	@echo "Installing Python packages in virtual environment..."
	. .venv/bin/activate && \
		pip install --upgrade pip wheel setuptools && \
		pip install --upgrade cython testresources numpy future attrdict3 pillow \
			image six requests flake8 protobuf==3.20 werkzeug grpcio-tools

	@echo "Creating directories for each version of Triton client..."
	mkdir -p ~/tritonserver2_19
	tar zxvf ~/tritonserver2_19.tgz -C ~/tritonserver2_19
	mkdir -p ~/tritonserver2_34
	tar zxvf ~/tritonserver2_34.tgz -C ~/tritonserver2_34

	@echo "Installing Triton Python client wheels in the virtual environment..."
	. .venv/bin/activate && \
		pip install --upgrade ~/tritonserver2_19/clients/python/tritonclient-2.19.0-py3-none-any.whl[all] && \
		pip install --upgrade ~/tritonserver2_34/clients/python/tritonclient-2.34.0-py3-none-any.whl[all]

controller_download_triton:
	wget https://github.com/triton-inference-server/server/releases/download/v2.34.0/tritonserver2.34.0-jetpack5.1.tgz
	mv tritonserver2.34.0-jetpack5.1.tgz ~/tritonserver2_34.tgz
################################################





################ Quick Access ##################
### To be run on the Controller ###
activate_venv:
	@echo "____Activating the virtual environment____"
	. .venv/bin/activate
	@echo "Virtual environment activated"

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

watch_triton_log:
	watch -n 1 cat ../tritonserver/triton.log

################################################





############### Tests and Checks ###############
### To be run on the Controller ###
ping_workers:
	@echo "____Pinging the Jetsons____"
	@ansible ${ANSIBLE_OPTS} all -m ping

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

is_triton_running:
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_PLAYBOOK_DIR}/is_triton_running.yaml

check_triton_client:
	@echo "____Checking Triton Client____"
	@python3 LoudController/triton_client.py -m inception_graphdef -b 4 -c 1 -s INCEPTION data/images/ --url 147.102.37.108:8000 --protocol HTTP

check: check_triton check_triton_client check_WorkerController
	@echo "\n🔍 Final Test : Test_LoudVA.py"
	python3 /home/iloudaros/Desktop/LoudVA/tests/Test_LoudVA.py
	@echo "Check Complete"

simulate_workload:
	@echo "____Simulating Workload____"
	@python3 LoudController/Experiments/Simulate_Workload.py --random-latency

notify:
	@curl \
		-d "Testing Notification" \
		-H "Title: LoudVA" \
		-H "Tags: white_check_mark" \
		${NOTIFICATION_URL}

tegrastats_log_name = 2025-06-08_06:23:38_id0_round_robin_tegrastats

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

################################################





############## Plots ################

################################################





################## Clean Up ####################
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