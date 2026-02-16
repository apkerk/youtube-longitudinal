"""
config.py
---------
Centralized configuration for YouTube Longitudinal Data Collection.

Contains:
- Intent keywords (8 languages) for Stream A
- Non-intent content keywords (8 languages) for Stream A'
- Raw file queries for Stream D (Casual)
- API configuration strings
- File paths and naming conventions
- Sweep schedules

Author: Katie Apker
Last Updated: Feb 02, 2026
"""

from pathlib import Path
from typing import Dict, List
from datetime import datetime

# =============================================================================
# PROJECT PATHS
# =============================================================================

# Project root (relative to this file: src/config.py -> project root)
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHANNELS_DIR = DATA_DIR / "channels"
VIDEOS_DIR = DATA_DIR / "videos"
LOGS_DIR = DATA_DIR / "logs"
CONFIG_DIR = PROJECT_ROOT / "config"

# Stream-specific directories
STREAM_DIRS = {
    "stream_a": CHANNELS_DIR / "stream_a",
    "stream_a_prime": CHANNELS_DIR / "stream_a_prime",
    "stream_b": CHANNELS_DIR / "stream_b",
    "stream_c": CHANNELS_DIR / "stream_c",
    "stream_d": CHANNELS_DIR / "stream_d",
}

# =============================================================================
# SAMPLE TARGETS
# =============================================================================

SAMPLE_TARGETS = {
    "stream_a": 200000,      # Intent creators (LARGE for attrition)
    "stream_a_prime": 200000, # Non-intent creators (LARGE for attrition)
    "stream_b": 2000,        # Algorithm favorites (benchmark)
    "stream_c": 50000,       # Searchable random
    "stream_d": 25000,       # Casual uploads
}

# =============================================================================
# SWEEP CONFIGURATION
# =============================================================================

SWEEP_FREQUENCY = {
    "stream_a": "weekly",
    "stream_a_prime": "weekly",
    "stream_b": "monthly",
    "stream_c": "monthly",
    "stream_d": "weekly",
}

# Cohort date filter (channels created on or after this date)
COHORT_CUTOFF_DATE = "2026-01-01"

# =============================================================================
# INTENT KEYWORDS (Stream A) - 8 Languages
# Ordered by yield rate (highest first based on EXP-006)
# =============================================================================

INTENT_KEYWORDS: Dict[str, List[str]] = {
    "Hindi": [
        "Mere channel mein aapka swagat hai",  # Welcome to my channel
        "Mera pehla video",                     # My first video
        "Introduction hindi",
        "Namaste doston",                       # Hello friends
        "Channel trailer hindi",
        "Apna pehla video",                     # My first video (alt)
    ],
    "English": [
        "Welcome to my channel",
        "My first video",
        "Introduction",
        "Intro",
        "Vlog 1",
        "Channel Trailer",
        "Get to know me",
        "Channel Introduction",
        "First video ever",
    ],
    "Spanish": [
        "Bienvenidos a mi canal",               # Welcome to my channel
        "Mi primer video",                      # My first video
        "Introducción",
        "Vlog 1 español",
        "Conóceme",                             # Get to know me
        "Presentación de mi canal",             # Channel presentation
    ],
    "Japanese": [
        "チャンネル登録よろしく",                # Please subscribe
        "初投稿",                               # First upload
        "自己紹介",                             # Self-introduction
        "はじめまして",                         # Nice to meet you
        "チャンネル紹介",                       # Channel introduction
    ],
    "German": [
        "Willkommen auf meinem Kanal",          # Welcome to my channel
        "Mein erstes Video",                    # My first video
        "Vorstellung",                          # Introduction
        "Kanal Trailer",
        "Über mich",                            # About me
    ],
    "Portuguese": [
        "Bem-vindos ao meu canal",              # Welcome to my channel
        "Meu primeiro vídeo",                   # My first video
        "Introdução",
        "Me conhecendo",                        # Getting to know me
        "Trailer do canal",
    ],
    "Korean": [
        "제 채널에 오신 것을 환영합니다",       # Welcome to my channel
        "첫 번째 영상",                         # First video
        "자기소개",                             # Self-introduction
        "채널 소개",                            # Channel introduction
        "첫 영상",                              # First video (alt)
    ],
    "French": [
        "Bienvenue sur ma chaîne",              # Welcome to my channel
        "Ma première vidéo",                    # My first video
        "Introduction",
        "Présentation",                         # Presentation
        "Trailer de la chaîne",
    ],
}

