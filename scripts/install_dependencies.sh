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

######### ONNX #########
pip3 install --upgrade flake8 flatbuffers


######### PyTorch #########
echo ______PyTorch Dependencies______
apt-get -y install autoconf \
            bc \
            g++-8 \
            gcc-8 \
            clang-8 \
            lld-8
pip3 install --upgrade expecttest xmlrunner hypothesis aiohttp pyyaml scipy ninja typing_extensions protobuf


echo ______PyTorch wheel______
pip3 install --upgrade https://developer.download.nvidia.com/compute/redist/jp/v461/pytorch/torch-1.11.0a0+17540c5+nv22.01-cp36-cp36m-linux_aarch64.whl pip3 install --upgrade https://developer.download.nvidia.com/compute/redist/jp/v50/pytorch/torch-1.12.0a0+2c916ef.nv22.3-cp38-cp38-linux_aarch64.whl


######## Utilities that we need #########
echo ______Utilities______
sudo apt install screen
sudo apt install strace
sudo pip3 install -U jetson-stats



####### The LoudVA repo ########
echo ______LoudVA______
cd /home/iloudaros
git clone https://github.com/iloudaros/LoudVA.git