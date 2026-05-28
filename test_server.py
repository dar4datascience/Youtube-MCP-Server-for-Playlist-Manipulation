"""
Unit tests for the MCP server.
Tests the tool handlers and server functionality.
"""
import unittest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import server module functions
import server as server_module


class TestListTools(unittest.IsolatedAsyncioTestCase):
    """Test the list_tools handler."""

    async def test_list_tools_returns_all_tools(self):
        """Test that all 10 tools are returned."""
        tools = await server_module.list_tools()

        tool_names = [tool.name for tool in tools]
        expected_tools = [
            'list_playlists',
            'get_playlist_videos',
            'create_playlist',
            'delete_playlist',
            'add_video_to_playlist',
            'remove_video_from_playlist',
            'move_video_between_playlists',
            'search_videos_in_playlist',
            'batch_reorganize',
            'infer_playlist_categories'
        ]

        self.assertEqual(len(tools), 10)
        for tool_name in expected_tools:
            self.assertIn(tool_name, tool_names)

    async def test_tool_schemas(self):
        """Test that tools have proper JSON schemas."""
        tools = await server_module.list_tools()

        # Check required fields exist
        for tool in tools:
            self.assertIsNotNone(tool.name)
            self.assertIsNotNone(tool.description)
            self.assertIn('type', tool.inputSchema)
            self.assertEqual(tool.inputSchema['type'], 'object')

        # Check specific tool schemas
        create_playlist_tool = next(t for t in tools if t.name == 'create_playlist')
        self.assertIn('title', create_playlist_tool.inputSchema.get('properties', {}))
        self.assertIn('title', create_playlist_tool.inputSchema.get('required', []))


