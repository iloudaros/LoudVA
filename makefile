include .environment #for our credentials, making it easy to reuse and add to .gitignore
ANSIBLE_DIRECTORY = ./ansible
ANSIBLE_OPTS = -i ${ANSIBLE_DIRECTORY}/inventory.ini -e "ansible_become_pass=${PASS}"

.PHONY: sync_time download_triton initialise_Jetsons setup_system start_triton


test:
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/test.yaml


###### System Initialization and Setup #######
# To be run on LoudGateway
################################################
sync_time: 
	@echo "____Setting Correct Time and Date on Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/sync_time.yaml

print_time:
	@echo "____What time is it?____"
	@ansible ${ANSIBLE_OPTS} Workers -a "date" -u iloudaros

download_triton:
	@echo "____Downloading and Sending triton to the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/download_triton.yaml

install_dependecies:
	@echo "____Installing Dependencies on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/install_dependencies.yaml

create_model_repository:
	@echo "____Creating Model Directory on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/create_model_repository.yaml

initialise_Jetsons: sync_time install_dependecies download_triton create_model_repository

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
	mkdir ~/tritonserver2_19
	tar zxvf ~/tritonserver2_19.tgz -C ~/tritonserver2_19
	mkdir ~/tritonserver2_44
	tar zxvf ~/tritonserver2_44.tgz -C ~/tritonserver2_44
	
	#### Run python wheels for each version of Triton client ####
	
	python3 -m pip install --upgrade ~/tritonserver/clients/python/tritonclient-2.19.0-py3-none-any.whl[all]
	python3 -m pip install --upgrade ~/tritonserver/clients/python/tritonclient-2.44.0-py3-none-manylinux2014_aarch64.whl[all]

client_download_triton:
	wget https://github.com/triton-inference-server/server/releases/download/v2.19.0/tritonserver2.19.0-jetpack4.6.1.tgz
	mv tritonserver2.19.0-jetpack4.6.1.tgz ~/tritonserver2_19.tgz	
	wget https://github.com/triton-inference-server/server/releases/download/v2.44.0/tritonserver2.44.0-igpu.tgz
	mv tritonserver2.44.0-igpu.tgz ~/tritonserver2_44.tgz

install_tao:
	@echo "____Installing TAO on The Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/install_tao.yaml

setup_system: initialise_Jetsons install_tao client_setup
	@echo "✅ : System Setup Complete"

update_workers:
	@echo "____Updating the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/update_workers.yaml

clone_LoudVA:
	@echo "____Cloning LoudVA to the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/clone_LoudVA.yaml

delete_LoudVA:
	@echo "____Deleting LoudVA from the Jetsons____"
	@ansible ${ANSIBLE_OPTS} LoudJetsons -a "rm -r /home/iloudaros/LoudVA" -u iloudaros --become

delete_tmp_flags:
	@echo "____Deleting Flags from the Jetsons____"
	@ansible ${ANSIBLE_OPTS} LoudJetsons -a "rm ansible/flags/triton_running.flag" -u iloudaros --become

print_flags:
	@echo "____Printing Flags from the Jetsons____"
	@ansible ${ANSIBLE_OPTS} Workers -a "ls /ansible/flags" -u iloudaros --become
################################################



############### Tests and Checks ###############
# To be run on LoudGateway
check_system: is_triton_running
	@(python3 ~/tritonserver/clients/python/image_client.py -m inception_graphdef -c 3 -s INCEPTION ~/LoudVA/data/images/brown_bear.jpg --url 192.168.0.120:8000 --protocol HTTP && echo "LoudJetson0✅") &
	@(python3 ~/tritonserver/clients/python/image_client.py -m inception_graphdef -c 3 -s INCEPTION ~/LoudVA/data/images/brown_bear.jpg --url 192.168.0.121:8000 --protocol HTTP && echo "LoudJetson1✅") &
	@(python3 ~/tritonserver/clients/python/image_client.py -m inception_graphdef -c 3 -s INCEPTION ~/LoudVA/data/images/brown_bear.jpg --url 192.168.0.122:8000 --protocol HTTP && echo "LoudJetson2✅")

