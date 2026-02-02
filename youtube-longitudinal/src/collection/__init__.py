"""
Collection module for YouTube Longitudinal Data Collection.
Contains scripts for initial data collection across all streams.

Streams:
- Stream A: Intent Creators (discover_intent.py)
- Stream A': Non-Intent Creators (discover_non_intent.py)
- Stream B: Algorithm Favorites/Benchmark (discover_benchmark.py)
- Stream C: Searchable Random (discover_random.py)
- Stream D: Casual Uploaders (discover_casual.py)
"""

__all__ = [
    "discover_intent",
    "discover_non_intent", 
    "discover_benchmark",
    "discover_random",
    "discover_casual",
]