# =============================================================================
# NON-INTENT CONTENT KEYWORDS (Stream A') - 8 Languages
# Content-focused keywords for creators who don't announce themselves
# =============================================================================

NON_INTENT_KEYWORDS: Dict[str, List[str]] = {
    "Hindi": [
        "gameplay hindi",
        "tutorial hindi",
        "recipe hindi",
        "review hindi",
        "unboxing hindi",
        "vlog hindi",
    ],
    "English": [
        "gameplay",
        "let's play",
        "tutorial",
        "recipe",
        "review",
        "unboxing",
        "haul",
        "day in my life",
        "GRWM",
        "cover song",
    ],
    "Spanish": [
        "gameplay español",
        "tutorial español",
        "receta",
        "reseña",
        "unboxing español",
        "rutina",
    ],
    "Japanese": [
        "ゲーム実況",                           # Game commentary
        "チュートリアル",                       # Tutorial
        "レビュー",                             # Review
        "開封",                                 # Unboxing
        "Vlog 日本",
    ],
    "German": [
        "gameplay deutsch",
        "tutorial deutsch",
        "rezept",
        "review deutsch",
        "unboxing deutsch",
    ],
    "Portuguese": [
        "gameplay português",
        "tutorial português",
        "receita",
        "review português",
        "unboxing português",
    ],
    "Korean": [
        "게임 플레이",                          # Gameplay
        "튜토리얼",                             # Tutorial
        "리뷰",                                 # Review
        "언박싱",                               # Unboxing
        "브이로그",                             # Vlog
    ],
    "French": [
        "gameplay français",
        "tutoriel",
        "recette",
        "review français",
        "unboxing français",
    ],
}

# =============================================================================
# CASUAL UPLOAD QUERIES (Stream D)
# Raw file patterns from cameras and phones
# =============================================================================

CASUAL_QUERIES: List[str] = [
    # Camera defaults
    "IMG_",          # iPhone, many cameras
    "MVI_",          # Canon video
    "DSC_",          # Sony, Nikon
    "MOV_",          # QuickTime
    "VID_",          # Android
    "DSCF",          # Fujifilm
    "GOPR",          # GoPro
    "DJI_",          # DJI drones
    "P_",            # Some Android phones
    
    # Screen recordings
    "Screen Recording",
    "Untitled",
    "New Recording",
    
    # Date-based defaults
    "20260",         # Catches 2026-01-XX style filenames
    "video_2026",
    "Video 2026",
]

# =============================================================================
# BENCHMARK QUERIES (Stream B)
# Vowel search for algorithm favorites
# =============================================================================

BENCHMARK_QUERIES: List[str] = [
    "a", "e", "i", "o", "u",
    "video",
]

# =============================================================================
# RANDOM PREFIX CONFIG (Stream C)
# =============================================================================

RANDOM_PREFIX_LENGTH = 3
RANDOM_PREFIX_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789"

# =============================================================================
# API CONFIGURATION
# =============================================================================

# Parts to request for channel details (Tier 1+2)
CHANNEL_PARTS = "snippet,statistics,contentDetails,status,topicDetails,brandingSettings,localizations"

# Parts to request for video details
VIDEO_PARTS = "snippet,statistics,contentDetails,status"

# Parts for activity feed
ACTIVITY_PARTS = "snippet,contentDetails"

# Maximum results per API call
MAX_RESULTS_PER_PAGE = 50