is_triton_running:
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/is_triton_running.yaml

performance_profiling: update_workers is_triton_running
	@echo "____Beginning The performance profiling____"
	@echo "(This will take a while)"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/performance_profiling.yaml -u iloudaros 
	@curl -d "Performance Profiling complete" ${NOTIFICATION_URL}

# To be run on the Jetsons
CONCURRENCY_FLOOR = 1
CONCURRENCY_LIMIT = 13

MEASUREMENT_MODE = count_windows #time_windows or count_windows

## used with time_windows with option --measurement-interval
MEASUREMENT_INTERVAL = 5000

## used with count_windows with option --measurement-request-count
MEASUREMENT_COUNT = 50

measure_performance:
	/home/iloudaros/tritonserver/clients/bin/perf_analyzer -m inception_graphdef --concurrency-range ${CONCURRENCY_FLOOR}:${CONCURRENCY_LIMIT} --measurement-mode ${MEASUREMENT_MODE} 

measure_performance_csv:
	/home/iloudaros/tritonserver/clients/bin/perf_analyzer -m inception_graphdef --concurrency-range ${CONCURRENCY_FLOOR}:${CONCURRENCY_LIMIT} --measurement-mode ${MEASUREMENT_MODE} -f measurements/performance/performance_measurements.csv


MEASUREMENT_INTERVAL2 = 500 #in ms
measure_power:
	@sudo tegrastats --interval ${MEASUREMENT_INTERVAL2} --start --logfile ~/LoudVA/measurements/power/tegra_log_${MEASUREMENT_INTERVAL2} && ~/tritonserver/clients/bin/perf_analyzer -m inception_graphdef --concurrency-range 1:3 && sudo tegrastats --stop
	@sudo bash ~/LoudVA/scripts/clean_measurements.sh ~/LoudVA/measurements/power/tegra_log_${MEASUREMENT_INTERVAL2} ~/LoudVA/measurements/power/power_measurement_${MEASUREMENT_INTERVAL2}
	@bash ~/LoudVA/scripts/mean_median.sh ~/LoudVA/measurements/power/power_measurement_${MEASUREMENT_INTERVAL2}
	@echo "Check ~/LoudVA/measurements/power/power_measurement_${MEASUREMENT_INTERVAL2} for the power measurements"

measure_idle_power:
	@sudo tegrastats --interval ${MEASUREMENT_INTERVAL2} --start --logfile ~/LoudVA/measurements/power/idle_tegra_log_${MEASUREMENT_INTERVAL2} && sleep 10 && sudo tegrastats --stop
	@sudo bash ~/LoudVA/scripts/clean_measurements.sh ~/LoudVA/measurements/power/idle_tegra_log_${MEASUREMENT_INTERVAL2} ~/LoudVA/measurements/power/idle_power_measurement_${MEASUREMENT_INTERVAL2}
	@bash ~/LoudVA/scripts/mean_median.sh ~/LoudVA/measurements/power/idle_power_measurement_${MEASUREMENT_INTERVAL2}
	@echo "Check ~/LoudVA/measurements/power/idle_power_measurement_${MEASUREMENT_INTERVAL2} for the power measurements"

measure_performance_and_power:
	@sudo tegrastats --interval ${MEASUREMENT_INTERVAL2} --start --logfile /home/iloudaros/LoudVA/measurements/power/tegra_log && /home/iloudaros/tritonserver/clients/bin/perf_analyzer -m inception_graphdef --concurrency-range ${CONCURRENCY_FLOOR}:${CONCURRENCY_LIMIT} --measurement-mode ${MEASUREMENT_MODE} -f /home/iloudaros/LoudVA/measurements/performance/performance_measurements.csv && sudo tegrastats --stop
	@sudo bash /home/iloudaros/LoudVA/scripts/clean_measurements.sh /home/iloudaros/LoudVA/measurements/power/tegra_log /home/iloudaros/LoudVA/measurements/power/power_measurement
	@bash /home/iloudaros/LoudVA/scripts/mean_median.sh /home/iloudaros/LoudVA/measurements/power/power_measurement
	@echo "Check /home/iloudaros/LoudVA/measurements/power/power_measurement_stats for the power measurements"
