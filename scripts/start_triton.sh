sudo sh -c 'cd /home/iloudaros/tritonserver/ && nohup ./bin/tritonserver  --model-repository=./model_repository --backend-directory=./backends --backend-config=tensorflow,version=2 &'
sleep 5