# Rate limiting
SLEEP_BETWEEN_CALLS = 0.1  # seconds
MAX_RETRIES = 5

# =============================================================================
# YOUTUBE VIDEO CATEGORY MAPPING (categoryId in videos)
# =============================================================================

YOUTUBE_CATEGORIES: Dict[int, str] = {
    1: "Film & Animation",
    2: "Autos & Vehicles",
    10: "Music",
    15: "Pets & Animals",
    17: "Sports",
    18: "Short Movies",
    19: "Travel & Events",
    20: "Gaming",
    21: "Videoblogging",
    22: "People & Blogs",
    23: "Comedy",
    24: "Entertainment",
    25: "News & Politics",
    26: "Howto & Style",
    27: "Education",
    28: "Science & Technology",
    29: "Nonprofits & Activism",
    30: "Movies",
    31: "Anime/Animation",
    32: "Action/Adventure",
    33: "Classics",
    34: "Comedy",
    35: "Documentary",
    36: "Drama",
    37: "Family",
    38: "Foreign",
    39: "Horror",
    40: "Sci-Fi/Fantasy",
    41: "Thriller",
    42: "Shorts",
    43: "Shows",
    44: "Trailers",
}

# =============================================================================
# YOUTUBE TOPIC CATEGORIES (topicDetails - Wikipedia-based hierarchical topics)
# These are assigned to CHANNELS and are more granular than video categories
# Full list from: https://developers.google.com/youtube/v3/docs/channels#topicDetails
# =============================================================================

# Parent Topics (Top Level)
YOUTUBE_PARENT_TOPICS: Dict[str, str] = {
    "/m/04rlf": "Music",
    "/m/02mscn": "Christian music",
    "/m/0ggq0m": "Classical music",
    "/m/01lyv": "Country music",
    "/m/02lkt": "Electronic music",
    "/m/0glt670": "Hip hop music",
    "/m/05rwpb": "Independent music",
    "/m/03_d0": "Jazz",
    "/m/028sqc": "Music of Asia",
    "/m/0g293": "Music of Latin America",
    "/m/064t9": "Pop music",
    "/m/06cqb": "Reggae",
    "/m/06j6l": "Rhythm and blues",
    "/m/06by7": "Rock music",
    "/m/0gywn": "Soul music",
    "/m/0bzvm2": "Gaming",
    "/m/025zzc": "Action game",
    "/m/02ntfj": "Action-adventure game",
    "/m/0b1vjn": "Casual game",
    "/m/02hygl": "Music video game",
    "/m/04q1x3q": "Puzzle video game",
    "/m/01sjng": "Racing video game",
    "/m/0403l3g": "Role-playing video game",
    "/m/021bp2": "Simulation video game",
    "/m/022dc6": "Sports game",
    "/m/03hf_rm": "Strategy video game",
    "/m/06ntj": "Sports",
    "/m/0jm_": "American football",
    "/m/018jz": "Baseball",
    "/m/018w8": "Basketball",
    "/m/01cgz": "Boxing",
    "/m/09xp_": "Cricket",
    "/m/02vx4": "Football",
    "/m/037hz": "Golf",
    "/m/03tmr": "Ice hockey",
    "/m/01h7lh": "Mixed martial arts",
    "/m/0410tth": "Motorsport",
    "/m/07bs0": "Tennis",
    "/m/07_53": "Volleyball",
    "/m/02jjt": "Entertainment",
    "/m/09kqc": "Humor",
    "/m/02vxn": "Movies",
    "/m/05qjc": "Performing arts",
    "/m/066wd": "Professional wrestling",
    "/m/0f2f9": "TV shows",
    "/m/019_rr": "Lifestyle",
    "/m/032tl": "Fashion",
    "/m/027x7n": "Fitness",
    "/m/02wbm": "Food",
    "/m/03glg": "Hobby",
    "/m/068hy": "Pets",
    "/m/041xxh": "Physical attractiveness",
    "/m/07c1v": "Technology",
    "/m/07bxq": "Tourism",
    "/m/07yv9": "Vehicles",
    "/m/098wr": "Society",
    "/m/09s1f": "Business",
    "/m/0kt51": "Health",
    "/m/01h6rj": "Military",
    "/m/05qt0": "Politics",
    "/m/06bvp": "Religion",
    "/m/01k8wb": "Knowledge",
}

