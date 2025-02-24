import argparse
from functools import partial
import os
import sys
from PIL import Image
import numpy as np
from attrdict import AttrDict
import tritonclient.grpc as grpcclient
import tritonclient.grpc.model_config_pb2 as mc
import tritonclient.http as httpclient
from tritonclient.utils import InferenceServerException
from tritonclient.utils import triton_to_np_dtype
from werkzeug.datastructures import FileStorage
from logging_config import setup_logging
import io

if sys.version_info >= (3, 0):
    import queue
else:
    import Queue as queue


# Configure logging
logger = setup_logging()

class UserData:

    def __init__(self):
        self._completed_requests = queue.Queue()


# Callback function used for async_stream_infer()
def completion_callback(user_data, result, error):
    # passing error raise and handling out
    user_data._completed_requests.put((result, error))


def parse_model(model_metadata, model_config):
    """
    Check the configuration of a model to make sure it meets the
    requirements for an image classification network (as expected by
    this client)
    """
    if len(model_metadata.inputs) != 1:
        raise Exception("expecting 1 input, got {}".format(
            len(model_metadata.inputs)))
    if len(model_metadata.outputs) != 1:
        raise Exception("expecting 1 output, got {}".format(
            len(model_metadata.outputs)))

    if len(model_config.input) != 1:
        raise Exception(
            "expecting 1 input in model configuration, got {}".format(
                len(model_config.input)))

    input_metadata = model_metadata.inputs[0]
    input_config = model_config.input[0]
    output_metadata = model_metadata.outputs[0]

    if output_metadata.datatype != "FP32":
        raise Exception("expecting output datatype to be FP32, model '" +
                        model_metadata.name + "' output type is " +
                        output_metadata.datatype)

    # Output is expected to be a vector. But allow any number of
    # dimensions as long as all but 1 is size 1 (e.g. { 10 }, { 1, 10
    # }, { 10, 1, 1 } are all ok). Ignore the batch dimension if there
    # is one.
    output_batch_dim = (model_config.max_batch_size > 0)
    non_one_cnt = 0
    for dim in output_metadata.shape:
        if output_batch_dim:
            output_batch_dim = False
        elif dim > 1:
            non_one_cnt += 1
            if non_one_cnt > 1:
                raise Exception("expecting model output to be a vector")

    # Model input must have 3 dims, either CHW or HWC (not counting
    # the batch dimension), either CHW or HWC
    input_batch_dim = (model_config.max_batch_size > 0)
    expected_input_dims = 3 + (1 if input_batch_dim else 0)
    if len(input_metadata.shape) != expected_input_dims:
        raise Exception(
            "expecting input to have {} dimensions, model '{}' input has {}".
            format(expected_input_dims, model_metadata.name,
                   len(input_metadata.shape)))

    if type(input_config.format) == str:
        FORMAT_ENUM_TO_INT = dict(mc.ModelInput.Format.items())
        input_config.format = FORMAT_ENUM_TO_INT[input_config.format]

    if ((input_config.format != mc.ModelInput.FORMAT_NCHW) and
        (input_config.format != mc.ModelInput.FORMAT_NHWC)):
        raise Exception("unexpected input format " +
                        mc.ModelInput.Format.Name(input_config.format) +
                        ", expecting " +
                        mc.ModelInput.Format.Name(mc.ModelInput.FORMAT_NCHW) +
                        " or " +
                        mc.ModelInput.Format.Name(mc.ModelInput.FORMAT_NHWC))

    if input_config.format == mc.ModelInput.FORMAT_NHWC:
        h = input_metadata.shape[1 if input_batch_dim else 0]
        w = input_metadata.shape[2 if input_batch_dim else 1]
        c = input_metadata.shape[3 if input_batch_dim else 2]
    else:
        c = input_metadata.shape[1 if input_batch_dim else 0]
        h = input_metadata.shape[2 if input_batch_dim else 1]
        w = input_metadata.shape[3 if input_batch_dim else 2]

    return (model_config.max_batch_size, input_metadata.name,
            output_metadata.name, c, h, w, input_config.format,
            input_metadata.datatype)


def preprocess(img, format, dtype, c, h, w, scaling, protocol):
    """
    Pre-process an image to meet the size, type and format
    requirements specified by the parameters.
    """
    if c == 1:
        sample_img = img.convert('L')
    else:
        sample_img = img.convert('RGB')

    resized_img = sample_img.resize((w, h), Image.BILINEAR)
    resized = np.array(resized_img)
    if resized.ndim == 2:
        resized = resized[:, :, np.newaxis]

    npdtype = triton_to_np_dtype(dtype)
    typed = resized.astype(npdtype)

    if scaling == 'INCEPTION':
        scaled = (typed / 127.5) - 1
    elif scaling == 'VGG':
        if c == 1:
            scaled = typed - np.asarray((128,), dtype=npdtype)
        else:
            scaled = typed - np.asarray((123, 117, 104), dtype=npdtype)
    else:
        scaled = typed

    # Swap to CHW if necessary
    if format == mc.ModelInput.FORMAT_NCHW:
        ordered = np.transpose(scaled, (2, 0, 1))
    else:
        ordered = scaled

    # Channels are in RGB order. Currently model configuration data
    # doesn't provide any information as to other channel orderings
    # (like BGR) so we just assume RGB.
    return ordered


