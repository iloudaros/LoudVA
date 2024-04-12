#!/bin/bash

# Set the username and the path to the SSH key on the local machine
username=iloudaros

# Set the list of remote servers
servers=(
    LoudJetson0
    LoudJetson1
    LoudJetson2
)

# Loop through the servers and copy the SSH key
for server in "${servers[@]}"
do
    echo "Copying SSH key to $server..."
    ssh-copy-id $username@$server
done
