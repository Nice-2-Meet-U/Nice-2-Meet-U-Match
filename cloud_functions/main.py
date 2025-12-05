"""
Main entry point for the Cloud Function.
Google Cloud Functions looks for a file named main.py.
"""
from match_cleanup_handler import handle_pool_event

# Export the handler function
__all__ = ['handle_pool_event']
