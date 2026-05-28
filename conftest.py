"""
Pytest configuration and shared fixtures for YouTube MCP Server tests.
"""
import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Automatically mock environment variables for all tests."""
    with patch.dict('os.environ', {
        'YOUTUBE_CLIENT_ID': 'test_client_id',
        'YOUTUBE_CLIENT_SECRET': 'test_client_secret',
        'YOUTUBE_REFRESH_TOKEN': 'test_refresh_token',
        'YOUTUBE_API_SERVICE_NAME': 'youtube',
        'YOUTUBE_API_VERSION': 'v3'
    }, clear=False):
        yield


@pytest.fixture
def reset_server_client():
    """Reset the server youtube_client before and after each test."""
    import server as server_module
    original_client = server_module.youtube_client
    server_module.youtube_client = None
    yield
    server_module.youtube_client = original_client
