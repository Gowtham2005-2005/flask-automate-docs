import pytest
import sys
import os

def run_tests():
    """Run the tests with coverage reporting"""
    # Add the parent directory to the Python path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    # Run pytest with coverage
    pytest.main([
        '--cov=app',
        '--cov-report=term-missing',
        '--cov-report=html',
        'test_app.py'
    ])

if __name__ == '__main__':
    run_tests() 