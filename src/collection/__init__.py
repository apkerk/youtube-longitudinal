"""
Collection module for YouTube Longitudinal Data Collection.
Contains scripts for initial data collection across all streams.

New Creator Cohort Streams:
- Stream A: Intent Creators (discover_intent.py)
- Stream A': Non-Intent Creators (discover_non_intent.py)
- Stream B: Algorithm Favorites/Benchmark (discover_benchmark.py)
- Stream C: Searchable Random (discover_random.py)
- Stream D: Casual Uploaders (discover_casual.py)

Gender Gap Panel:
- Data prep: clean_baileys.py
- Video enumeration: enumerate_videos.py
- AI census: discover_ai_creators.py
"""

__all__ = [
    "discover_intent",
    "discover_non_intent",
    "discover_benchmark",
    "discover_random",
    "discover_casual",
    "clean_baileys",
    "enumerate_videos",
    "discover_ai_creators",
]
