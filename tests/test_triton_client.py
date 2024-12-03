# Just playing around with unit tests for the Triton client

import unittest
from unittest.mock import patch, MagicMock
from PIL import Image
import numpy as np
import os, sys


current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sibling_folder_path = os.path.join(parent_dir, 'LoudController')
sys.path.append(sibling_folder_path)

import triton_client

class TestTritonClient(unittest.TestCase):

    def setUp(self):
        # Set up any necessary test data or configurations
        self.image_path = 'data/images/brown_bear.jpg'
        self.mock_args = [
            '--model-name', 'inception_graphdef',
            '--model-version', '1',
            '--batch-size', '1',
            '--classes', '1',
            '--scaling', 'INCEPTION',
            '--url', 'localhost:8000',
            '--protocol', 'HTTP',
            self.image_path
        ]

    @patch('triton_client.grpcclient.InferenceServerClient')
    @patch('triton_client.httpclient.InferenceServerClient')
    def test_inference_http(self, mock_http_client, mock_grpc_client):
        # Mock the HTTP client
        mock_http_client.return_value.get_model_metadata.return_value = MagicMock()
        mock_http_client.return_value.get_model_config.return_value = MagicMock()
        mock_http_client.return_value.infer.return_value = MagicMock()

        # Run inference
        result = triton_client.inference(self.mock_args)

        # Assert that the HTTP client methods were called
        mock_http_client.return_value.get_model_metadata.assert_called_once()
        mock_http_client.return_value.get_model_config.assert_called_once()
        mock_http_client.return_value.infer.assert_called_once()

    @patch('triton_client.grpcclient.InferenceServerClient')
    @patch('triton_client.httpclient.InferenceServerClient')
    def test_inference_grpc(self, mock_http_client, mock_grpc_client):
        # Modify args to use gRPC protocol
        grpc_args = self.mock_args.copy()
        grpc_args[grpc_args.index('--protocol') + 1] = 'gRPC'

        # Mock the gRPC client
        mock_grpc_client.return_value.get_model_metadata.return_value = MagicMock()
        mock_grpc_client.return_value.get_model_config.return_value = MagicMock()
        mock_grpc_client.return_value.infer.return_value = MagicMock()

        # Run inference
        result = triton_client.inference(grpc_args)

        # Assert that the gRPC client methods were called
        mock_grpc_client.return_value.get_model_metadata.assert_called_once()
        mock_grpc_client.return_value.get_model_config.assert_called_once()
        mock_grpc_client.return_value.infer.assert_called_once()

    def test_preprocess(self):
        # Test the preprocess function
        img = Image.open(self.image_path)
        processed_image = triton_client.preprocess(
            img, 'FORMAT_NCHW', np.float32, 3, 299, 299, 'INCEPTION', 'HTTP'
        )

        # Assert the shape and type of the processed image
        self.assertEqual(processed_image.shape, (3, 299, 299))
        self.assertEqual(processed_image.dtype, np.float32)

    def test_postprocess(self):
        # Mock a result
        mock_results = MagicMock()
        mock_results.as_numpy.return_value = np.array([["0:bear", "1.0"]])

        # Run postprocess
        with patch('builtins.print') as mocked_print:
            triton_client.postprocess(mock_results, 'output', 1, True)

            # Check if the print function was called correctly
            mocked_print.assert_any_call("    0 (bear) = 1.0")

if __name__ == '__main__':
    unittest.main()
