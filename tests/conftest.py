"""Test configuration for pytest."""

import pytest
import os

# Ensure the PyQt6 application doesn't require a display for testing
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "gui: mark test as requiring GUI components"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )