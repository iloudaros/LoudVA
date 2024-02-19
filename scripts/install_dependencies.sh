#!/bin/sh

######### Triton Dependencies #########
echo ______Dependencies______
apt-get update 
apt-get install -y --no-install-recommends \
    software-properties-common \
    autoconf \
    automake \
    build-essential \
    git \
    cmake \
    libb64-dev \
    libre2-dev \
    libssl-dev \
    libtool \
    libboost-dev \
    rapidjson-dev \
    patchelf \
    pkg-config \
    libcurl4-openssl-dev \
    libopenblas-dev \
    libarchive-dev \
    zlib1g-dev \
    python3 \
    python3-pip \
    python3-dev


sudo apt install screen