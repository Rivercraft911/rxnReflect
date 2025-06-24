"""
Reaction Wheel Driver Package.

This package provides the ReactionWheel class for communicating with the RW4-12.
"""

from .driver import (
    ReactionWheel,
    WheelError,
    WheelCrcError,
    WheelNackError,
    NSPCommand,
    WheelMode,
    EDACFile,
    
    
    
    #the low-level helpers needed ONLY for the loopback test
    _slip_encode,
    _slip_decode,
    _crc_func,
    FEND
)