class TestCallTool(unittest.IsolatedAsyncioTestCase):
    """Test the call_tool handler."""

    def setUp(self):
        """Reset youtube_client before each test."""
        server_module.youtube_client = None

    @patch('server.YouTubeClient')
    async def test_call_tool_initializes_client(self, mock_client_class):
        """Test that youtube_client is initialized on first tool call."""
        mock_client = MagicMock()
        mock_client.list_playlists.return_value = []
        mock_client_class.return_value = mock_client

        await server_module.call_tool('list_playlists', {})

        mock_client_class.assert_called_once()
        self.assertIsNotNone(server_module.youtube_client)

    @patch('server.YouTubeClient')
    async def test_list_playlists_tool(self, mock_client_class):
        """Test list_playlists tool execution."""
        mock_client = MagicMock()
        mock_client.list_playlists.return_value = [
            {'id': 'PL1', 'title': 'Test Playlist', 'item_count': 5}
        ]
        mock_client_class.return_value = mock_client

        result = await server_module.call_tool('list_playlists', {'max_results': 10})

        mock_client.list_playlists.assert_called_once_with(max_results=10)
        self.assertEqual(len(result), 1)

        # Parse the JSON response
        response_data = json.loads(result[0].text)
        self.assertEqual(response_data['playlist_count'], 1)
        self.assertEqual(len(response_data['playlists']), 1)

    @patch('server.YouTubeClient')
    async def test_get_playlist_videos_tool(self, mock_client_class):
        """Test get_playlist_videos tool execution."""
        mock_client = MagicMock()
        mock_client.get_playlist_videos.return_value = [
            {'video_id': 'VID1', 'title': 'Video 1'},
            {'video_id': 'VID2', 'title': 'Video 2'}
        ]
        mock_client_class.return_value = mock_client

        result = await server_module.call_tool('get_playlist_videos', {
            'playlist_id': 'PL123',
            'max_results': 50
        })

        mock_client.get_playlist_videos.assert_called_once_with(
            playlist_id='PL123',
            max_results=50
        )

        response_data = json.loads(result[0].text)
        self.assertEqual(response_data['video_count'], 2)

    @patch('server.YouTubeClient')
    async def test_create_playlist_tool(self, mock_client_class):
        """Test create_playlist tool execution."""
        mock_client = MagicMock()
        mock_client.create_playlist.return_value = {
            'id': 'PL_NEW',
            'title': 'My New Playlist',
            'privacy_status': 'private'
        }
        mock_client_class.return_value = mock_client

        result = await server_module.call_tool('create_playlist', {
            'title': 'My New Playlist',
            'description': 'A test playlist',
            'privacy_status': 'private'
        })

        mock_client.create_playlist.assert_called_once_with(
            title='My New Playlist',
            description='A test playlist',
            privacy_status='private'
        )

        response_data = json.loads(result[0].text)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['playlist']['id'], 'PL_NEW')

    @patch('server.YouTubeClient')
    async def test_delete_playlist_tool(self, mock_client_class):
        """Test delete_playlist tool execution."""
        mock_client = MagicMock()
        mock_client.delete_playlist.return_value = True
        mock_client_class.return_value = mock_client

        result = await server_module.call_tool('delete_playlist', {
            'playlist_id': 'PL_DELETE'
        })

        mock_client.delete_playlist.assert_called_once_with('PL_DELETE')

        response_data = json.loads(result[0].text)
        self.assertTrue(response_data['success'])

    @patch('server.YouTubeClient')
    async def test_add_video_to_playlist_tool(self, mock_client_class):
        """Test add_video_to_playlist tool execution."""
        mock_client = MagicMock()
        mock_client.add_video_to_playlist.return_value = {
            'playlist_item_id': 'PLI_NEW',
            'position': 0
        }
        mock_client_class.return_value = mock_client

        result = await server_module.call_tool('add_video_to_playlist', {
            'playlist_id': 'PL123',
            'video_id': 'VID123',
            'position': 0
        })

        mock_client.add_video_to_playlist.assert_called_once_with(
            playlist_id='PL123',
            video_id='VID123',
            position=0
        )

        response_data = json.loads(result[0].text)
        self.assertTrue(response_data['success'])

    @patch('server.YouTubeClient')
    async def test_remove_video_from_playlist_tool(self, mock_client_class):
        """Test remove_video_from_playlist tool execution."""
        mock_client = MagicMock()
        mock_client.remove_video_from_playlist.return_value = True
        mock_client_class.return_value = mock_client

        result = await server_module.call_tool('remove_video_from_playlist', {
            'playlist_item_id': 'PLI_OLD'
        })

        mock_client.remove_video_from_playlist.assert_called_once_with('PLI_OLD')

        response_data = json.loads(result[0].text)
        self.assertTrue(response_data['success'])

    @patch('server.YouTubeClient')
    async def test_move_video_between_playlists_tool(self, mock_client_class):
        """Test move_video_between_playlists tool execution."""
        mock_client = MagicMock()
        mock_client.move_video_between_playlists.return_value = {
            'video_id': 'VID123',
            'moved_from': 'PL1',
            'moved_to': 'PL2'
        }
        mock_client_class.return_value = mock_client

        result = await server_module.call_tool('move_video_between_playlists', {
            'source_playlist_id': 'PL1',
            'target_playlist_id': 'PL2',
            'video_id': 'VID123',
            'playlist_item_id': 'PLI_OLD'
        })

        mock_client.move_video_between_playlists.assert_called_once_with(
            source_playlist_id='PL1',
            target_playlist_id='PL2',
            video_id='VID123',
            playlist_item_id='PLI_OLD'
        )

        response_data = json.loads(result[0].text)
        self.assertTrue(response_data['success'])

    @patch('server.YouTubeClient')
    async def test_search_videos_in_playlist_tool(self, mock_client_class):
        """Test search_videos_in_playlist tool execution."""
        mock_client = MagicMock()
        mock_client.search_videos_in_playlist.return_value = [
            {'video_id': 'VID1', 'title': 'Python Tutorial'}
        ]
        mock_client_class.return_value = mock_client

        result = await server_module.call_tool('search_videos_in_playlist', {
            'playlist_id': 'PL123',
            'query': 'Python'
        })

        mock_client.search_videos_in_playlist.assert_called_once_with(
            playlist_id='PL123',
            query='Python'
        )

        response_data = json.loads(result[0].text)
        self.assertEqual(response_data['match_count'], 1)

    @patch('server.YouTubeClient')
    async def test_batch_reorganize_tool(self, mock_client_class):
        """Test batch_reorganize tool execution."""
        mock_client = MagicMock()
        mock_client.batch_reorganize.return_value = [
            {'success': True, 'result': {'video_id': 'VID1'}},
            {'success': True, 'result': {'video_id': 'VID2'}}
        ]
        mock_client_class.return_value = mock_client

        operations = [
            {'source_playlist_id': 'PL1', 'target_playlist_id': 'PL2', 'video_id': 'VID1', 'playlist_item_id': 'PLI1'},
            {'source_playlist_id': 'PL3', 'target_playlist_id': 'PL4', 'video_id': 'VID2', 'playlist_item_id': 'PLI2'}
        ]

        result = await server_module.call_tool('batch_reorganize', {
            'operations': operations
        })

        mock_client.batch_reorganize.assert_called_once_with(operations)

        response_data = json.loads(result[0].text)
        self.assertEqual(response_data['total_operations'], 2)
        self.assertEqual(response_data['successful'], 2)

    @patch('server.YouTubeClient')
    async def test_infer_playlist_categories_tool(self, mock_client_class):
        """Test infer_playlist_categories tool execution."""
        mock_client = MagicMock()
        mock_client.infer_playlist_categories.return_value = {
            'playlist_id': 'PL123',
            'total_videos': 10,
            'top_keywords': [('python', 5), ('tutorial', 3)],
            'suggested_categories': {'python': {'keyword': 'python', 'video_count': 5}}
        }
        mock_client_class.return_value = mock_client

        result = await server_module.call_tool('infer_playlist_categories', {
            'playlist_id': 'PL123'
        })

        mock_client.infer_playlist_categories.assert_called_once_with('PL123')

        response_data = json.loads(result[0].text)
        self.assertEqual(response_data['playlist_id'], 'PL123')
        self.assertEqual(response_data['total_videos'], 10)