################################################



################ Quick Access ##################
# To be run on LoudGateway
start_triton: sync_time
	@echo "____Starting Triton on the Jetsons____"
	@sleep 1
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/start_triton.yaml 
	@echo "Loading..."
	@sleep 20
	@make is_triton_running 

start_triton_gpumetrics:
	@echo "____Starting Triton on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/start_triton_gpumetrics.yaml

stop_triton:
	@echo "____Stopping Triton on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/stop_triton.yaml

start_LoudVA_server:
	@echo "____Starting LoudVA____"
	@python3 ~/LoudVA/LoudVA/LoudVA.py 

start_LoudVA: start_triton start_LoudVA_server

reboot_workers: stop_triton
	@echo "____Rebooting the Jetsons____"
	@sleep 1
	@ansible ${ANSIBLE_OPTS} LoudJetsons -a "reboot" -u iloudaros --become &
	@echo "Rebooting..."
	@sleep 30
	@echo "Jetsons Rebooted"
	@sleep 5
	@make start_triton

remove_triton_running_flag:
	@echo "____Removing the triton running flag____"
	@ansible ${ANSIBLE_OPTS} LoudJetsons -a "rm /ansible/flags/triton_running.flag" -u iloudaros --become

default_power_mode:
	@echo "____Setting the Jetsons to Default Power Mode____"
	@ansible ${ANSIBLE_OPTS} LoudJetsons -a "nvpmodel -m 0" -u iloudaros --become


# To be run on the Jetsons
# .76800000 153600000 230400000 .307200000 384000000 460800000 .537600000 614400000 691200000 .768000000 844800000 .921600000
GPU_MIN_FREQ = 76800000 
GPU_MAX_FREQ = 921600000
change_gpu_freq:
	@sudo sh -c 'echo '${GPU_MIN_FREQ}' > /sys/devices/57000000.gpu/devfreq/57000000.gpu/min_freq'
	@sudo sh -c 'echo '${GPU_MAX_FREQ}' > /sys/devices/57000000.gpu/devfreq/57000000.gpu/max_freq'

current_gpu_freq:
	echo "Current GPU Frequency"
	@cat /sys/devices/57000000.gpu/devfreq/57000000.gpu/cur_freq
	echo "Upper Boundary"
	@cat /sys/devices/57000000.gpu/devfreq/57000000.gpu/max_freq
	echo "Lower Boundary"
	@cat /sys/devices/57000000.gpu/devfreq/57000000.gpu/min_freq

3D_scaling:
	sudo sh -c 'echo 1 > /sys/devices/57000000.gpu/enable_3d_scaling'

available_frequencies:
	cat /sys/devices/57000000.gpu/devfreq/57000000.gpu/available_frequencies

edit_nvpmodel:
	sudo nano /etc/nvpmodel/nvpmodel_t210_jetson-nano.conf

cat_nvpmodel:
	cat /etc/nvpmodel/nvpmodel_t210_jetson-nano.conf

watch_log:
	watch -n 1 cat /home/iloudaros/measurements/Performance.log

# To be run on the client
check_api:
	@curl 127.0.0.1:5000
################################################





################## Clean Up ####################
clean: delete_LoudVA
	@echo "____Removing Triton from the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/delete_triton.yaml
	@echo "____Removing Triton from LoudGateway____"
	rm -r ~/tritonserver*
	rm -r ~/LoudVA/measurements/*

delete_measurements:
	@echo "Deleting..."
	@rm -r ~/LoudVA/measurements/*
	@touch ~/LoudVA/measurements/.gitkeep