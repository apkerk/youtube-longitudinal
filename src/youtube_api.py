"""
youtube_api.py
--------------
Enhanced YouTube API helper functions for longitudinal data collection.

Provides:
- Authentication and service building
- Request execution with exponential backoff
- Channel data extraction (Tier 1+2 with full topic details)
- Video data extraction with Shorts classification
- New video detection for longitudinal tracking
- Activity feed extraction

Author: Katie Apker
Last Updated: Feb 02, 2026
"""

import csv
import os
import re
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

import yaml
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Import config (handle both direct run and module import)
try:
    from . import config
except ImportError:
    import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION & AUTHENTICATION
# =============================================================================

def load_config(config_path: str = 'config/config.yaml') -> Dict:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Relative path to config file from project root
        
    Returns:
        Dictionary of configuration values
    """
    base_dir = Path(__file__).parent.parent
    abs_config_path = base_dir / config_path
    
    with open(abs_config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_authenticated_service(api_key: Optional[str] = None):
    """
    Build and return the YouTube Data API service.
    
    Args:
        api_key: Optional API key (if not provided, loads from config)
        
    Returns:
        YouTube API service object
        
    Raises:
        ValueError: If API key is missing or invalid
    """
    if not api_key:
        cfg = load_config()
        api_key = cfg.get('api_key')
        
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        raise ValueError("API Key is missing or invalid in config.yaml")
        
    return build('youtube', 'v3', developerKey=api_key)


# =============================================================================
# QUOTA TRACKING
# =============================================================================

_quota_daily_total = 0
_quota_current_date = ""


def _log_quota_usage(quota_cost: int, endpoint_name: str) -> None:
    """Append quota usage to daily CSV log."""
    global _quota_daily_total, _quota_current_date

    today = datetime.utcnow().strftime("%Y%m%d")
    if today != _quota_current_date:
        _quota_daily_total = 0
        _quota_current_date = today

    _quota_daily_total += quota_cost
    log_path = Path(__file__).parent.parent / "data" / "logs" / f"quota_{today}.csv"

    try:
        write_header = not log_path.exists()
        with open(log_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(['timestamp', 'endpoint_name', 'quota_cost', 'cumulative_daily_total'])
            writer.writerow([datetime.utcnow().isoformat(), endpoint_name, quota_cost, _quota_daily_total])
    except Exception:
        pass  # Never block API operations for logging failures


# =============================================================================
# REQUEST EXECUTION WITH RETRY
# =============================================================================

def execute_request(request, max_retries: int = 5, quota_cost: int = 1, endpoint_name: str = "unknown") -> Dict:
    """
    Execute an API request with exponential backoff for rate limits.

    Args:
        request: YouTube API request object
        max_retries: Maximum number of retry attempts
        quota_cost: API quota units consumed by this request
        endpoint_name: Name of the endpoint for quota logging

    Returns:
        API response dictionary

    Raises:
        Exception: If all retries fail
    """
    retries = 0
    while retries < max_retries:
        try:
            result = request.execute()
            _log_quota_usage(quota_cost, endpoint_name)
            return result
        except HttpError as e:
            if e.resp.status in [403, 429, 500, 503]:
                sleep_time = (2 ** retries) + (time.time() % 1)
                logger.warning(f"API Error {e.resp.status}: Retrying in {sleep_time:.2f}s...")
                time.sleep(sleep_time)
                retries += 1
            else:
                raise e
    raise Exception(f"Failed after {max_retries} retries.")


def chunks(lst: List, n: int):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


# =============================================================================
# TOPIC EXTRACTION & DECODING
# =============================================================================

def extract_topics(topic_details: Dict) -> Dict[str, Any]:
    """
    Extract and decode topic information from channel topicDetails.
    
    Args:
        topic_details: The topicDetails object from channel API response
        
    Returns:
        Dictionary with decoded topic information:
        - topic_categories_raw: Full list of Wikipedia URLs
        - topic_ids: YouTube topic IDs
        - topic_1, topic_2, topic_3: Decoded top 3 topics
        - topic_count: Number of topics assigned
    """
    result = {
        'topic_categories_raw': None,
        'topic_ids': None,
        'topic_1': None,
        'topic_2': None,
        'topic_3': None,
        'topic_count': 0,
    }
    
    if not topic_details:
        return result
    
    # Extract topic categories (Wikipedia URLs)
    topic_categories = topic_details.get('topicCategories', [])
    if topic_categories:
        result['topic_categories_raw'] = '|'.join(topic_categories)
        result['topic_count'] = len(topic_categories)
        
        # Decode top 3 topics
        decoded_topics = [config.decode_topic_url(url) for url in topic_categories[:3]]
        if len(decoded_topics) >= 1:
            result['topic_1'] = decoded_topics[0]
        if len(decoded_topics) >= 2:
            result['topic_2'] = decoded_topics[1]
        if len(decoded_topics) >= 3:
            result['topic_3'] = decoded_topics[2]
    
    # Extract topic IDs (if available - deprecated but may still exist)
    topic_ids = topic_details.get('topicIds', [])
    if topic_ids:
        result['topic_ids'] = '|'.join(topic_ids)
    
    return result


# =============================================================================
# CHANNEL DATA EXTRACTION
# =============================================================================

def get_channel_full_details(
    youtube,
    channel_ids: List[str],
    stream_type: str = "unknown",
    discovery_language: str = "unknown",
    discovery_keyword: str = "unknown"
) -> List[Dict]:
    """
    Get comprehensive channel details (Tier 1+2) for a list of channel IDs.
    
    Includes all shock-relevant variables and full topic extraction.
    
    Args:
        youtube: Authenticated YouTube API service
        channel_ids: List of channel IDs to fetch
        stream_type: Stream identifier (stream_a, stream_b, etc.)
        discovery_language: Language of the discovery keyword
        discovery_keyword: The keyword that found this channel
        
    Returns:
        List of channel data dictionaries
    """
    channels_data = []
    unique_ids = list(set(channel_ids))
    
    for chunk in chunks(unique_ids, 50):
        try:
            request = youtube.channels().list(
                part=config.CHANNEL_PARTS,
                id=",".join(chunk)
            )
            response = execute_request(request)
            
            for item in response.get('items', []):
                channel = parse_channel_response(
                    item, 
                    stream_type, 
                    discovery_language, 
                    discovery_keyword
                )
                channels_data.append(channel)
                
            time.sleep(config.SLEEP_BETWEEN_CALLS)
            
        except Exception as e:
            logger.error(f"Error fetching channel details: {e}")
            
    return channels_data


def parse_channel_response(
    item: Dict,
    stream_type: str,
    discovery_language: str,
    discovery_keyword: str
) -> Dict:
    """
    Parse a single channel API response into a flat dictionary.
    
    Args:
        item: Channel item from API response
        stream_type: Stream identifier
        discovery_language: Language of discovery keyword
        discovery_keyword: The keyword that found this channel
        
    Returns:
        Flat dictionary of channel data
    """
    snippet = item.get('snippet', {})
    statistics = item.get('statistics', {})
    content_details = item.get('contentDetails', {})
    status = item.get('status', {})
    topic_details = item.get('topicDetails', {})
    branding = item.get('brandingSettings', {})
    localizations = item.get('localizations', {})
    
    # Extract topics
    topics = extract_topics(topic_details)
    
    # Extract branding keywords
    channel_branding = branding.get('channel', {})
    keywords = channel_branding.get('keywords', '')
    
    # Extract localizations
    localization_list = list(localizations.keys()) if localizations else []
    
    return {
        # Identification
        'channel_id': item.get('id'),
        'title': snippet.get('title'),
        'description': snippet.get('description', '')[:5000],  # Truncate long descriptions
        'custom_url': snippet.get('customUrl'),
        'published_at': snippet.get('publishedAt'),
        
        # Metrics
        'view_count': int(statistics.get('viewCount', 0)),
        'subscriber_count': int(statistics.get('subscriberCount', 0)),
        'video_count': int(statistics.get('videoCount', 0)),
        'hidden_subscriber_count': statistics.get('hiddenSubscriberCount', False),
        
        # Geographic & Language
        'country': snippet.get('country'),
        'default_language': snippet.get('defaultLanguage'),
        
        # Topic Categories
        'topic_categories_raw': topics['topic_categories_raw'],
        'topic_ids': topics['topic_ids'],
        'topic_1': topics['topic_1'],
        'topic_2': topics['topic_2'],
        'topic_3': topics['topic_3'],
        'topic_count': topics['topic_count'],
        
        # Policy-relevant
        'made_for_kids': status.get('madeForKids', False),
        'privacy_status': status.get('privacyStatus'),
        'long_uploads_status': status.get('longUploadsStatus'),
        'is_linked': status.get('isLinked'),
        
        # Branding
        'keywords': keywords,
        'localization_count': len(localization_list),
        'localizations_available': '|'.join(localization_list) if localization_list else None,
        'profile_picture_url': snippet.get('thumbnails', {}).get('default', {}).get('url'),
        
        # Content structure
        'uploads_playlist_id': content_details.get('relatedPlaylists', {}).get('uploads'),
        
        # Will be filled by get_oldest_video()
        'first_video_date': None,
        'first_video_id': None,
        'first_video_title': None,
        
        # Discovery metadata
        'stream_type': stream_type,
        'discovery_language': discovery_language,
        'discovery_keyword': discovery_keyword,
        'scraped_at': datetime.utcnow().isoformat(),
    }


def get_channel_stats_only(youtube, channel_ids: List[str]) -> List[Dict]:
    """
    Get only basic stats for channels (for sweeps).
    
    Args:
        youtube: Authenticated YouTube API service
        channel_ids: List of channel IDs to fetch
        
    Returns:
        List of channel stats dictionaries
    """
    channels_data = []
    unique_ids = list(set(channel_ids))
    
    for chunk in chunks(unique_ids, 50):
        try:
            request = youtube.channels().list(
                part="statistics,status",
                id=",".join(chunk)
            )
            response = execute_request(request)
            
            for item in response.get('items', []):
                stats = item.get('statistics', {})
                status = item.get('status', {})
                
                channels_data.append({
                    'channel_id': item.get('id'),
                    'view_count': int(stats.get('viewCount', 0)),
                    'subscriber_count': int(stats.get('subscriberCount', 0)),
                    'video_count': int(stats.get('videoCount', 0)),
                    'made_for_kids': status.get('madeForKids', False),
                    'status': 'active',
                    'scraped_at': datetime.utcnow().isoformat(),
                })
                
            time.sleep(config.SLEEP_BETWEEN_CALLS)
            
        except HttpError as e:
            if e.resp.status == 404:
                # Channel not found - mark as deleted
                for cid in chunk:
                    channels_data.append({
                        'channel_id': cid,
                        'view_count': None,
                        'subscriber_count': None,
                        'video_count': None,
                        'made_for_kids': None,
                        'status': 'not_found',
                        'scraped_at': datetime.utcnow().isoformat(),
                    })
            else:
                logger.error(f"Error fetching channel stats: {e}")
                
    return channels_data


# =============================================================================
# VIDEO DATA EXTRACTION
# =============================================================================

def get_video_details_batch(youtube, video_ids: List[str], trigger_type: str = "initial") -> List[Dict]:
    """
    Get full video details for a batch of video IDs.
    
    Args:
        youtube: Authenticated YouTube API service
        video_ids: List of video IDs to fetch
        trigger_type: Why this video was fetched (initial, new_video_detection)
        
    Returns:
        List of video data dictionaries
    """
    videos_data = []
    unique_ids = list(set(video_ids))
    
    for chunk in chunks(unique_ids, 50):
        try:
            request = youtube.videos().list(
                part=config.VIDEO_PARTS,
                id=",".join(chunk)
            )
            response = execute_request(request)
            
            for item in response.get('items', []):
                video = parse_video_response(item, trigger_type)
                videos_data.append(video)
                
            time.sleep(config.SLEEP_BETWEEN_CALLS)
            
        except Exception as e:
            logger.error(f"Error fetching video details: {e}")
            
    return videos_data


def get_video_stats_batch(youtube, video_ids: List[str]) -> List[Dict]:
    """
    Get only statistics for a batch of video IDs (lean daily panel fetch).

    Unlike get_video_details_batch() which requests full snippet/contentDetails/status,
    this only fetches statistics. Same API cost but less data transfer.

    Args:
        youtube: Authenticated YouTube API service
        video_ids: List of video IDs to fetch

    Returns:
        List of dicts: {video_id, view_count, like_count, comment_count, scraped_at}
    """
    stats_data = []
    unique_ids = list(set(video_ids))

    for chunk in chunks(unique_ids, 50):
        try:
            request = youtube.videos().list(
                part="statistics",
                id=",".join(chunk)
            )
            response = execute_request(request)

            for item in response.get('items', []):
                statistics = item.get('statistics', {})
                stats_data.append({
                    'video_id': item.get('id'),
                    'view_count': int(statistics.get('viewCount', 0)),
                    'like_count': int(statistics.get('likeCount', 0)),
                    'comment_count': int(statistics.get('commentCount', 0)),
                    'scraped_at': datetime.utcnow().isoformat(),
                })

            time.sleep(config.SLEEP_BETWEEN_CALLS)

        except Exception as e:
            logger.error(f"Error fetching video stats: {e}")

    return stats_data


def parse_video_response(item: Dict, trigger_type: str) -> Dict:
    """
    Parse a single video API response into a flat dictionary.

    Args:
        item: Video item from API response
        trigger_type: Why this video was fetched

    Returns:
        Flat dictionary of video data
    """
    snippet = item.get('snippet', {})
    statistics = item.get('statistics', {})
    content_details = item.get('contentDetails', {})
    status = item.get('status', {})
    
    # Parse duration to seconds
    duration_iso = content_details.get('duration', 'PT0S')
    duration_seconds = parse_duration(duration_iso)
    
    # Determine if Short
    is_short = duration_seconds <= config.SHORTS_MAX_DURATION_SECONDS
    
    # Extract hashtags from description
    description = snippet.get('description', '')
    hashtags = extract_hashtags(description)
    
    # Extract content ratings
    content_rating = content_details.get('contentRating', {})
    
    # Extract region restrictions
    region_restriction = content_details.get('regionRestriction', {})
    
    return {
        'video_id': item.get('id'),
        'channel_id': snippet.get('channelId'),
        'title': snippet.get('title'),
        'description': description[:5000],  # Truncate
        'published_at': snippet.get('publishedAt'),
        
        # Metrics
        'view_count': int(statistics.get('viewCount', 0)),
        'like_count': int(statistics.get('likeCount', 0)),
        'comment_count': int(statistics.get('commentCount', 0)),
        
        # Duration & Shorts
        'duration': duration_iso,
        'duration_seconds': duration_seconds,
        'is_short': is_short,
        
        # Classification
        'category_id': snippet.get('categoryId'),
        'category_name': config.YOUTUBE_CATEGORIES.get(
            int(snippet.get('categoryId', 0)), 'Unknown'
        ),
        
        # Tags & Hashtags
        'tags': '|'.join(snippet.get('tags', [])) if snippet.get('tags') else None,
        'hashtags': '|'.join(hashtags) if hashtags else None,
        'hashtag_count': len(hashtags),
        
        # Technical
        'definition': content_details.get('definition'),
        'dimension': content_details.get('dimension'),
        'caption': content_details.get('caption') == 'true',
        'licensed_content': content_details.get('licensedContent', False),
        
        # Policy-relevant
        'content_rating_yt': content_rating.get('ytRating'),
        'region_restriction_blocked': '|'.join(region_restriction.get('blocked', [])) if region_restriction.get('blocked') else None,
        'region_restriction_allowed': '|'.join(region_restriction.get('allowed', [])) if region_restriction.get('allowed') else None,
        
        # Metadata
        'trigger_type': trigger_type,
        'scraped_at': datetime.utcnow().isoformat(),
    }


def parse_duration(duration_iso: str) -> int:
    """
    Parse ISO 8601 duration to seconds.
    
    Args:
        duration_iso: Duration string like 'PT1H30M45S'
        
    Returns:
        Duration in seconds
    """
    if not duration_iso:
        return 0
        
    # Pattern for ISO 8601 duration
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, duration_iso)
    
    if not match:
        return 0
        
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    
    return hours * 3600 + minutes * 60 + seconds


def extract_hashtags(text: str) -> List[str]:
    """
    Extract hashtags from text.
    
    Args:
        text: Text to search for hashtags
        
    Returns:
        List of hashtags (without # symbol)
    """
    if not text:
        return []
    
    # Find all hashtags
    hashtags = re.findall(r'#(\w+)', text)
    return hashtags


# =============================================================================
# PLAYLIST & OLDEST VIDEO
# =============================================================================

def get_oldest_video(youtube, uploads_playlist_id: str) -> Optional[Dict]:
    """
    Get the oldest video from a channel's uploads playlist.
    
    Args:
        youtube: Authenticated YouTube API service
        uploads_playlist_id: The uploads playlist ID (UU... format)
        
    Returns:
        Dictionary with first_video_date, first_video_id, first_video_title
        or None if no videos found
    """
    if not uploads_playlist_id:
        return None
        
    try:
        # Get total items to know how many pages to skip
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=uploads_playlist_id,
            maxResults=1
        )
        response = execute_request(request)
        
        # Get total results
        total = response.get('pageInfo', {}).get('totalResults', 0)
        
        if total == 0:
            return None
            
        # We need to paginate to the last page to get oldest
        # This is expensive, so we'll use a binary search approach
        # For now, just get the last page by calculating pages needed
        
        # Actually, the API doesn't support reverse order, so we need to paginate
        # For efficiency, let's just get the metadata and use the channel creation date
        # as a proxy, OR accept that we'll need multiple calls for oldest video
        
        # Simple approach: paginate to last page (max 50 results per page)
        page_token = None
        oldest_video = None
        
        # Limit pagination to avoid excessive API calls
        max_pages = min(10, (total // 50) + 1)
        
        for _ in range(max_pages):
            request = youtube.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=page_token
            )
            response = execute_request(request)
            
            items = response.get('items', [])
            if items:
                # Get the last item (oldest in this page)
                last_item = items[-1]
                oldest_video = {
                    'first_video_id': last_item['snippet']['resourceId']['videoId'],
                    'first_video_title': last_item['snippet']['title'],
                    'first_video_date': last_item['snippet']['publishedAt'],
                }
            
            page_token = response.get('nextPageToken')
            if not page_token:
                break
                
            time.sleep(config.SLEEP_BETWEEN_CALLS)
            
        return oldest_video
        
    except Exception as e:
        logger.error(f"Error getting oldest video: {e}")
        return None


def get_all_video_ids(
    youtube,
    uploads_playlist_id: str,
    channel_id: str,
    start_page_token: Optional[str] = None
) -> Tuple[List[Dict], Optional[str]]:
    """
    Get ALL video IDs from a channel's uploads playlist.

    Unlike get_oldest_video() which caps at 10 pages, this paginates to
    completion. Supports checkpoint/resume via start_page_token.

    Args:
        youtube: Authenticated YouTube API service
        uploads_playlist_id: The uploads playlist ID (UU... format)
        channel_id: Channel ID (for tagging output)
        start_page_token: Optional page token to resume from

    Returns:
        Tuple of (list of video dicts, final page token or None if complete)
        Each dict: {video_id, channel_id, published_at, title}
    """
    video_list: List[Dict] = []
    page_token = start_page_token

    while True:
        try:
            request = youtube.playlistItems().list(
                part='snippet',
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=page_token
            )
            response = execute_request(request)

            for item in response.get('items', []):
                snippet = item.get('snippet', {})
                video_list.append({
                    'video_id': snippet.get('resourceId', {}).get('videoId'),
                    'channel_id': channel_id,
                    'published_at': snippet.get('publishedAt'),
                    'title': snippet.get('title'),
                })

            page_token = response.get('nextPageToken')
            if not page_token:
                return video_list, None

            time.sleep(config.SLEEP_BETWEEN_CALLS)

        except HttpError as e:
            if e.resp.status == 404:
                logger.warning(f"Playlist not found: {uploads_playlist_id}")
                break
            else:
                logger.error(f"Error enumerating videos for {channel_id}: {e}")
                return video_list, page_token

        except Exception as e:
            logger.error(f"Unexpected error enumerating videos for {channel_id}: {e}")
            return video_list, page_token

    return video_list, None


def get_newest_videos(youtube, uploads_playlist_id: str, max_results: int = 5) -> List[str]:
    """
    Get the newest video IDs from a channel's uploads playlist.
    
    Args:
        youtube: Authenticated YouTube API service
        uploads_playlist_id: The uploads playlist ID
        max_results: Maximum number of videos to return
        
    Returns:
        List of video IDs (newest first)
    """
    if not uploads_playlist_id:
        return []
        
    try:
        request = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=max_results
        )
        response = execute_request(request)
        
        video_ids = [
            item['contentDetails']['videoId']
            for item in response.get('items', [])
        ]
        
        return video_ids
        
    except Exception as e:
        logger.error(f"Error getting newest videos: {e}")
        return []


# =============================================================================
# NEW VIDEO DETECTION (FOR SWEEPS)
# =============================================================================

def detect_new_videos(
    youtube,
    channel_id: str,
    uploads_playlist_id: str,
    last_video_count: int,
    current_video_count: int,
    known_video_ids: Optional[List[str]] = None
) -> List[str]:
    """
    Detect new videos uploaded since last sweep.
    
    Args:
        youtube: Authenticated YouTube API service
        channel_id: Channel ID
        uploads_playlist_id: Uploads playlist ID
        last_video_count: Video count from previous sweep
        current_video_count: Current video count
        known_video_ids: Optional list of already-known video IDs
        
    Returns:
        List of new video IDs
    """
    if current_video_count <= last_video_count:
        return []
        
    # Calculate how many new videos
    new_count = current_video_count - last_video_count
    
    # Fetch enough videos to capture the new ones
    fetch_count = min(new_count + 5, 50)  # Buffer for safety
    
    try:
        request = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=fetch_count
        )
        response = execute_request(request)
        
        video_ids = [
            item['contentDetails']['videoId']
            for item in response.get('items', [])
        ]
        
        # If we have known IDs, filter to truly new videos
        if known_video_ids:
            known_set = set(known_video_ids)
            new_ids = [vid for vid in video_ids if vid not in known_set]
            return new_ids
        else:
            # Return the estimated new videos (newest ones)
            return video_ids[:new_count]
            
    except Exception as e:
        logger.error(f"Error detecting new videos for {channel_id}: {e}")
        return []


# =============================================================================
# CHANNEL ACTIVITIES
# =============================================================================

def get_channel_activities(youtube, channel_id: str, max_results: int = 5) -> List[Dict]:
    """
    Get recent activities for a channel.
    
    Args:
        youtube: Authenticated YouTube API service
        channel_id: Channel ID to fetch activities for
        max_results: Maximum number of activities to return
        
    Returns:
        List of activity dictionaries
    """
    try:
        request = youtube.activities().list(
            part=config.ACTIVITY_PARTS,
            channelId=channel_id,
            maxResults=max_results
        )
        response = execute_request(request)
        
        activities = []
        for item in response.get('items', []):
            snippet = item.get('snippet', {})
            content = item.get('contentDetails', {})
            
            activity = {
                'activity_type': snippet.get('type'),
                'activity_published': snippet.get('publishedAt'),
                'activity_title': snippet.get('title'),
            }
            
            # Extract video ID if it's an upload
            if snippet.get('type') == 'upload':
                upload_info = content.get('upload', {})
                activity['activity_video_id'] = upload_info.get('videoId')
            else:
                activity['activity_video_id'] = None
                
            activities.append(activity)
            
        return activities
        
    except Exception as e:
        logger.error(f"Error fetching activities for {channel_id}: {e}")
        return []


# =============================================================================
# SEARCH HELPERS
# =============================================================================

def search_videos(
    youtube,
    query: str,
    published_after: str,
    published_before: str,
    max_results: int = 50,
    region_code: Optional[str] = None,
    order: str = "date"
) -> List[Dict]:
    """
    Search for videos matching criteria.
    
    Args:
        youtube: Authenticated YouTube API service
        query: Search query string
        published_after: ISO timestamp for start of window
        published_before: ISO timestamp for end of window
        max_results: Maximum results per page (max 50)
        region_code: Optional region code (e.g., 'US')
        order: Sort order ('date', 'relevance', 'viewCount')
        
    Returns:
        List of video items from search results
    """
    try:
        kwargs = {
            'part': 'snippet',
            'type': 'video',
            'q': query,
            'publishedAfter': published_after,
            'publishedBefore': published_before,
            'order': order,
            'maxResults': max_results,
        }
        
        if region_code:
            kwargs['regionCode'] = region_code
            
        request = youtube.search().list(**kwargs)
        response = execute_request(request)
        
        return response.get('items', [])
        
    except Exception as e:
        logger.error(f"Error searching for '{query}': {e}")
        return []


def search_videos_paginated(
    youtube,
    query: str,
    published_after: str,
    published_before: str,
    max_pages: int = 10,
    region_code: Optional[str] = None,
    order: str = "date"
) -> List[Dict]:
    """
    Search for videos with pagination support.
    
    Args:
        youtube: Authenticated YouTube API service
        query: Search query string
        published_after: ISO timestamp for start of window
        published_before: ISO timestamp for end of window
        max_pages: Maximum number of pages to fetch
        region_code: Optional region code
        order: Sort order
        
    Returns:
        List of all video items across pages
    """
    all_videos = []
    page_token = None
    
    for _ in range(max_pages):
        try:
            kwargs = {
                'part': 'snippet',
                'type': 'video',
                'q': query,
                'publishedAfter': published_after,
                'publishedBefore': published_before,
                'order': order,
                'maxResults': 50,
            }
            
            if region_code:
                kwargs['regionCode'] = region_code
            if page_token:
                kwargs['pageToken'] = page_token
                
            request = youtube.search().list(**kwargs)
            response = execute_request(request)
            
            items = response.get('items', [])
            all_videos.extend(items)
            
            page_token = response.get('nextPageToken')
            if not page_token:
                break
                
            time.sleep(config.SLEEP_BETWEEN_CALLS)
            
        except Exception as e:
            logger.error(f"Error in paginated search for '{query}': {e}")
            break
            
    return all_videos


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def extract_channel_ids_from_search(search_results: List[Dict]) -> List[str]:
    """
    Extract unique channel IDs from search results.
    
    Args:
        search_results: List of search result items
        
    Returns:
        List of unique channel IDs
    """
    channel_ids = set()
    for item in search_results:
        channel_id = item.get('snippet', {}).get('channelId')
        if channel_id:
            channel_ids.add(channel_id)
    return list(channel_ids)


def filter_channels_by_date(
    channels: List[Dict],
    cutoff_date: str
) -> List[Dict]:
    """
    Filter channels to only include those created on or after cutoff date.
    
    Args:
        channels: List of channel dictionaries
        cutoff_date: ISO date string (e.g., '2026-01-01')
        
    Returns:
        Filtered list of channels
    """
    return [
        ch for ch in channels
        if ch.get('published_at', '') >= cutoff_date
    ]
