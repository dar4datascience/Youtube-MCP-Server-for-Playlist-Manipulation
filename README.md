# YouTube MCP Server for Playlist Manipulation

A Model Context Protocol (MCP) server that enables AI assistants to manipulate your YouTube playlists directly through the YouTube Data API v3.

## Features

- **List & browse** all your YouTube playlists
- **Create & delete** playlists
- **Move videos** between playlists (atomic operations)
- **Search videos** within playlists
- **Batch reorganize** multiple videos at once
- **Analyze content** for automatic categorization suggestions

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Google Cloud Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable **YouTube Data API v3** in the API Library
4. Go to **Credentials** → **Create Credentials** → **OAuth client ID**
5. Select **Desktop app** as the application type
6. Note the **Client ID** and **Client Secret**

### 3. Configure Environment

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your credentials
YOUTUBE_CLIENT_ID=your_client_id_here
YOUTUBE_CLIENT_SECRET=your_client_secret_here
```

### 4. Authenticate (One-time)

```bash
python auth_setup.py
```

This will open a browser window for OAuth2 authorization. After granting permission, copy the `YOUTUBE_REFRESH_TOKEN` into your `.env` file.

### 5. Configure Windsurf

Copy the MCP configuration to your Windsurf settings:

```bash
# Linux/macOS
cp windsurf_mcp.json ~/.config/windsurf/mcp.json

# Or manually add the contents of windsurf_mcp.json to your Windsurf MCP settings
```

### 6. Test the Connection

Restart Windsurf and the MCP tools should appear in your tool list. Test with:

> "Show me all my YouTube playlists"

## Available MCP Tools

| Tool | Purpose |
|------|---------|
| `list_playlists` | Get all your playlists with metadata |
| `get_playlist_videos` | List videos in a specific playlist |
| `create_playlist` | Create a new playlist |
| `delete_playlist` | Remove a playlist |
| `add_video_to_playlist` | Add a video by ID to a playlist |
| `remove_video_from_playlist` | Remove a video from a playlist |
| `move_video_between_playlists` | Move a video from one playlist to another |
| `search_videos_in_playlist` | Find videos by keyword in a playlist |
| `batch_reorganize` | Move multiple videos at once |
| `infer_playlist_categories` | Analyze playlist content for categorization suggestions |

## Example Workflows

### Reorganize a Messy Playlist

1. Use `infer_playlist_categories` to analyze a large playlist
2. Create new playlists based on suggested categories
3. Use `search_videos_in_playlist` to find videos for each category
4. Use `batch_reorganize` to move videos to their new homes

### Merge Playlists

1. Use `get_playlist_videos` on the source playlist
2. Use `batch_reorganize` to move all videos to the target playlist
3. Use `delete_playlist` on the now-empty source playlist

## Security Notes

- **Never commit** your `.env` file or `.refresh_token` file
- The refresh token grants full YouTube access — keep it secure
- API calls are subject to YouTube's quota limits (10,000 units/day)

## Troubleshooting

### "Authentication Error" when using tools
Run `python auth_setup.py` again to refresh your token.

### "Quota exceeded" errors
YouTube Data API has daily limits. Check your usage in [Google Cloud Console](https://console.cloud.google.com/).

### MCP server not appearing in Windsurf
- Verify the path in `windsurf_mcp.json` is absolute and correct
- Check Windsurf's MCP logs for connection errors
- Ensure `python` is in your PATH

## License

MIT