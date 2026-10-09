# Insight generation is implemented in analytics.py so it can be tested independently.
# This module is kept as a clear project entry point for future extensions.
from analytics import generate_insights

__all__ = ["generate_insights"]