class TestCallToolErrors(unittest.IsolatedAsyncioTestCase):
    """Test error handling in call_tool."""

    def setUp(self):
        server_module.youtube_client = None

    @patch('server.YouTubeClient')
    async def test_authentication_error(self, mock_client_class):
        """Test handling of authentication errors."""
        mock_client_class.side_effect = ValueError('Missing YouTube API credentials')

        result = await server_module.call_tool('list_playlists', {})

        self.assertIn('Authentication Error', result[0].text)

    @patch('server.YouTubeClient')
    async def test_unknown_tool(self, mock_client_class):
        """Test handling of unknown tool names."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        result = await server_module.call_tool('unknown_tool', {})

        self.assertIn('Unknown tool', result[0].text)

    @patch('server.YouTubeClient')
    async def test_tool_execution_error(self, mock_client_class):
        """Test handling of errors during tool execution."""
        mock_client = MagicMock()
        mock_client.list_playlists.side_effect = Exception('API Quota Exceeded')
        mock_client_class.return_value = mock_client

        result = await server_module.call_tool('list_playlists', {})

        response_data = json.loads(result[0].text)
        self.assertFalse(response_data['success'])
        self.assertIn('API Quota Exceeded', response_data['error'])

    @patch('server.YouTubeClient')
    async def test_init_error_other_exception(self, mock_client_class):
        """Test handling of non-authentication init errors."""
        mock_client_class.side_effect = Exception('Network error')

        result = await server_module.call_tool('list_playlists', {})

        self.assertIn('Failed to initialize YouTube client', result[0].text)


class TestServerStructure(unittest.TestCase):
    """Test server module structure and constants."""

    def test_server_name(self):
        """Test that server has correct name."""
        self.assertEqual(server_module.app.name, 'youtube-playlist-server')

    def test_youtube_client_initially_none(self):
        """Test that youtube_client starts as None."""
        # This is important for lazy initialization
        self.assertIsNone(server_module.youtube_client)


if __name__ == '__main__':
    unittest.main()