def postprocess(results, output_name, batch_size, batching):
    """
    Post-process results to show classifications.
    """

    output_array = results.as_numpy(output_name)
    if len(output_array) != batch_size:
        raise Exception("expected {} results, got {}".format(
            batch_size, len(output_array)))

    output = []
    # Include special handling for non-batching models
    for results in output_array:
        if not batching:
            results = [results]
        for result in results:
            if output_array.dtype.type == np.object_:
                cls = "".join(chr(x) for x in result).split(':')
            else:
                cls = result.split(':')
            logger.debug("{} ({}) = {}".format(cls[0], cls[1], cls[2]))
            output.append(cls)

    return output


def requestGenerator(batched_image_data, input_name, output_name, dtype, model_name, model_version, classes, protocol="http"):
    protocol = protocol.lower()

    if protocol == "grpc":
        client = grpcclient
    else:
        client = httpclient

    # Set the input data
    inputs = [client.InferInput(input_name, batched_image_data.shape, dtype)]
    inputs[0].set_data_from_numpy(batched_image_data)

    outputs = [
        client.InferRequestedOutput(output_name, class_count=classes)
    ]

    yield inputs, outputs, model_name, model_version




def convert_http_metadata_config(_metadata, _config):
    _model_metadata = AttrDict(_metadata)
    _model_config = AttrDict(_config)

    return _model_metadata, _model_config


def inference(image_sources, model_name, model_version='1', batch_size=1, classes=3, scaling='INCEPTION', url='localhost:8000', protocol='HTTP', verbose=False, async_set=False, streaming=False):
    if streaming and protocol.lower() != "grpc":
        raise Exception("Streaming is only allowed with gRPC protocol")

    try:
        if protocol.lower() == "grpc":
            triton_client = grpcclient.InferenceServerClient(url=url, verbose=verbose)
        else:
            concurrency = 20 if async_set else 1
            triton_client = httpclient.InferenceServerClient(url=url, verbose=verbose, concurrency=concurrency)
    except Exception as e:
        logger.error("client creation failed: " + str(e))
        sys.exit(1)

    try:
        model_metadata = triton_client.get_model_metadata(model_name=model_name, model_version=model_version)
    except InferenceServerException as e:
        logger.error("failed to retrieve the metadata: " + str(e))
        sys.exit(1)

    try:
        model_config = triton_client.get_model_config(model_name=model_name, model_version=model_version)
    except InferenceServerException as e:
        logger.error("failed to retrieve the config: " + str(e))
        sys.exit(1)

    if protocol.lower() == "grpc":
        model_config = model_config.config
    else:
        model_metadata, model_config = convert_http_metadata_config(model_metadata, model_config)

    max_batch_size, input_name, output_name, c, h, w, format, dtype = parse_model(model_metadata, model_config)

    # Preprocess the input sources into input data according to model requirements
    image_data = []

    for source in image_sources:
        logger.debug(f"Processing image source")
        try:
            if isinstance(source, bytes):
                img = Image.open(io.BytesIO(source))
            elif isinstance(source, FileStorage):
                source.stream.seek(0)  # Ensure the stream is at the start
                img = Image.open(source.stream)
            elif os.path.isdir(source):
                for filename in os.listdir(source):
                    filepath = os.path.join(source, filename)
                    if os.path.isfile(filepath):
                        img = Image.open(filepath)
                        image_data.append(preprocess(img, format, dtype, c, h, w, scaling, protocol.lower()))
                continue
            elif os.path.isfile(source):
                img = Image.open(source)
            else:
                logger.error(f"Invalid input source: {source}")
                continue

            image_data.append(preprocess(img, format, dtype, c, h, w, scaling, protocol.lower()))
        except Exception as e:
            logger.error(f"Error processing image source: {e}")

    if not image_data:
        logger.error("No valid images found for processing.")
        return

    # Ensure image_data is not empty before proceeding
    if len(image_data) < batch_size:
        logger.error("Not enough images to fill the batch size.")
        return

    requests = []
    responses = []
    user_data = UserData()
    sent_count = 0
    # Holds the handles to the ongoing HTTP async requests.
    async_requests = []
    
    if streaming:
        triton_client.start_stream(partial(completion_callback, user_data))

    image_idx = 0
    last_request = False

    while not last_request:
        repeated_image_data = []

        for idx in range(batch_size):
            repeated_image_data.append(image_data[image_idx])
            image_idx = (image_idx + 1) % len(image_data)
            if image_idx == 0:
                last_request = True

        if max_batch_size > 0:
            batched_image_data = np.stack(repeated_image_data, axis=0)
        else:
            batched_image_data = repeated_image_data[0]

        try:
            for inputs, outputs, model_name, model_version in requestGenerator(
                    batched_image_data, input_name, output_name, dtype, model_name, model_version, classes, protocol):
                sent_count += 1
                if streaming:
                    triton_client.async_stream_infer(
                        model_name,
                        inputs,
                        request_id=str(sent_count),
                        model_version=model_version,
                        outputs=outputs)
                elif async_set:
                    if protocol.lower() == "grpc":
                        triton_client.async_infer(
                            model_name,
                            inputs,
                            partial(completion_callback, user_data),
                            request_id=str(sent_count),
                            model_version=model_version,
                            outputs=outputs)
                    else:
                        async_requests.append(
                            triton_client.async_infer(
                                model_name,
                                inputs,
                                request_id=str(sent_count),
                                model_version=model_version,
                                outputs=outputs))
                else:
                    responses.append(
                        triton_client.infer(model_name,
                                            inputs,
                                            request_id=str(sent_count),
                                            model_version=model_version,
                                            outputs=outputs))

        except InferenceServerException as e:
            logger.error("inference failed: " + str(e))
            if streaming:
                triton_client.stop_stream()
            sys.exit(1)

    if streaming:
        triton_client.stop_stream()

    if protocol.lower() == "grpc":
        if streaming or async_set:
            processed_count = 0
            while processed_count < sent_count:
                (results, error) = user_data._completed_requests.get()
                processed_count += 1
                if error is not None:
                    logger.error("inference failed: " + str(error))
                    sys.exit(1)
                responses.append(results)
    else:
        if async_set:
            for async_request in async_requests:
                responses.append(async_request.get_result())

    all_results = []
    for response in responses:
        if protocol.lower() == "grpc":
            this_id = response.get_response().id
        else:
            this_id = response.get_response()["id"]
        logger.debug("Request {}, batch size {}".format(this_id, batch_size))
        all_results.append(postprocess(response, output_name, batch_size, max_batch_size > 0))

    logger.debug("PASS")
    return all_results