# Extended Topic Mapping (Wikipedia URL to readable name)
# Topics are returned as Wikipedia URLs like: https://en.wikipedia.org/wiki/Entertainment
YOUTUBE_TOPIC_URL_TO_NAME: Dict[str, str] = {
    # Music
    "https://en.wikipedia.org/wiki/Music": "Music",
    "https://en.wikipedia.org/wiki/Christian_music": "Christian music",
    "https://en.wikipedia.org/wiki/Classical_music": "Classical music",
    "https://en.wikipedia.org/wiki/Country_music": "Country music",
    "https://en.wikipedia.org/wiki/Electronic_music": "Electronic music",
    "https://en.wikipedia.org/wiki/Hip_hop_music": "Hip hop music",
    "https://en.wikipedia.org/wiki/Independent_music": "Independent music",
    "https://en.wikipedia.org/wiki/Jazz": "Jazz",
    "https://en.wikipedia.org/wiki/Music_of_Asia": "Music of Asia",
    "https://en.wikipedia.org/wiki/Music_of_Latin_America": "Music of Latin America",
    "https://en.wikipedia.org/wiki/Pop_music": "Pop music",
    "https://en.wikipedia.org/wiki/Reggae": "Reggae",
    "https://en.wikipedia.org/wiki/Rhythm_and_blues": "Rhythm and blues",
    "https://en.wikipedia.org/wiki/Rock_music": "Rock music",
    "https://en.wikipedia.org/wiki/Soul_music": "Soul music",
    
    # Gaming
    "https://en.wikipedia.org/wiki/Video_game_culture": "Gaming",
    "https://en.wikipedia.org/wiki/Action_game": "Action game",
    "https://en.wikipedia.org/wiki/Action-adventure_game": "Action-adventure game",
    "https://en.wikipedia.org/wiki/Casual_game": "Casual game",
    "https://en.wikipedia.org/wiki/Music_video_game": "Music video game",
    "https://en.wikipedia.org/wiki/Puzzle_video_game": "Puzzle video game",
    "https://en.wikipedia.org/wiki/Racing_video_game": "Racing video game",
    "https://en.wikipedia.org/wiki/Role-playing_video_game": "Role-playing video game",
    "https://en.wikipedia.org/wiki/Simulation_video_game": "Simulation video game",
    "https://en.wikipedia.org/wiki/Sports_game": "Sports game",
    "https://en.wikipedia.org/wiki/Strategy_video_game": "Strategy video game",
    
    # Sports
    "https://en.wikipedia.org/wiki/Sport": "Sports",
    "https://en.wikipedia.org/wiki/American_football": "American football",
    "https://en.wikipedia.org/wiki/Baseball": "Baseball",
    "https://en.wikipedia.org/wiki/Basketball": "Basketball",
    "https://en.wikipedia.org/wiki/Boxing": "Boxing",
    "https://en.wikipedia.org/wiki/Cricket": "Cricket",
    "https://en.wikipedia.org/wiki/Association_football": "Football (Soccer)",
    "https://en.wikipedia.org/wiki/Golf": "Golf",
    "https://en.wikipedia.org/wiki/Ice_hockey": "Ice hockey",
    "https://en.wikipedia.org/wiki/Mixed_martial_arts": "Mixed martial arts",
    "https://en.wikipedia.org/wiki/Motorsport": "Motorsport",
    "https://en.wikipedia.org/wiki/Tennis": "Tennis",
    "https://en.wikipedia.org/wiki/Volleyball": "Volleyball",
    
    # Entertainment
    "https://en.wikipedia.org/wiki/Entertainment": "Entertainment",
    "https://en.wikipedia.org/wiki/Humor": "Humor",
    "https://en.wikipedia.org/wiki/Film": "Movies",
    "https://en.wikipedia.org/wiki/Performing_arts": "Performing arts",
    "https://en.wikipedia.org/wiki/Professional_wrestling": "Professional wrestling",
    "https://en.wikipedia.org/wiki/Television_program": "TV shows",
    
    # Lifestyle
    "https://en.wikipedia.org/wiki/Lifestyle_(sociology)": "Lifestyle",
    "https://en.wikipedia.org/wiki/Fashion": "Fashion",
    "https://en.wikipedia.org/wiki/Physical_fitness": "Fitness",
    "https://en.wikipedia.org/wiki/Food": "Food",
    "https://en.wikipedia.org/wiki/Hobby": "Hobby",
    "https://en.wikipedia.org/wiki/Pet": "Pets",
    "https://en.wikipedia.org/wiki/Physical_attractiveness": "Physical attractiveness (Beauty)",
    "https://en.wikipedia.org/wiki/Technology": "Technology",
    "https://en.wikipedia.org/wiki/Tourism": "Tourism",
    "https://en.wikipedia.org/wiki/Vehicle": "Vehicles",
    
    # Society
    "https://en.wikipedia.org/wiki/Society": "Society",
    "https://en.wikipedia.org/wiki/Business": "Business",
    "https://en.wikipedia.org/wiki/Health": "Health",
    "https://en.wikipedia.org/wiki/Military": "Military",
    "https://en.wikipedia.org/wiki/Politics": "Politics",
    "https://en.wikipedia.org/wiki/Religion": "Religion",
    
    # Knowledge
    "https://en.wikipedia.org/wiki/Knowledge": "Knowledge",
    
    # Additional common topics
    "https://en.wikipedia.org/wiki/Anime": "Anime",
    "https://en.wikipedia.org/wiki/Animation": "Animation",
    "https://en.wikipedia.org/wiki/Comedy": "Comedy",
    "https://en.wikipedia.org/wiki/Dance": "Dance",
    "https://en.wikipedia.org/wiki/Education": "Education",
    "https://en.wikipedia.org/wiki/News": "News",
    "https://en.wikipedia.org/wiki/Science": "Science",
    "https://en.wikipedia.org/wiki/Nature": "Nature",
    "https://en.wikipedia.org/wiki/Travel": "Travel",
    "https://en.wikipedia.org/wiki/Cooking": "Cooking",
    "https://en.wikipedia.org/wiki/Beauty": "Beauty",
    "https://en.wikipedia.org/wiki/Vlog": "Vlog",
    "https://en.wikipedia.org/wiki/How-to": "How-to",
    "https://en.wikipedia.org/wiki/Review": "Review",
    "https://en.wikipedia.org/wiki/Unboxing": "Unboxing",
}


