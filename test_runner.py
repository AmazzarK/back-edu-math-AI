#!/usr/bin/env python3
"""
Test runner script for EduMath AI Platform.
Provides utilities for running tests and generating coverage reports.
"""
import os
import sys
import subprocess
import unittest
from pathlib import Path

def setup_test_environment():
    """Set up environment variables for testing."""
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'True'
    os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    os.environ['SECRET_KEY'] = 'test-secret-key'
    os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret'
    os.environ['WTF_CSRF_ENABLED'] = 'False'

def run_unit_tests():
    """Run unit tests."""
    print("Running unit tests...")
    setup_test_environment()
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent / 'tests'
    suite = loader.discover(str(start_dir), pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_with_coverage():
    """Run tests with coverage reporting."""
    print("Running tests with coverage...")
    setup_test_environment()
    
    try:
        # Run coverage
        cmd = [
            sys.executable, '-m', 'coverage', 'run',
            '--source=app',
            '--omit=app/tests/*,*/venv/*,*/migrations/*',
            '-m', 'unittest', 'discover',
            '-s', 'tests',
            '-p', 'test_*.py',
            '-v'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Generate coverage report
        print("\nGenerating coverage report...")
        subprocess.run([sys.executable, '-m', 'coverage', 'report', '-m'])
        
        # Generate HTML coverage report
        print("\nGenerating HTML coverage report...")
        subprocess.run([sys.executable, '-m', 'coverage', 'html'])
        print("HTML coverage report generated in htmlcov/")
        
        return result.returncode == 0
        
    except FileNotFoundError:
        print("Coverage not installed. Install with: pip install coverage")
        return False

def run_api_tests():
    """Run API integration tests."""
    print("Running API integration tests...")
    setup_test_environment()
    
    # Run specific API tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent / 'tests'
    
    # Load API test files specifically
    api_test_files = [
        'test_auth_api.py',
        'test_chat_api.py',
        'test_classes_api.py',
        'test_dashboard_api.py',
        'test_files_api.py',
        'test_notifications_api.py'
    ]
    
    suite = unittest.TestSuite()
    for test_file in api_test_files:
        test_path = start_dir / test_file
        if test_path.exists():
            tests = loader.loadTestsFromName(f'tests.{test_file[:-3]}')
            suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def check_code_quality():
    """Run code quality checks."""
    print("Running code quality checks...")
    
    checks_passed = True
    
    # Run flake8 for style checking
    try:
        print("\n1. Running flake8...")
        result = subprocess.run([
            sys.executable, '-m', 'flake8',
            'app/',
            '--max-line-length=100',
            '--ignore=E501,W503'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ flake8 passed")
        else:
            print("✗ flake8 failed:")
            print(result.stdout)
            checks_passed = False
            
    except FileNotFoundError:
        print("flake8 not installed. Install with: pip install flake8")
    
    # Run pylint for additional checks
    try:
        print("\n2. Running pylint...")
        result = subprocess.run([
            sys.executable, '-m', 'pylint',
            'app/',
            '--disable=C0114,C0115,C0116,R0903'  # Disable some verbose warnings
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ pylint passed")
        else:
            print("⚠️  pylint warnings:")
            print(result.stdout)
            
    except FileNotFoundError:
        print("pylint not installed. Install with: pip install pylint")
    
    # Run bandit for security checks
    try:
        print("\n3. Running bandit...")
        result = subprocess.run([
            sys.executable, '-m', 'bandit',
            '-r', 'app/',
            '-x', 'app/tests/'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ bandit passed")
        else:
            print("⚠️  bandit security warnings:")
            print(result.stdout)
            
    except FileNotFoundError:
        print("bandit not installed. Install with: pip install bandit")
    
    return checks_passed

def run_performance_tests():
    """Run performance tests."""
    print("Running performance tests...")
    
    try:
        # Use locust for load testing if available
        test_file = Path(__file__).parent / 'tests' / 'performance' / 'locustfile.py'
        if test_file.exists():
            print("Run performance tests with:")
            print(f"  locust -f {test_file} --host=http://localhost:5000")
        else:
            print("No performance tests found")
            
    except Exception as e:
        print(f"Performance test setup failed: {e}")

def clean_test_artifacts():
    """Clean up test artifacts."""
    print("Cleaning test artifacts...")
    
    artifacts = [
        '.coverage',
        'htmlcov/',
        '.pytest_cache/',
        '__pycache__/',
        '*.pyc'
    ]
    
    for artifact in artifacts:
        if os.path.exists(artifact):
            if os.path.isdir(artifact):
                import shutil
                shutil.rmtree(artifact)
                print(f"Removed directory: {artifact}")
            else:
                os.remove(artifact)
                print(f"Removed file: {artifact}")

def main():
    """Main CLI interface for test runner."""
    if len(sys.argv) < 2:
        print("EduMath AI Platform - Test Runner")
        print("Usage: python test_runner.py <command>")
        print("\nAvailable commands:")
        print("  unit        - Run unit tests")
        print("  api         - Run API integration tests")
        print("  coverage    - Run tests with coverage")
        print("  quality     - Run code quality checks")
        print("  performance - Run performance tests")
        print("  all         - Run all tests")
        print("  clean       - Clean test artifacts")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'unit':
        success = run_unit_tests()
        sys.exit(0 if success else 1)
    
    elif command == 'api':
        success = run_api_tests()
        sys.exit(0 if success else 1)
    
    elif command == 'coverage':
        success = run_with_coverage()
        sys.exit(0 if success else 1)
    
    elif command == 'quality':
        success = check_code_quality()
        sys.exit(0 if success else 1)
    
    elif command == 'performance':
        run_performance_tests()
    
    elif command == 'all':
        print("Running comprehensive test suite...")
        print("=" * 50)
        
        success = True
        
        # Run unit tests
        print("\n1. Unit Tests")
        print("-" * 20)
        success &= run_unit_tests()
        
        # Run API tests
        print("\n2. API Tests")
        print("-" * 20)
        success &= run_api_tests()
        
        # Run coverage
        print("\n3. Coverage Analysis")
        print("-" * 20)
        success &= run_with_coverage()
        
        # Run quality checks
        print("\n4. Code Quality")
        print("-" * 20)
        success &= check_code_quality()
        
        print("\n" + "=" * 50)
        if success:
            print("✓ All tests passed!")
        else:
            print("✗ Some tests failed!")
        
        sys.exit(0 if success else 1)
    
    elif command == 'clean':
        clean_test_artifacts()
    
    else:
        print(f"Unknown command: {command}")
        print("Use 'python test_runner.py' to see available commands")

if __name__ == '__main__':
    main()
