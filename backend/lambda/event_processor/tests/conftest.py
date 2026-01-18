"""
Pytest configuration for Event Processor Lambda tests.

Sets up the path to allow importing from parent directory.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
lambda_event_processor_dir = Path(__file__).parent.parent
sys.path.insert(0, str(lambda_event_processor_dir))
