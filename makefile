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

check_system: 
	python3 ~/tritonserver/clients/python/image_client.py -m inception_graphdef -c 3 -s INCEPTION ~/LoudVA/data/images/brown_bear.jpg --url 192.168.0.120:8000 --protocol HTTP &
	python3 ~/tritonserver/clients/python/image_client.py -m inception_graphdef -c 3 -s INCEPTION ~/LoudVA/data/images/brown_bear.jpg --url 192.168.0.121:8000 --protocol HTTP &
	python3 ~/tritonserver/clients/python/image_client.py -m inception_graphdef -c 3 -s INCEPTION ~/LoudVA/data/images/brown_bear.jpg --url 192.168.0.122:8000 --protocol HTTP 

start_LoudVA_server:
	@echo "____Starting LoudVA____"
	python3 ~/LoudVA/LoudVA/LoudVA.py 

start_LoudVA: start_triton start_LoudVA_server

stop_triton:
	@echo "____Stopping Triton on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/stop_triton.yaml
################################################




################ Quick Access ##################
# To be run on LoudGateway
start_triton:
	@echo "____Starting Triton on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/start_triton.yaml

start_triton_gpumetrics:
	@echo "____Starting Triton on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/start_triton_gpumetrics.yaml


# To be run on the Jetsons
measure_time:
	~/tritonserver/clients/bin/perf_analyzer -m inception_graphdef --concurrency-range 1:6

measure_time_csv:
	~/tritonserver/clients/bin/perf_analyzer -m inception_graphdef --concurrency-range 1:6 -f measurements/performance_measurements.csv

measure_power:
	@> ~/LoudVA/measurements/measurement.log
	@sudo tegrastats --interval 2000 --start --logfile ~/LoudVA/measurements/measurement.log && ~/tritonserver/clients/bin/perf_analyzer -m inception_graphdef --concurrency-range 1:3 && sudo tegrastats --stop
	@sudo bash ~/LoudVA/scripts/clean_measurements.sh ~/LoudVA/measurements/measurement.log ~/LoudVA/measurements/clean.log
	@bash ~/LoudVA/scripts/mean_median.sh ~/LoudVA/measurements/clean.log
	@echo "Check ~/LoudVA/measurements/clean.log for the power measurements"


# To be run on the client
check_api:
	@curl 127.0.0.1:5000
################################################





################## Clean Up ####################
clean:
	@echo "____Removing Triton from the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/delete_triton.yaml
	@echo "____Removing Triton from LoudGateway____"
	rm -r ~/tritonserver*
	