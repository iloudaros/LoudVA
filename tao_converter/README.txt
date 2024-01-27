Installation instructions:

This document captures simple instructions to run the TAO converter. 


1. Copy the executable to the target device 
2. Install openssl library using the following command.
   1. $ sudo apt-get install libssl-dev
3. Export the following environment variables
   1. For an x86 platform:
      1. $ export TRT_LIB_PATH="/usr/lib/x86_64-linux-gnu"
      2. $ export TRT_INC_PATH="/usr/include/x86_64-linux-gnu"
   2. For an aarch platform:
      1. export TRT_LIB_PATH=/usr/lib/aarch64-linux-gnu
      2. export TRT_INCLUDE_PATH=/usr/include/aarch64-linux-gnu
4. Run the tao-converter

Sample usage:


        ./tao-converter -h
