include .environment #for our credentials, making it easy to reuse and add to .gitignore
ANSIBLE_DIRECTORY = ./ansible
ANSIBLE_OPTS = -i ${ANSIBLE_DIRECTORY}/inventory.ini -e "ansible_become_pass=${PASS}"

.PHONY: sync_time download_triton initialise_Jetsons setup_system start_triton


###### System Initialization and Setup #######
# To be run on LoudGateway
################################################
sync_time: 
	@echo "____Setting Correct Time and Date on Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/sync_time.yaml

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
	sudo apt-get install -y --no-install-recommends \
        curl \
        pkg-config \
        python3 \
        python3-pip \
        python3-dev
	pip3 install --upgrade wheel setuptools cython testresources
	pip3 install --upgrade grpcio-tools numpy future attrdict pillow image
	pip install protobuf==3.20
	pip3 install flask
	mkdir ~/tritonserver
	tar zxvf ~/tritonserver.tgz -C ~/tritonserver
	python3 -m pip install --upgrade ~/tritonserver/clients/python/tritonclient-2.19.0-py3-none-any.whl[all]

client_download_triton:
	wget https://github.com/triton-inference-server/server/releases/download/v2.19.0/tritonserver2.19.0-jetpack4.6.1.tgz
	mv tritonserver2.19.0-jetpack4.6.1.tgz ~/tritonserver.tgz	

install_tao:
	@echo "____Installing TAO on The Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/install_tao.yaml

setup_system: initialise_Jetsons install_tao client_setup

update_workers:
	@echo "____Updating the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/update_workers.yaml

clone_LoudVA:
	@echo "____Cloning LoudVA to the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/clone_LoudVA.yaml

delete_LoudVA:
	@echo "____Deleting LoudVA from the Jetsons____"
	@ansible ${ANSIBLE_OPTS} LoudJetsons -a "rm -r /home/iloudaros/LoudVA" -u iloudaros --become
################################################



############### Tests and Checks ###############
# To be run on LoudGateway
check_system: start_triton
	@(python3 ~/tritonserver/clients/python/image_client.py -m inception_graphdef -c 3 -s INCEPTION ~/LoudVA/data/images/brown_bear.jpg --url 192.168.0.120:8000 --protocol HTTP && echo "LoudJetson0✅") &
	@(python3 ~/tritonserver/clients/python/image_client.py -m inception_graphdef -c 3 -s INCEPTION ~/LoudVA/data/images/brown_bear.jpg --url 192.168.0.121:8000 --protocol HTTP && echo "LoudJetson1✅") &
	@(python3 ~/tritonserver/clients/python/image_client.py -m inception_graphdef -c 3 -s INCEPTION ~/LoudVA/data/images/brown_bear.jpg --url 192.168.0.122:8000 --protocol HTTP && echo "LoudJetson2✅")

triton_running:
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/triton_running.yaml

performance_profiling: start_triton check_system #update_workers
	@echo "____Beginning The performance profiling____"
	@echo "(This will take a while)"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/performance_profiling.yaml -u iloudaros 


# To be run on the Jetsons
CONCURRENCY_LIMIT = 13
measure_performance:
	/home/iloudaros/tritonserver/clients/bin/perf_analyzer -m inception_graphdef --concurrency-range 1:${CONCURRENCY_LIMIT}

measure_performance_csv:
	/home/iloudaros/tritonserver/clients/bin/perf_analyzer -m inception_graphdef --concurrency-range 1:${CONCURRENCY_LIMIT} --measurement-interval 10000 -f measurements/performance_measurements.csv


MEASUREMENT_INTER = 500 #in ms
measure_power:
	@> ~/LoudVA/measurements/measurement.log
	@sudo tegrastats --interval ${MEASUREMENT_INTER} --start --logfile ~/LoudVA/measurements/power_measurement_${MEASUREMENT_INTER}.log && ~/tritonserver/clients/bin/perf_analyzer -m inception_graphdef --concurrency-range 1:3 && sudo tegrastats --stop
	@sudo bash ~/LoudVA/scripts/clean_measurements.sh ~/LoudVA/measurements/power_measurement_${MEASUREMENT_INTER}.log ~/LoudVA/measurements/clean_power_measurement_${MEASUREMENT_INTER}.log
	@bash ~/LoudVA/scripts/mean_median.sh ~/LoudVA/measurements/clean_power_measurement_${MEASUREMENT_INTER}.log
	@echo "Check ~/LoudVA/measurements/clean_power_measurement_${MEASUREMENT_INTER}.log for the power measurements"

measure_idle_power:
	@> ~/LoudVA/measurements/measurement.log
	@sudo tegrastats --interval ${MEASUREMENT_INTER} --start --logfile ~/LoudVA/measurements/idle_power_measurement_${MEASUREMENT_INTER}.log && sleep 10 && sudo tegrastats --stop
	@sudo bash ~/LoudVA/scripts/clean_measurements.sh ~/LoudVA/measurements/power_measurement_${MEASUREMENT_INTER}.log ~/LoudVA/measurements/clean_idle_power_measurement_${MEASUREMENT_INTER}.log
	@bash ~/LoudVA/scripts/mean_median.sh ~/LoudVA/measurements/clean_idle_power_measurement_${MEASUREMENT_INTER}.log
	@echo "Check ~/LoudVA/measurements/clean_idle_power_measurement_${MEASUREMENT_INTER}.log for the power measurements"
################################################



################ Quick Access ##################
# To be run on LoudGateway
start_triton:
	@echo "____Starting Triton on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/start_triton.yaml 

start_triton_gpumetrics:
	@echo "____Starting Triton on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/start_triton_gpumetrics.yaml

stop_triton:
	@echo "____Stopping Triton on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/stop_triton.yaml

start_LoudVA_server:
	@echo "____Starting LoudVA____"
	python3 ~/LoudVA/LoudVA/LoudVA.py 

start_LoudVA: start_triton start_LoudVA_server

reboot_workers: stop_triton
	@echo "____Rebooting the Jetsons____"
	@sleep 1
	@ansible ${ANSIBLE_OPTS} LoudJetsons -a "reboot" -u iloudaros --become

remove_triton_running_flag:
	@echo "____Removing the triton running flag____"
	@ansible ${ANSIBLE_OPTS} LoudJetsons -a "rm /ansible/flags/triton_running.flag" -u iloudaros --become

# To be run on the Jetsons
GPU_FREQ = 76800000 # .76800000 153600000 230400000 .307200000 384000000 460800000 .537600000 614400000 691200000 .768000000 844800000 .921600000
change_gpu_freq:
	sudo sh -c 'echo ${GPU_FREQ} > /sys/devices/57000000.gpu/devfreq/57000000.gpu/min_freq'
	sudo sh -c 'echo ${GPU_FREQ} > /sys/devices/57000000.gpu/devfreq/57000000.gpu/max_freq'

3D_scaling:
	sudo sh -c 'echo 1 > /sys/devices/57000000.gpu/enable_3d_scaling'

available_frequencies:
	cat /sys/devices/57000000.gpu/devfreq/57000000.gpu/available_frequencies

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
	