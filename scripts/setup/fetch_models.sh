set -ex

# TensorFlow inception
mkdir -p /home/iloudaros/tritonserver/model_repository/inception_graphdef/1
wget -O /tmp/inception_v3_2016_08_28_frozen.pb.tar.gz \
     https://storage.googleapis.com/download.tensorflow.org/models/inception_v3_2016_08_28_frozen.pb.tar.gz
(cd /tmp && tar xzf inception_v3_2016_08_28_frozen.pb.tar.gz)
mv /tmp/inception_v3_2016_08_28_frozen.pb /home/iloudaros/tritonserver/model_repository/inception_graphdef/1/model.graphdef

