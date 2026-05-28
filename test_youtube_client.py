"""
Unit tests for the YouTubeClient class.
Uses mocking to avoid actual API calls.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from youtube_client import YouTubeClient


class TestYouTubeClient(unittest.TestCase):
    """Test cases for YouTubeClient."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'YOUTUBE_CLIENT_ID': 'test_client_id',
            'YOUTUBE_CLIENT_SECRET': 'test_client_secret',
            'YOUTUBE_REFRESH_TOKEN': 'test_refresh_token',
            'YOUTUBE_API_SERVICE_NAME': 'youtube',
            'YOUTUBE_API_VERSION': 'v3'
        })
        self.env_patcher.start()

    def tearDown(self):
        """Clean up after tests."""
        self.env_patcher.stop()

    @patch('youtube_client.build')
    @patch('youtube_client.Request')
    @patch('youtube_client.Credentials')
    def test_authenticate_success(self, mock_credentials_class, mock_request, mock_build):
        """Test successful authentication."""
        # Setup mocks
        mock_creds = MagicMock()
        mock_creds.expired = False
        mock_credentials_class.return_value = mock_creds
        mock_build.return_value = MagicMock()

        # Create client
        client = YouTubeClient()

        # Verify credentials were created correctly
        mock_credentials_class.assert_called_once_with(
            token=None,
            refresh_token='test_refresh_token',
            token_uri='https://oauth2.googleapis.com/token',
            client_id='test_client_id',
            client_secret='test_client_secret',
            scopes=[
                'https://www.googleapis.com/auth/youtube',
                'https://www.googleapis.com/auth/youtube.readonly'
            ]
        )

        # Verify token refresh was called
        mock_creds.refresh.assert_called_once()

        # Verify YouTube API was built
        mock_build.assert_called_once_with(
            'youtube',
            'v3',
            credentials=mock_creds,
            cache_discovery=False
        )

        self.assertIsNotNone(client._youtube)

    def test_authenticate_missing_credentials(self):
        """Test authentication fails with missing credentials."""
        # Clear environment
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                YouTubeClient()

        self.assertIn('Missing YouTube API credentials', str(context.exception))

    @patch('youtube_client.build')
    @patch('youtube_client.Request')
    @patch('youtube_client.Credentials')
    def test_list_playlists(self, mock_credentials_class, mock_request, mock_build):
        """Test listing playlists."""
        # Setup mocks
        mock_creds = MagicMock()
        mock_creds.expired = False
        mock_credentials_class.return_value = mock_creds

        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube

        # Mock playlist response
        mock_response = {
            'items': [
                {
                    'id': 'PL123',
                    'snippet': {
                        'title': 'Test Playlist',
                        'description': 'Test Description',
                        'publishedAt': '2024-01-01T00:00:00Z',
                        'channelId': 'UC123',
                        'channelTitle': 'Test Channel',
                        'status': {'privacyStatus': 'public'}
                    },
                    'contentDetails': {'itemCount': 10}
                }
            ],
            'nextPageToken': None
        }

        mock_playlists = MagicMock()
        mock_playlists.list.return_value.execute.return_value = mock_response
        mock_youtube.playlists.return_value = mock_playlists

        # Create client and test
        client = YouTubeClient()
        playlists = client.list_playlists()

        # Verify results
        self.assertEqual(len(playlists), 1)
        self.assertEqual(playlists[0]['id'], 'PL123')
        self.assertEqual(playlists[0]['title'], 'Test Playlist')
        self.assertEqual(playlists[0]['item_count'], 10)

    @patch('youtube_client.build')
    @patch('youtube_client.Request')
    @patch('youtube_client.Credentials')
    def test_create_playlist(self, mock_credentials_class, mock_request, mock_build):
        """Test creating a playlist."""
        # Setup mocks
        mock_creds = MagicMock()
        mock_creds.expired = False
        mock_credentials_class.return_value = mock_creds

        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube

        # Mock create response
        mock_response = {
            'id': 'PL456',
            'snippet': {
                'title': 'New Playlist',
                'description': 'New Description'
            },
            'status': {'privacyStatus': 'private'}
        }

        mock_playlists = MagicMock()
        mock_playlists.insert.return_value.execute.return_value = mock_response
        mock_youtube.playlists.return_value = mock_playlists

        # Create client and test
        client = YouTubeClient()
        result = client.create_playlist('New Playlist', 'New Description')

        # Verify results
        self.assertEqual(result['id'], 'PL456')
        self.assertEqual(result['title'], 'New Playlist')
        self.assertEqual(result['privacy_status'], 'private')

    @patch('youtube_client.build')
    @patch('youtube_client.Request')
    @patch('youtube_client.Credentials')
    def test_get_playlist_videos(self, mock_credentials_class, mock_request, mock_build):
        """Test getting playlist videos."""
        # Setup mocks
        mock_creds = MagicMock()
        mock_creds.expired = False
        mock_credentials_class.return_value = mock_creds

        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube

        # Mock videos response
        mock_response = {
            'items': [
                {
                    'id': 'PLI789',
                    'snippet': {
                        'title': 'Test Video',
                        'description': 'Video Description',
                        'position': 0,
                        'publishedAt': '2024-01-01T00:00:00Z',
                        'resourceId': {'videoId': 'ABC123'},
                        'videoOwnerChannelId': 'UC789',
                        'videoOwnerChannelTitle': 'Video Channel',
                        'thumbnails': {'default': {'url': 'http://example.com/thumb.jpg'}}
                    }
                }
            ],
            'nextPageToken': None
        }

        mock_playlist_items = MagicMock()
        mock_playlist_items.list.return_value.execute.return_value = mock_response
        mock_youtube.playlistItems.return_value = mock_playlist_items

        # Create client and test
        client = YouTubeClient()
        videos = client.get_playlist_videos('PL123')

        # Verify results
        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0]['video_id'], 'ABC123')
        self.assertEqual(videos[0]['title'], 'Test Video')
        self.assertEqual(videos[0]['position'], 0)

    @patch('youtube_client.build')
    @patch('youtube_client.Request')
    @patch('youtube_client.Credentials')
    def test_add_video_to_playlist(self, mock_credentials_class, mock_request, mock_build):
        """Test adding video to playlist."""
        # Setup mocks
        mock_creds = MagicMock()
        mock_creds.expired = False
        mock_credentials_class.return_value = mock_creds

        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube

        # Mock insert response
        mock_response = {
            'id': 'PLI999',
            'snippet': {
                'playlistId': 'PL123',
                'position': 5,
                'resourceId': {'videoId': 'XYZ789'}
            }
        }

        mock_playlist_items = MagicMock()
        mock_playlist_items.insert.return_value.execute.return_value = mock_response
        mock_youtube.playlistItems.return_value = mock_playlist_items

        # Create client and test
        client = YouTubeClient()
        result = client.add_video_to_playlist('PL123', 'XYZ789', position=5)

        # Verify results
        self.assertEqual(result['playlist_item_id'], 'PLI999')
        self.assertEqual(result['position'], 5)

    @patch('youtube_client.build')
    @patch('youtube_client.Request')
    @patch('youtube_client.Credentials')
    def test_remove_video_from_playlist(self, mock_credentials_class, mock_request, mock_build):
        """Test removing video from playlist."""
        # Setup mocks
        mock_creds = MagicMock()
        mock_creds.expired = False
        mock_credentials_class.return_value = mock_creds

        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube

        mock_playlist_items = MagicMock()
        mock_youtube.playlistItems.return_value = mock_playlist_items

        # Create client and test
        client = YouTubeClient()
        result = client.remove_video_from_playlist('PLI999')

        # Verify the delete was called
        mock_playlist_items.delete.assert_called_once_with(id='PLI999')
        self.assertTrue(result)

    @patch('youtube_client.build')
    @patch('youtube_client.Request')
    @patch('youtube_client.Credentials')
    def test_move_video_between_playlists(self, mock_credentials_class, mock_request, mock_build):
        """Test moving video between playlists."""
        # Setup mocks
        mock_creds = MagicMock()
        mock_creds.expired = False
        mock_credentials_class.return_value = mock_creds

        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube

        # Mock responses for add and remove
        mock_add_response = {
            'id': 'PLI_NEW',
            'snippet': {'position': 3}
        }

        mock_playlist_items = MagicMock()
        mock_playlist_items.insert.return_value.execute.return_value = mock_add_response
        mock_youtube.playlistItems.return_value = mock_playlist_items

        # Create client and test
        client = YouTubeClient()
        result = client.move_video_between_playlists(
            source_playlist_id='PL_SOURCE',
            target_playlist_id='PL_TARGET',
            video_id='VID123',
            playlist_item_id='PLI_OLD'
        )

        # Verify results
        self.assertEqual(result['video_id'], 'VID123')
        self.assertEqual(result['moved_from'], 'PL_SOURCE')
        self.assertEqual(result['moved_to'], 'PL_TARGET')

    @patch('youtube_client.build')
    @patch('youtube_client.Request')
    @patch('youtube_client.Credentials')
    def test_search_videos_in_playlist(self, mock_credentials_class, mock_request, mock_build):
        """Test searching videos in playlist."""
        # Setup mocks
        mock_creds = MagicMock()
        mock_creds.expired = False
        mock_credentials_class.return_value = mock_creds

        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube

        # Mock response with multiple videos
        mock_response = {
            'items': [
                {
                    'id': 'PLI1',
                    'snippet': {
                        'title': 'Python Tutorial',
                        'description': 'Learn Python',
                        'position': 0,
                        'publishedAt': '2024-01-01T00:00:00Z',
                        'resourceId': {'videoId': 'VID1'},
                        'videoOwnerChannelTitle': 'Channel1',
                        'thumbnails': {}
                    }
                },
                {
                    'id': 'PLI2',
                    'snippet': {
                        'title': 'JavaScript Guide',
                        'description': 'Learn JavaScript',
                        'position': 1,
                        'publishedAt': '2024-01-02T00:00:00Z',
                        'resourceId': {'videoId': 'VID2'},
                        'videoOwnerChannelTitle': 'Channel2',
                        'thumbnails': {}
                    }
                }
            ],
            'nextPageToken': None
        }

        mock_playlist_items = MagicMock()
        mock_playlist_items.list.return_value.execute.return_value = mock_response
        mock_youtube.playlistItems.return_value = mock_playlist_items

        # Create client and test
        client = YouTubeClient()
        results = client.search_videos_in_playlist('PL123', 'Python')

        # Verify results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Python Tutorial')

    @patch('youtube_client.build')
    @patch('youtube_client.Request')
    @patch('youtube_client.Credentials')
    def test_delete_playlist(self, mock_credentials_class, mock_request, mock_build):
        """Test deleting a playlist."""
        # Setup mocks
        mock_creds = MagicMock()
        mock_creds.expired = False
        mock_credentials_class.return_value = mock_creds

        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube

        mock_playlists = MagicMock()
        mock_youtube.playlists.return_value = mock_playlists

        # Create client and test
        client = YouTubeClient()
        result = client.delete_playlist('PL_DELETE')

        # Verify the delete was called
        mock_playlists.delete.assert_called_once_with(id='PL_DELETE')
        self.assertTrue(result)


class TestYouTubeClientEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.env_patcher = patch.dict(os.environ, {
            'YOUTUBE_CLIENT_ID': 'test_client_id',
            'YOUTUBE_CLIENT_SECRET': 'test_client_secret',
            'YOUTUBE_REFRESH_TOKEN': 'test_refresh_token',
            'YOUTUBE_API_SERVICE_NAME': 'youtube',
            'YOUTUBE_API_VERSION': 'v3'
        })
        self.env_patcher.start()

    def tearDown(self):
        """Clean up after tests."""
        self.env_patcher.stop()

    @patch('youtube_client.build')
    @patch('youtube_client.Request')
    @patch('youtube_client.Credentials')
    def test_list_playlists_empty(self, mock_credentials_class, mock_request, mock_build):
        """Test listing playlists when there are none."""
        mock_creds = MagicMock()
        mock_creds.expired = False
        mock_credentials_class.return_value = mock_creds

        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube

        # Mock empty response
        mock_response = {'items': [], 'nextPageToken': None}
        mock_playlists = MagicMock()
        mock_playlists.list.return_value.execute.return_value = mock_response
        mock_youtube.playlists.return_value = mock_playlists

        client = YouTubeClient()
        playlists = client.list_playlists()

        self.assertEqual(len(playlists), 0)

    @patch('youtube_client.build')
    @patch('youtube_client.Request')
    @patch('youtube_client.Credentials')
    def test_list_playlists_pagination(self, mock_credentials_class, mock_request, mock_build):
        """Test playlist pagination."""
        mock_creds = MagicMock()
        mock_creds.expired = False
        mock_credentials_class.return_value = mock_creds

        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube

        # Mock paginated responses
        mock_response_1 = {
            'items': [{'id': 'PL1', 'snippet': {'title': 'P1', 'channelId': 'C1', 'channelTitle': 'CT1', 'publishedAt': '2024-01-01T00:00:00Z', 'status': {'privacyStatus': 'public'}}, 'contentDetails': {'itemCount': 1}}],
            'nextPageToken': 'TOKEN1'
        }
        mock_response_2 = {
            'items': [{'id': 'PL2', 'snippet': {'title': 'P2', 'channelId': 'C2', 'channelTitle': 'CT2', 'publishedAt': '2024-01-02T00:00:00Z', 'status': {'privacyStatus': 'private'}}, 'contentDetails': {'itemCount': 2}}],
            'nextPageToken': None
        }

        mock_playlists = MagicMock()
        mock_playlists.list.return_value.execute.side_effect = [mock_response_1, mock_response_2]
        mock_youtube.playlists.return_value = mock_playlists

        client = YouTubeClient()
        playlists = client.list_playlists(max_results=100)

        self.assertEqual(len(playlists), 2)

    @patch('youtube_client.build')
    @patch('youtube_client.Request')
    @patch('youtube_client.Credentials')
    def test_batch_reorganize_partial_failure(self, mock_credentials_class, mock_request, mock_build):
        """Test batch reorganize with some failures."""
        mock_creds = MagicMock()
        mock_creds.expired = False
        mock_credentials_class.return_value = mock_creds

        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube

        # First call succeeds, second fails
        mock_playlist_items = MagicMock()
        mock_playlist_items.insert.return_value.execute.side_effect = [
            {'id': 'PLI_NEW1', 'snippet': {'position': 0}},
            Exception('API Error')
        ]
        mock_youtube.playlistItems.return_value = mock_playlist_items

        client = YouTubeClient()
        operations = [
            {'source_playlist_id': 'PL1', 'target_playlist_id': 'PL2', 'video_id': 'VID1', 'playlist_item_id': 'PLI1'},
            {'source_playlist_id': 'PL3', 'target_playlist_id': 'PL4', 'video_id': 'VID2', 'playlist_item_id': 'PLI2'}
        ]

        results = client.batch_reorganize(operations)

        self.assertEqual(len(results), 2)
        self.assertTrue(results[0]['success'])
        self.assertFalse(results[1]['success'])


if __name__ == '__main__':
    unittest.main()
