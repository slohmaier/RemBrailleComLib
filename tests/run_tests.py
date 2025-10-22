#!/usr/bin/env python3
"""
RemBraille Test Suite Runner

Runs all RemBraille protocol tests with proper organization and reporting.
"""

import sys
import os
import unittest
import argparse
from io import StringIO
import time

# Add tests directory to path
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TESTS_DIR)


class ColoredTextTestResult(unittest.TextTestResult):
    """Custom test result class with colored output"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_start_time = None

    def startTest(self, test):
        super().startTest(test)
        self.test_start_time = time.time()

    def addSuccess(self, test):
        super().addSuccess(test)
        elapsed = time.time() - self.test_start_time
        if self.showAll:
            self.stream.writeln(f" ... \033[92mok\033[0m ({elapsed:.3f}s)")

    def addError(self, test, err):
        super().addError(test, err)
        if self.showAll:
            self.stream.writeln(" ... \033[91mERROR\033[0m")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        if self.showAll:
            self.stream.writeln(" ... \033[91mFAIL\033[0m")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        if self.showAll:
            self.stream.writeln(f" ... \033[93mskipped\033[0m '{reason}'")


class ColoredTextTestRunner(unittest.TextTestRunner):
    """Custom test runner with colored output"""
    resultclass = ColoredTextTestResult


def discover_tests(test_type=None, pattern='test*.py'):
    """Discover tests based on type"""
    loader = unittest.TestLoader()

    if test_type == 'unit':
        suite = loader.discover(
            start_dir=os.path.join(TESTS_DIR, 'unit'),
            pattern=pattern,
            top_level_dir=TESTS_DIR
        )
    elif test_type == 'integration':
        suite = loader.discover(
            start_dir=os.path.join(TESTS_DIR, 'integration'),
            pattern=pattern,
            top_level_dir=TESTS_DIR
        )
    elif test_type == 'server-client':
        suite = loader.discover(
            start_dir=os.path.join(TESTS_DIR, 'integration'),
            pattern='test_server_client.py',
            top_level_dir=TESTS_DIR
        )
    elif test_type == 'receiver':
        suite = loader.discover(
            start_dir=os.path.join(TESTS_DIR, 'integration'),
            pattern='test_receiver.py',
            top_level_dir=TESTS_DIR
        )
    elif test_type == 'driver':
        suite = loader.discover(
            start_dir=os.path.join(TESTS_DIR, 'integration'),
            pattern='test_driver.py',
            top_level_dir=TESTS_DIR
        )
    elif test_type == 'all':
        suite = unittest.TestSuite()
        # Add unit tests
        unit_suite = loader.discover(
            start_dir=os.path.join(TESTS_DIR, 'unit'),
            pattern=pattern,
            top_level_dir=TESTS_DIR
        )
        suite.addTests(unit_suite)

        # Add integration tests
        integration_suite = loader.discover(
            start_dir=os.path.join(TESTS_DIR, 'integration'),
            pattern=pattern,
            top_level_dir=TESTS_DIR
        )
        suite.addTests(integration_suite)
    else:
        # Default: discover all tests
        suite = loader.discover(
            start_dir=TESTS_DIR,
            pattern=pattern,
            top_level_dir=TESTS_DIR
        )

    return suite


def print_banner(text):
    """Print a formatted banner"""
    width = 70
    print("\n" + "=" * width)
    print(f" {text}")
    print("=" * width + "\n")


def print_summary(result):
    """Print test summary"""
    print_banner("Test Summary")

    total = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    success = total - failures - errors - skipped

    print(f"Total Tests:  {total}")
    print(f"\033[92mPassed:       {success}\033[0m")

    if failures > 0:
        print(f"\033[91mFailed:       {failures}\033[0m")

    if errors > 0:
        print(f"\033[91mErrors:       {errors}\033[0m")

    if skipped > 0:
        print(f"\033[93mSkipped:      {skipped}\033[0m")

    print()

    if result.wasSuccessful():
        print("\033[92m✓ All tests passed!\033[0m\n")
        return 0
    else:
        print("\033[91m✗ Some tests failed\033[0m\n")
        return 1


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(
        description='Run RemBraille protocol tests',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Types:
  unit              Run only unit tests (protocol message tests)
  integration       Run all integration tests
  server-client     Run server-client integration tests only
  receiver          Run receiver (macOS app) integration tests
  driver            Run driver (NVDA) integration tests
  all               Run all tests (default)

Examples:
  # Run all tests
  python3 run_tests.py

  # Run only unit tests
  python3 run_tests.py --type unit

  # Run receiver integration tests with verbose output
  python3 run_tests.py --type receiver -v

  # Run specific test
  python3 run_tests.py --pattern test_protocol.py
        """
    )

    parser.add_argument(
        '--type', '-t',
        choices=['unit', 'integration', 'server-client', 'receiver', 'driver', 'all'],
        default='all',
        help='Type of tests to run (default: all)'
    )

    parser.add_argument(
        '--pattern', '-p',
        default='test*.py',
        help='Pattern to match test files (default: test*.py)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='count',
        default=1,
        help='Verbose output (use -vv for extra verbose)'
    )

    parser.add_argument(
        '--failfast', '-f',
        action='store_true',
        help='Stop on first failure'
    )

    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )

    args = parser.parse_args()

    # Print header
    print_banner("RemBraille Test Suite")

    print(f"Test Type:    {args.type}")
    print(f"Pattern:      {args.pattern}")
    print(f"Verbosity:    {args.verbose}")
    print(f"Fail Fast:    {args.failfast}")
    print()

    # Discover tests
    suite = discover_tests(args.type, args.pattern)

    # Run tests
    if args.no_color:
        runner = unittest.TextTestRunner(
            verbosity=args.verbose,
            failfast=args.failfast
        )
    else:
        runner = ColoredTextTestRunner(
            verbosity=args.verbose,
            failfast=args.failfast
        )

    print_banner("Running Tests")
    result = runner.run(suite)

    # Print summary
    exit_code = print_summary(result)

    return exit_code


if __name__ == '__main__':
    sys.exit(main())
