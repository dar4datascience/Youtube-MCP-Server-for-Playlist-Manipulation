"""
YouTube Data API client wrapper with OAuth2 authentication.
"""
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

load_dotenv()


class YouTubeClient:
    """Authenticated YouTube Data API client."""

    def __init__(self):
        self._credentials = None
        self._youtube = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate using stored refresh token."""
        refresh_token = os.getenv('YOUTUBE_REFRESH_TOKEN')
        client_id = os.getenv('YOUTUBE_CLIENT_ID')
        client_secret = os.getenv('YOUTUBE_CLIENT_SECRET')

        if not all([refresh_token, client_id, client_secret]):
            raise ValueError(
                "Missing YouTube API credentials. "
                "Set YOUTUBE_REFRESH_TOKEN, YOUTUBE_CLIENT_ID, and YOUTUBE_CLIENT_SECRET in .env. "
                "Run auth_setup.py first to obtain a refresh token."
            )

        self._credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=[
                'https://www.googleapis.com/auth/youtube',
                'https://www.googleapis.com/auth/youtube.readonly'
            ]
        )

        # Refresh the access token
        self._credentials.refresh(Request())

        self._youtube = build(
            os.getenv('YOUTUBE_API_SERVICE_NAME', 'youtube'),
            os.getenv('YOUTUBE_API_VERSION', 'v3'),
            credentials=self._credentials,
            cache_discovery=False
        )

    def _ensure_authenticated(self):
        """Ensure credentials are fresh."""
        if self._credentials.expired:
            self._credentials.refresh(Request())

    # ==================== Playlist Operations ====================

    def list_playlists(self, max_results: int = 50) -> List[Dict[str, Any]]:
        """Get all playlists for the authenticated user's channel."""
        self._ensure_authenticated()
        playlists = []
        next_page_token = None

        while True:
            request = self._youtube.playlists().list(
                part='snippet,contentDetails',
                mine=True,
                maxResults=min(max_results, 50),
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response.get('items', []):
                playlists.append({
                    'id': item['id'],
                    'title': item['snippet']['title'],
                    'description': item['snippet'].get('description', ''),
                    'item_count': item['contentDetails']['itemCount'],
                    'privacy_status': item['snippet'].get('status', {}).get('privacyStatus', 'unknown'),
                    'published_at': item['snippet']['publishedAt'],
                    'channel_id': item['snippet']['channelId'],
                    'channel_title': item['snippet']['channelTitle']
                })

            next_page_token = response.get('nextPageToken')
            if not next_page_token or len(playlists) >= max_results:
                break

        return playlists

    def create_playlist(self, title: str, description: str = "",
                        privacy_status: str = "private") -> Dict[str, Any]:
        """Create a new playlist."""
        self._ensure_authenticated()

        request = self._youtube.playlists().insert(
            part='snippet,status',
            body={
                'snippet': {
                    'title': title,
                    'description': description
                },
                'status': {
                    'privacyStatus': privacy_status
                }
            }
        )
        response = request.execute()

        return {
            'id': response['id'],
            'title': response['snippet']['title'],
            'description': response['snippet'].get('description', ''),
            'privacy_status': response['status']['privacyStatus'],
            'url': f"https://www.youtube.com/playlist?list={response['id']}"
        }

    def delete_playlist(self, playlist_id: str) -> bool:
        """Delete a playlist by ID."""
        self._ensure_authenticated()

        try:
            self._youtube.playlists().delete(id=playlist_id).execute()
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to delete playlist {playlist_id}: {e}")

    # ==================== Playlist Item Operations ====================

    def get_playlist_videos(self, playlist_id: str,
                            max_results: int = 50) -> List[Dict[str, Any]]:
        """Get all videos in a playlist with their metadata."""
        self._ensure_authenticated()
        videos = []
        next_page_token = None

        while True:
            request = self._youtube.playlistItems().list(
                part='snippet,contentDetails',
                playlistId=playlist_id,
                maxResults=min(max_results, 50),
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response.get('items', []):
                snippet = item['snippet']
                videos.append({
                    'playlist_item_id': item['id'],
                    'video_id': snippet['resourceId']['videoId'],
                    'title': snippet['title'],
                    'description': snippet.get('description', ''),
                    'position': snippet['position'],
                    'published_at': snippet['publishedAt'],
                    'channel_id': snippet.get('videoOwnerChannelId'),
                    'channel_title': snippet.get('videoOwnerChannelTitle', ''),
                    'thumbnails': snippet.get('thumbnails', {}),
                    'video_url': f"https://www.youtube.com/watch?v={snippet['resourceId']['videoId']}"
                })

            next_page_token = response.get('nextPageToken')
            if not next_page_token or len(videos) >= max_results:
                break

        return videos

    def add_video_to_playlist(self, playlist_id: str, video_id: str,
                              position: Optional[int] = None) -> Dict[str, Any]:
        """Add a video to a playlist."""
        self._ensure_authenticated()

        body = {
            'snippet': {
                'playlistId': playlist_id,
                'resourceId': {
                    'kind': 'youtube#video',
                    'videoId': video_id
                }
            }
        }

        if position is not None:
            body['snippet']['position'] = position

        request = self._youtube.playlistItems().insert(
            part='snippet',
            body=body
        )
        response = request.execute()

        return {
            'playlist_item_id': response['id'],
            'video_id': video_id,
            'playlist_id': playlist_id,
            'position': response['snippet']['position']
        }

    def remove_video_from_playlist(self, playlist_item_id: str) -> bool:
        """Remove a video from a playlist using its playlist item ID."""
        self._ensure_authenticated()

        try:
            self._youtube.playlistItems().delete(id=playlist_item_id).execute()
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to remove playlist item {playlist_item_id}: {e}")

    def move_video_between_playlists(self, source_playlist_id: str,
                                     target_playlist_id: str,
                                     video_id: str,
                                     playlist_item_id: str) -> Dict[str, Any]:
        """Atomically move a video from one playlist to another."""
        self._ensure_authenticated()

        # First, add to target playlist
        add_result = self.add_video_to_playlist(target_playlist_id, video_id)

        # Then, remove from source playlist
        self.remove_video_from_playlist(playlist_item_id)

        return {
            'video_id': video_id,
            'moved_from': source_playlist_id,
            'moved_to': target_playlist_id,
            'new_playlist_item_id': add_result['playlist_item_id'],
            'new_position': add_result['position']
        }

    def search_videos_in_playlist(self, playlist_id: str,
                                   query: str) -> List[Dict[str, Any]]:
        """Search for videos in a playlist by keyword."""
        videos = self.get_playlist_videos(playlist_id, max_results=500)
        query_lower = query.lower()

        matching_videos = []
        for video in videos:
            if (query_lower in video['title'].lower() or
                query_lower in video['description'].lower()):
                matching_videos.append(video)

        return matching_videos

    def batch_reorganize(self, operations: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Perform multiple move operations atomically.

        Each operation dict should have:
        - source_playlist_id
        - target_playlist_id
        - video_id
        - playlist_item_id
        """
        results = []
        for op in operations:
            try:
                result = self.move_video_between_playlists(
                    source_playlist_id=op['source_playlist_id'],
                    target_playlist_id=op['target_playlist_id'],
                    video_id=op['video_id'],
                    playlist_item_id=op['playlist_item_id']
                )
                results.append({'success': True, 'result': result})
            except Exception as e:
                results.append({'success': False, 'error': str(e), 'operation': op})

        return results

    def infer_playlist_categories(self, playlist_id: str) -> Dict[str, Any]:
        """Analyze video titles/descriptions to suggest categorization patterns."""
        videos = self.get_playlist_videos(playlist_id, max_results=200)

        # Extract common words from titles (excluding stop words)
        from collections import Counter
        import re

        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
            'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
            'through', 'during', 'before', 'after', 'above', 'below',
            'between', 'under', 'and', 'but', 'or', 'yet', 'so',
            'if', 'because', 'although', 'though', 'while', 'where',
            'when', 'that', 'which', 'who', 'whom', 'whose', 'what',
            'this', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
            'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my',
            'your', 'his', 'its', 'our', 'their', 'mine', 'yours',
            'hers', 'ours', 'theirs', '-', '|', ':', '...', ''
        }

        all_words = []
        for video in videos:
            title = video.get('title', '').lower()
            desc = video.get('description', '').lower()

            # Extract words (alphanumeric sequences)
            title_words = re.findall(r'\b[a-zA-Z]+\b', title)
            desc_words = re.findall(r'\b[a-zA-Z]+\b', desc)[:20]  # Limit description words

            all_words.extend([w for w in title_words if w not in stop_words and len(w) > 2])
            all_words.extend([w for w in desc_words if w not in stop_words and len(w) > 2])

        word_counts = Counter(all_words)
        top_keywords = word_counts.most_common(20)

        # Simple category suggestion based on common keywords
        suggested_categories = {}
        for word, count in top_keywords[:10]:
            matching_videos = [
                v for v in videos
                if word in v['title'].lower() or word in v['description'].lower()
            ]
            if len(matching_videos) >= 3:  # At least 3 videos match
                suggested_categories[word] = {
                    'keyword': word,
                    'video_count': len(matching_videos),
                    'videos': [v['video_id'] for v in matching_videos[:5]]  # Sample videos
                }

        return {
            'playlist_id': playlist_id,
            'total_videos': len(videos),
            'top_keywords': top_keywords,
            'suggested_categories': suggested_categories,
            'analysis_summary': f"Found {len(suggested_categories)} potential categories based on content analysis"
        }