def parse_arguments():
    parser = argparse.ArgumentParser(description='Triton Client Inference')
    parser.add_argument('-v',
                        '--verbose',
                        action="store_true",
                        required=False,
                        default=False,
                        help='Enable verbose output')
    parser.add_argument('-a',
                        '--async',
                        dest="async_set",
                        action="store_true",
                        required=False,
                        default=False,
                        help='Use asynchronous inference API')
    parser.add_argument('--streaming',
                        action="store_true",
                        required=False,
                        default=False,
                        help='Use streaming inference API. ' +
                        'The flag is only available with gRPC protocol.')
    parser.add_argument('-m',
                        '--model-name',
                        type=str,
                        required=True,
                        help='Name of model')
    parser.add_argument('-x',
                        '--model-version',
                        type=str,
                        required=False,
                        default="",
                        help='Version of model. Default is to use latest version.')
    parser.add_argument('-b',
                        '--batch-size',
                        type=int,
                        required=False,
                        default=1,
                        help='Batch size. Default is 1.')
    parser.add_argument('-c',
                        '--classes',
                        type=int,
                        required=False,
                        default=1,
                        help='Number of class results to report. Default is 1.')
    parser.add_argument('-s',
                        '--scaling',
                        type=str,
                        choices=['NONE', 'INCEPTION', 'VGG'],
                        required=False,
                        default='NONE',
                        help='Type of scaling to apply to image pixels. Default is NONE.')
    parser.add_argument('-u',
                        '--url',
                        type=str,
                        required=False,
                        default='localhost:8000',
                        help='Inference server URL. Default is localhost:8000.')
    parser.add_argument('-i',
                        '--protocol',
                        type=str,
                        required=False,
                        default='HTTP',
                        help='Protocol (HTTP/gRPC) used to communicate with ' +
                        'the inference service. Default is HTTP.')
    parser.add_argument('image_filename',
                        type=str,
                        nargs='+',  # Allow multiple image filenames
                        help='Input image / Input folder.')
    
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    inference(
        image_sources=args.image_filename,
        model_name=args.model_name,
        model_version=args.model_version,
        batch_size=args.batch_size,
        classes=args.classes,
        scaling=args.scaling,
        url=args.url,
        protocol=args.protocol,
        verbose=args.verbose,
        async_set=args.async_set,
        streaming=args.streaming
    )