def decode_topic_url(url: str) -> str:
    """
    Decode a Wikipedia topic URL to a readable name.
    
    Args:
        url: Wikipedia URL like 'https://en.wikipedia.org/wiki/Entertainment'
        
    Returns:
        Decoded topic name or the URL path if not in mapping
    """
    if url in YOUTUBE_TOPIC_URL_TO_NAME:
        return YOUTUBE_TOPIC_URL_TO_NAME[url]
    
    # Fallback: extract from URL path
    if "/wiki/" in url:
        topic = url.split("/wiki/")[-1].replace("_", " ")
        return topic
    
    return url


def decode_topic_id(topic_id: str) -> str:
    """
    Decode a YouTube topic ID to a readable name.
    
    Args:
        topic_id: Topic ID like '/m/04rlf'
        
    Returns:
        Decoded topic name or the ID if not in mapping
    """
    return YOUTUBE_PARENT_TOPICS.get(topic_id, topic_id)

# =============================================================================
# DATA SCHEMA DEFINITIONS
# =============================================================================

# Channel fields for initial collection
CHANNEL_INITIAL_FIELDS = [
    # Identification
    "channel_id",
    "title",
    "description",
    "custom_url",
    "published_at",
    
    # Metrics
    "view_count",
    "subscriber_count",
    "video_count",
    "hidden_subscriber_count",
    
    # Geographic & Language
    "country",
    "default_language",
    
    # Topic Categories (hierarchical - more granular than video categories)
    "topic_categories_raw",      # Full list of Wikipedia URLs
    "topic_ids",                 # YouTube topic IDs (/m/xxxxx format)
    "topic_1",                   # Primary topic (decoded)
    "topic_2",                   # Secondary topic (decoded)
    "topic_3",                   # Tertiary topic (decoded)
    "topic_count",               # Number of topics assigned
    
    # Policy-relevant (for shock analysis)
    "made_for_kids",
    "privacy_status",
    "long_uploads_status",
    "is_linked",
    
    # Branding
    "keywords",
    "localization_count",
    "localizations_available",
    "profile_picture_url",
    
    # Content structure
    "uploads_playlist_id",
    "first_video_date",
    "first_video_id",
    "first_video_title",
    
    # Discovery metadata (system)
    "stream_type",
    "discovery_language",
    "discovery_keyword",
    "scraped_at",
]

