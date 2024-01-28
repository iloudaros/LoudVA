include .environment #for our credentials, making it easy to reuse and add to .gitignore
ANSIBLE_DIRECTORY = ./ansible
ANSIBLE_OPTS = -i ${ANSIBLE_DIRECTORY}/inventory.ini -e "ansible_become_pass=${PASS}"

.PHONY: sync_time download_triton initialise_Jetsons setup_system start_triton


###### System Iniitialization and Setup #######
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
	pip3 install --upgrade wheel setuptools cython
	pip3 install --upgrade grpcio-tools numpy==1.19.4 future attrdict
	cd ~
	mkdir ~/tritonserver
	tar zxvf ~/tritonserver2.19.0-jetpack4.6.1.tgz -C ~/tritonserver
	python3 -m pip install --upgrade clients/python/tritonclient-2.19.0-py3-none-any.whl[all]


setup_system: initialise_Jetsons client_setup

################################################



start_triton:
	@echo "____Starting Triton on the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/start_triton.yaml


