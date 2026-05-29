#!/usr/bin/env python3
"""
YouTube Playlist Manipulation MCP Server

A Model Context Protocol server that exposes YouTube Data API operations
for playlist reorganization and management.
"""
import json
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
)

from youtube_client import YouTubeClient

app = Server("youtube-playlist-server")
youtube_client: YouTubeClient | None = None


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available YouTube playlist manipulation tools."""
    return [
        Tool(
            name="list_playlists",
            description="Get all YouTube playlists for the authenticated user with their metadata (title, ID, item count, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of playlists to return (default: 50)",
                        "default": 50
                    }
                }
            }
        ),
        Tool(
            name="get_playlist_videos",
            description="Fetch all videos in a specific playlist with their metadata including video ID, title, description, position, and URLs",
            inputSchema={
                "type": "object",
                "properties": {
                    "playlist_id": {
                        "type": "string",
                        "description": "YouTube playlist ID (starts with 'PL')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of videos to return (default: 50)",
                        "default": 50
                    }
                },
                "required": ["playlist_id"]
            }
        ),
        Tool(
            name="create_playlist",
            description="Create a new YouTube playlist with the specified title and optional description. Requires confirmed=true or will return a dry-run summary instead of executing.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title for the new playlist"
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description for the playlist",
                        "default": ""
                    },
                    "privacy_status": {
                        "type": "string",
                        "enum": ["private", "unlisted", "public"],
                        "description": "Privacy setting for the playlist",
                        "default": "private"
                    },
                    "confirmed": {
                        "type": "boolean",
                        "description": "Must be true to execute. If false or omitted, returns a dry-run summary without making any changes.",
                        "default": False
                    }
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="delete_playlist",
            description="Delete a YouTube playlist permanently. This cannot be undone! Requires confirmed=true or will return a dry-run summary instead of executing.",
            inputSchema={
                "type": "object",
                "properties": {
                    "playlist_id": {
                        "type": "string",
                        "description": "YouTube playlist ID to delete"
                    },
                    "confirmed": {
                        "type": "boolean",
                        "description": "Must be true to execute. If false or omitted, returns a dry-run summary without making any changes.",
                        "default": False
                    }
                },
                "required": ["playlist_id"]
            }
        ),
        Tool(
            name="add_video_to_playlist",
            description="Add a video to a playlist by its video ID. Requires confirmed=true or will return a dry-run summary instead of executing.",
            inputSchema={
                "type": "object",
                "properties": {
                    "playlist_id": {
                        "type": "string",
                        "description": "Target playlist ID"
                    },
                    "video_id": {
                        "type": "string",
                        "description": "YouTube video ID (11 characters, e.g., 'dQw4w9WgXcQ')"
                    },
                    "position": {
                        "type": "integer",
                        "description": "Optional position to insert the video (0-indexed). If not specified, adds to end.",
                    },
                    "confirmed": {
                        "type": "boolean",
                        "description": "Must be true to execute. If false or omitted, returns a dry-run summary without making any changes.",
                        "default": False
                    }
                },
                "required": ["playlist_id", "video_id"]
            }
        ),
        Tool(
            name="remove_video_from_playlist",
            description="Remove a video from a playlist using its playlist item ID (not video ID). Use get_playlist_videos to find the playlist_item_id. Requires confirmed=true or will return a dry-run summary instead of executing.",
            inputSchema={
                "type": "object",
                "properties": {
                    "playlist_item_id": {
                        "type": "string",
                        "description": "The playlist item ID (unique identifier for this video in this specific playlist)"
                    },
                    "confirmed": {
                        "type": "boolean",
                        "description": "Must be true to execute. If false or omitted, returns a dry-run summary without making any changes.",
                        "default": False
                    }
                },
                "required": ["playlist_item_id"]
            }
        ),
        Tool(
            name="move_video_between_playlists",
            description="Move a video from one playlist to another atomically (removes from source, adds to target). Requires confirmed=true or will return a dry-run summary instead of executing.",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_playlist_id": {
                        "type": "string",
                        "description": "Playlist ID to move the video from"
                    },
                    "target_playlist_id": {
                        "type": "string",
                        "description": "Playlist ID to move the video to"
                    },
                    "video_id": {
                        "type": "string",
                        "description": "YouTube video ID to move"
                    },
                    "playlist_item_id": {
                        "type": "string",
                        "description": "The playlist item ID from the source playlist (required for removal)"
                    },
                    "confirmed": {
                        "type": "boolean",
                        "description": "Must be true to execute. If false or omitted, returns a dry-run summary without making any changes.",
                        "default": False
                    }
                },
                "required": ["source_playlist_id", "target_playlist_id", "video_id", "playlist_item_id"]
            }
        ),
        Tool(
            name="search_videos_in_playlist",
            description="Search for videos within a playlist by keyword matching in title or description",
            inputSchema={
                "type": "object",
                "properties": {
                    "playlist_id": {
                        "type": "string",
                        "description": "Playlist ID to search within"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query to match against video titles and descriptions"
                    }
                },
                "required": ["playlist_id", "query"]
            }
        ),
        Tool(
            name="batch_reorganize",
            description="Perform multiple video move operations in a single call. Useful for bulk reorganizations. Requires confirmed=true or will return a dry-run summary instead of executing.",
            inputSchema={
                "type": "object",
                "properties": {
                    "operations": {
                        "type": "array",
                        "description": "List of move operations to perform",
                        "items": {
                            "type": "object",
                            "properties": {
                                "source_playlist_id": {"type": "string"},
                                "target_playlist_id": {"type": "string"},
                                "video_id": {"type": "string"},
                                "playlist_item_id": {"type": "string"}
                            },
                            "required": ["source_playlist_id", "target_playlist_id", "video_id", "playlist_item_id"]
                        }
                    },
                    "confirmed": {
                        "type": "boolean",
                        "description": "Must be true to execute. If false or omitted, returns a dry-run summary without making any changes.",
                        "default": False
                    }
                },
                "required": ["operations"]
            }
        ),
        Tool(
            name="infer_playlist_categories",
            description="Analyze video titles and descriptions in a playlist to suggest optimal categorization and reorganization patterns based on common keywords and themes",
            inputSchema={
                "type": "object",
                "properties": {
                    "playlist_id": {
                        "type": "string",
                        "description": "Playlist ID to analyze"
                    }
                },
                "required": ["playlist_id"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute the requested tool."""
    global youtube_client

    if youtube_client is None:
        try:
            youtube_client = YouTubeClient()
        except ValueError as e:
            return [TextContent(
                type="text",
                text=f"Authentication Error: {str(e)}\n\nPlease run 'python auth_setup.py' to set up YouTube API credentials."
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Failed to initialize YouTube client: {str(e)}"
            )]

    try:
        if name == "list_playlists":
            playlists = youtube_client.list_playlists(
                max_results=arguments.get("max_results", 50)
            )
            return [TextContent(
                type="text",
                text=json.dumps({
                    "playlist_count": len(playlists),
                    "playlists": playlists
                }, indent=2)
            )]

        elif name == "get_playlist_videos":
            videos = youtube_client.get_playlist_videos(
                playlist_id=arguments["playlist_id"],
                max_results=arguments.get("max_results", 50)
            )
            return [TextContent(
                type="text",
                text=json.dumps({
                    "playlist_id": arguments["playlist_id"],
                    "video_count": len(videos),
                    "videos": videos
                }, indent=2)
            )]

        elif name == "create_playlist":
            if not arguments.get("confirmed", False):
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "confirmed": False,
                        "action": "create_playlist",
                        "dry_run": True,
                        "would_create": {
                            "title": arguments["title"],
                            "description": arguments.get("description", ""),
                            "privacy_status": arguments.get("privacy_status", "private")
                        },
                        "message": "Dry run only. Re-call with confirmed=true to create this playlist."
                    }, indent=2)
                )]
            result = youtube_client.create_playlist(
                title=arguments["title"],
                description=arguments.get("description", ""),
                privacy_status=arguments.get("privacy_status", "private")
            )
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "playlist": result
                }, indent=2)
            )]

        elif name == "delete_playlist":
            if not arguments.get("confirmed", False):
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "confirmed": False,
                        "action": "delete_playlist",
                        "dry_run": True,
                        "would_delete": {
                            "playlist_id": arguments["playlist_id"]
                        },
                        "message": "Dry run only. Re-call with confirmed=true to permanently delete this playlist. This cannot be undone!"
                    }, indent=2)
                )]
            success = youtube_client.delete_playlist(arguments["playlist_id"])
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": success,
                    "message": f"Playlist {arguments['playlist_id']} deleted successfully"
                }, indent=2)
            )]

        elif name == "add_video_to_playlist":
            if not arguments.get("confirmed", False):
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "confirmed": False,
                        "action": "add_video_to_playlist",
                        "dry_run": True,
                        "would_add": {
                            "playlist_id": arguments["playlist_id"],
                            "video_id": arguments["video_id"],
                            "position": arguments.get("position", "end")
                        },
                        "message": "Dry run only. Re-call with confirmed=true to add the video."
                    }, indent=2)
                )]
            result = youtube_client.add_video_to_playlist(
                playlist_id=arguments["playlist_id"],
                video_id=arguments["video_id"],
                position=arguments.get("position")
            )
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "result": result
                }, indent=2)
            )]

        elif name == "remove_video_from_playlist":
            if not arguments.get("confirmed", False):
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "confirmed": False,
                        "action": "remove_video_from_playlist",
                        "dry_run": True,
                        "would_remove": {
                            "playlist_item_id": arguments["playlist_item_id"]
                        },
                        "message": "Dry run only. Re-call with confirmed=true to remove the video."
                    }, indent=2)
                )]
            success = youtube_client.remove_video_from_playlist(
                arguments["playlist_item_id"]
            )
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": success,
                    "message": f"Video removed successfully"
                }, indent=2)
            )]

        elif name == "move_video_between_playlists":
            if not arguments.get("confirmed", False):
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "confirmed": False,
                        "action": "move_video_between_playlists",
                        "dry_run": True,
                        "would_move": {
                            "video_id": arguments["video_id"],
                            "playlist_item_id": arguments["playlist_item_id"],
                            "source_playlist_id": arguments["source_playlist_id"],
                            "target_playlist_id": arguments["target_playlist_id"]
                        },
                        "message": "Dry run only. Re-call with confirmed=true to move the video."
                    }, indent=2)
                )]
            result = youtube_client.move_video_between_playlists(
                source_playlist_id=arguments["source_playlist_id"],
                target_playlist_id=arguments["target_playlist_id"],
                video_id=arguments["video_id"],
                playlist_item_id=arguments["playlist_item_id"]
            )
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "result": result
                }, indent=2)
            )]

        elif name == "search_videos_in_playlist":
            videos = youtube_client.search_videos_in_playlist(
                playlist_id=arguments["playlist_id"],
                query=arguments["query"]
            )
            return [TextContent(
                type="text",
                text=json.dumps({
                    "playlist_id": arguments["playlist_id"],
                    "query": arguments["query"],
                    "match_count": len(videos),
                    "matching_videos": videos
                }, indent=2)
            )]

        elif name == "batch_reorganize":
            if not arguments.get("confirmed", False):
                ops = arguments["operations"]
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "confirmed": False,
                        "action": "batch_reorganize",
                        "dry_run": True,
                        "total_operations": len(ops),
                        "would_move": ops,
                        "message": f"Dry run only. {len(ops)} move operation(s) pending. Re-call with confirmed=true to execute."
                    }, indent=2)
                )]
            results = youtube_client.batch_reorganize(arguments["operations"])
            successful = sum(1 for r in results if r["success"])
            failed = len(results) - successful

            return [TextContent(
                type="text",
                text=json.dumps({
                    "total_operations": len(results),
                    "successful": successful,
                    "failed": failed,
                    "results": results
                }, indent=2)
            )]

        elif name == "infer_playlist_categories":
            analysis = youtube_client.infer_playlist_categories(
                arguments["playlist_id"]
            )
            return [TextContent(
                type="text",
                text=json.dumps(analysis, indent=2)
            )]

        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]


async def main():
    """Run the MCP server using stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