# Channel fields for sweeps
CHANNEL_SWEEP_FIELDS = [
    "channel_id",
    "view_count",
    "subscriber_count",
    "video_count",
    "made_for_kids",
    "status",
    "made_for_kids_changed",
    "scraped_at",
]

# Video fields
VIDEO_FIELDS = [
    "video_id",
    "channel_id",
    "title",
    "description",
    "published_at",
    "view_count",
    "like_count",
    "comment_count",
    "duration",
    "duration_seconds",
    "is_short",
    "category_id",
    "category_name",
    "tags",
    "hashtags",
    "hashtag_count",
    "definition",
    "dimension",
    "caption",
    "licensed_content",
    "content_rating_yt",
    "region_restriction_blocked",
    "region_restriction_allowed",
    "trigger_type",
    "scraped_at",
]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_timestamp() -> str:
    """Get current timestamp in standard format."""
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def get_date_stamp() -> str:
    """Get current date stamp for filenames."""
    return datetime.utcnow().strftime("%Y%m%d")


def ensure_directories() -> None:
    """Create all required directories if they don't exist."""
    for stream_dir in STREAM_DIRS.values():
        stream_dir.mkdir(parents=True, exist_ok=True)
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def get_output_path(stream: str, prefix: str = "initial") -> Path:
    """Get output path for a stream's data file."""
    return STREAM_DIRS[stream] / f"{prefix}_{get_date_stamp()}.csv"


def get_all_intent_keywords() -> List[tuple]:
    """Get all intent keywords as (keyword, language) tuples."""
    keywords = []
    for language, kw_list in INTENT_KEYWORDS.items():
        for kw in kw_list:
            keywords.append((kw, language))
    return keywords


def get_all_non_intent_keywords() -> List[tuple]:
    """Get all non-intent keywords as (keyword, language) tuples."""
    keywords = []
    for language, kw_list in NON_INTENT_KEYWORDS.items():
        for kw in kw_list:
            keywords.append((kw, language))
    return keywords


# =============================================================================
# VALIDATION THRESHOLDS
# =============================================================================

VALIDATION_THRESHOLDS = {
    "max_subscriber_drop_pct": 0.5,      # Flag if subs drop >50%
    "max_view_decrease": 0,              # Views should never decrease
    "max_video_decrease": 0,             # Videos shouldn't decrease (deletions flagged)
}

# =============================================================================
# SHORTS CLASSIFICATION
# =============================================================================

SHORTS_MAX_DURATION_SECONDS = 60  # Videos <= 60 seconds are Shorts

