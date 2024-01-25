PASS = [password]
ANSIBLE_DIRECTORY = ./ansible
ANSIBLE_OPTS = -i ${ANSIBLE_DIRECTORY}/inventory.ini -e "ansible_become_pass=${PASS}"


initialise_Jetsons:
	@echo "____Setting Correct Time and Date on Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/sync_time.yaml
	@echo "____Downloading and Sending triton to the Jetsons____"
	@ansible-playbook ${ANSIBLE_OPTS} ${ANSIBLE_DIRECTORY}/download_triton.yaml