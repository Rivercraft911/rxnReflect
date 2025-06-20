"""
Reaction Wheel Driver Package.

This package provides the ReactionWheel class for communicating with the RW4-12.
"""

# Expose the main class and custom exceptions to the user of this package.
from .driver import ReactionWheel, WheelError, WheelCrcError, WheelNackError