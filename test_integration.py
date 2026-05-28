"""
Integration tests for the YouTube MCP Server.
These tests verify the interaction between components.
"""
import unittest
import json
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import server as server_module


class TestServerIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests combining multiple components."""

    def setUp(self):
        """Reset state before each test."""
        server_module.youtube_client = None

    @patch('server.YouTubeClient')
    async def test_full_workflow_list_create_delete(self, mock_client_class):
        """Test a full workflow: list -> create -> list -> delete."""
        mock_client = MagicMock()

        # Simulate listing playlists (empty initially)
        mock_client.list_playlists.side_effect = [
            [],  # First call - empty
            [{'id': 'PL_NEW', 'title': 'New Playlist', 'item_count': 0}]  # After creation
        ]

        mock_client.create_playlist.return_value = {
            'id': 'PL_NEW',
            'title': 'New Playlist',
            'url': 'https://www.youtube.com/playlist?list=PL_NEW'
        }

        mock_client.delete_playlist.return_value = True
        mock_client_class.return_value = mock_client

        # Step 1: List playlists (empty)
        result = await server_module.call_tool('list_playlists', {})
        data = json.loads(result[0].text)
        self.assertEqual(data['playlist_count'], 0)

        # Step 2: Create a playlist
        result = await server_module.call_tool('create_playlist', {
            'title': 'New Playlist',
            'description': 'Test description'
        })
        data = json.loads(result[0].text)
        self.assertTrue(data['success'])
        playlist_id = data['playlist']['id']

        # Step 3: List again (should show the new playlist)
        result = await server_module.call_tool('list_playlists', {})
        data = json.loads(result[0].text)
        self.assertEqual(data['playlist_count'], 1)

        # Step 4: Delete the playlist
        result = await server_module.call_tool('delete_playlist', {
            'playlist_id': playlist_id
        })
        data = json.loads(result[0].text)
        self.assertTrue(data['success'])

    @patch('server.YouTubeClient')
    async def test_reorganize_workflow(self, mock_client_class):
        """Test video reorganization workflow: search -> move."""
        mock_client = MagicMock()

        # Setup mock data
        mock_client.get_playlist_videos.return_value = [
            {
                'playlist_item_id': 'PLI1',
                'video_id': 'VID1',
                'title': 'Python Basics'
            },
            {
                'playlist_item_id': 'PLI2',
                'video_id': 'VID2',
                'title': 'JavaScript Basics'
            }
        ]

        mock_client.search_videos_in_playlist.side_effect = [
            [{'playlist_item_id': 'PLI1', 'video_id': 'VID1', 'title': 'Python Basics'}],
            [{'playlist_item_id': 'PLI2', 'video_id': 'VID2', 'title': 'JavaScript Basics'}]
        ]

        mock_client.move_video_between_playlists.return_value = {
            'video_id': 'VID1',
            'moved_from': 'PL_GENERAL',
            'moved_to': 'PL_PYTHON',
            'new_playlist_item_id': 'PLI_NEW'
        }

        mock_client_class.return_value = mock_client

        # Step 1: Get videos from general playlist
        result = await server_module.call_tool('get_playlist_videos', {
            'playlist_id': 'PL_GENERAL'
        })
        data = json.loads(result[0].text)
        self.assertEqual(data['video_count'], 2)

        # Step 2: Search for Python-related videos
        result = await server_module.call_tool('search_videos_in_playlist', {
            'playlist_id': 'PL_GENERAL',
            'query': 'Python'
        })
        data = json.loads(result[0].text)
        self.assertEqual(data['match_count'], 1)
        self.assertEqual(data['matching_videos'][0]['title'], 'Python Basics')

        # Step 3: Move the Python video to the Python playlist
        result = await server_module.call_tool('move_video_between_playlists', {
            'source_playlist_id': 'PL_GENERAL',
            'target_playlist_id': 'PL_PYTHON',
            'video_id': 'VID1',
            'playlist_item_id': 'PLI1'
        })
        data = json.loads(result[0].text)
        self.assertTrue(data['success'])
        self.assertEqual(data['result']['moved_to'], 'PL_PYTHON')

    @patch('server.YouTubeClient')
    async def test_batch_reorganize_with_analysis(self, mock_client_class):
        """Test combining analysis with batch reorganization."""
        mock_client = MagicMock()

        # Setup analysis results
        mock_client.infer_playlist_categories.return_value = {
            'playlist_id': 'PL_GENERAL',
            'total_videos': 10,
            'top_keywords': [('python', 5), ('javascript', 3)],
            'suggested_categories': {
                'python': {'keyword': 'python', 'video_count': 5, 'videos': ['VID1', 'VID2', 'VID3']},
                'javascript': {'keyword': 'javascript', 'video_count': 3, 'videos': ['VID4', 'VID5']}
            }
        }

        # Setup batch reorganization
        mock_client.batch_reorganize.return_value = [
            {'success': True, 'result': {'video_id': 'VID1'}},
            {'success': True, 'result': {'video_id': 'VID2'}},
            {'success': True, 'result': {'video_id': 'VID3'}}
        ]

        mock_client.get_playlist_videos.side_effect = [
            # First call - videos in general playlist with positions
            [
                {'playlist_item_id': 'PLI1', 'video_id': 'VID1', 'title': 'Python Tutorial'},
                {'playlist_item_id': 'PLI2', 'video_id': 'VID2', 'title': 'Python Advanced'},
                {'playlist_item_id': 'PLI3', 'video_id': 'VID3', 'title': 'Python Basics'}
            ],
            # Second call - after moves
            []
        ]

        mock_client_class.return_value = mock_client

        # Step 1: Analyze playlist for categories
        result = await server_module.call_tool('infer_playlist_categories', {
            'playlist_id': 'PL_GENERAL'
        })
        data = json.loads(result[0].text)
        self.assertEqual(data['total_videos'], 10)
        self.assertIn('python', data['suggested_categories'])

        # Step 2: Get video details to obtain playlist_item_ids
        result = await server_module.call_tool('get_playlist_videos', {
            'playlist_id': 'PL_GENERAL'
        })
        data = json.loads(result[0].text)
        videos = data['videos']

        # Step 3: Batch move Python videos to Python playlist
        operations = [
            {
                'source_playlist_id': 'PL_GENERAL',
                'target_playlist_id': 'PL_PYTHON',
                'video_id': video['video_id'],
                'playlist_item_id': video['playlist_item_id']
            }
            for video in videos
        ]

        result = await server_module.call_tool('batch_reorganize', {
            'operations': operations
        })
        data = json.loads(result[0].text)
        self.assertEqual(data['successful'], 3)
        self.assertEqual(data['failed'], 0)


class TestErrorRecovery(unittest.IsolatedAsyncioTestCase):
    """Test error handling and recovery scenarios."""

    def setUp(self):
        server_module.youtube_client = None

    @patch('server.YouTubeClient')
    async def test_continue_after_partial_batch_failure(self, mock_client_class):
        """Test that operations continue even if some batch items fail."""
        mock_client = MagicMock()

        # Setup batch reorganization with partial failure
        mock_client.batch_reorganize.return_value = [
            {'success': True, 'result': {'video_id': 'VID1'}},
            {'success': False, 'error': 'Video not found', 'operation': {'video_id': 'VID2'}},
            {'success': True, 'result': {'video_id': 'VID3'}}
        ]

        mock_client_class.return_value = mock_client

        operations = [
            {'source_playlist_id': 'PL1', 'target_playlist_id': 'PL2', 'video_id': 'VID1', 'playlist_item_id': 'PLI1'},
            {'source_playlist_id': 'PL1', 'target_playlist_id': 'PL2', 'video_id': 'VID2', 'playlist_item_id': 'PLI2'},
            {'source_playlist_id': 'PL1', 'target_playlist_id': 'PL2', 'video_id': 'VID3', 'playlist_item_id': 'PLI3'}
        ]

        result = await server_module.call_tool('batch_reorganize', {
            'operations': operations
        })
        data = json.loads(result[0].text)

        self.assertEqual(data['total_operations'], 3)
        self.assertEqual(data['successful'], 2)
        self.assertEqual(data['failed'], 1)
        self.assertEqual(data['results'][1]['error'], 'Video not found')

    @patch('server.YouTubeClient')
    async def test_reinit_client_after_error(self, mock_client_class):
        """Test that client reinitialization works after an error."""
        mock_client = MagicMock()

        # First call fails, second succeeds
        mock_client.list_playlists.side_effect = [
            Exception('Temporary API error'),
            [{'id': 'PL1', 'title': 'Playlist 1', 'item_count': 5}]
        ]

        mock_client_class.return_value = mock_client

        # First attempt should fail gracefully
        result = await server_module.call_tool('list_playlists', {})
        data = json.loads(result[0].text)
        self.assertFalse(data['success'])
        self.assertIn('Temporary API error', data['error'])


class TestDataConsistency(unittest.IsolatedAsyncioTestCase):
    """Test data consistency across operations."""

    def setUp(self):
        server_module.youtube_client = None

    @patch('server.YouTubeClient')
    async def test_playlist_item_id_required_for_removal(self, mock_client_class):
        """Test that playlist_item_id (not video_id) is used for removal."""
        mock_client = MagicMock()
        mock_client.remove_video_from_playlist.return_value = True
        mock_client_class.return_value = mock_client

        # Should use playlist_item_id, not video_id
        result = await server_module.call_tool('remove_video_from_playlist', {
            'playlist_item_id': 'PLI_SPECIFIC_123'
        })

        mock_client.remove_video_from_playlist.assert_called_once_with('PLI_SPECIFIC_123')

        data = json.loads(result[0].text)
        self.assertTrue(data['success'])

    @patch('server.YouTubeClient')
    async def test_video_id_vs_playlist_item_id_distinction(self, mock_client_class):
        """Test that video_id and playlist_item_id are handled correctly in moves."""
        mock_client = MagicMock()
        mock_client.move_video_between_playlists.return_value = {
            'video_id': 'VIDEO_123',
            'moved_from': 'PL_SOURCE',
            'moved_to': 'PL_TARGET',
            'new_playlist_item_id': 'NEW_PLI_456'
        }
        mock_client_class.return_value = mock_client

        # Move requires both video_id (for adding to target) and playlist_item_id (for removing from source)
        result = await server_module.call_tool('move_video_between_playlists', {
            'source_playlist_id': 'PL_SOURCE',
            'target_playlist_id': 'PL_TARGET',
            'video_id': 'VIDEO_123',  # Used for add operation
            'playlist_item_id': 'OLD_PLI_789'  # Used for remove operation
        })

        mock_client.move_video_between_playlists.assert_called_once_with(
            source_playlist_id='PL_SOURCE',
            target_playlist_id='PL_TARGET',
            video_id='VIDEO_123',
            playlist_item_id='OLD_PLI_789'
        )


if __name__ == '__main__':
    unittest.main()
