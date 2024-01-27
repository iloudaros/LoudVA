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
    libb64-dev \
    libre2-dev \
    libssl-dev \
    libtool \
    libboost-dev \
    rapidjson-dev \
    patchelf \
    pkg-config \
    libopenblas-dev \
    libarchive-dev \
    zlib1g-dev \
    python3 \
    python3-pip \
    python3-dev


echo ______PyTorch Dependencies______
apt-get -y install autoconf \
            bc \
            g++-8 \
            gcc-8 \
            clang-8 \
            lld-8
pip3 install --upgrade expecttest xmlrunner hypothesis aiohttp pyyaml scipy ninja typing_extensions protobuf


echo ______PyTorch wheel______
pip3 install --upgrade https://developer.download.nvidia.com/compute/redist/jp/v461/pytorch/torch-1.11.0a0+17540c5+nv22.01-cp36-cp36m-linux_aarch64.whl


echo ______client libraries and examples______

apt-get install -y --no-install-recommends \
            curl \
            jq

pip3 install --upgrade wheel setuptools cython && \
pip3 install --upgrade grpcio-tools numpy==1.19.4 future attrdict
pip3 install --upgrade six requests flake8 flatbuffers pillow

#######################################