#!/usr/bin/env python3
"""
Test runner script for the YouTube MCP Server.
Provides convenient ways to run different test suites.
"""
import subprocess
import sys
import argparse


def run_unit_tests(coverage=False, verbose=True):
    """Run unit tests (default)."""
    cmd = ['python', '-m', 'pytest', 'test_youtube_client.py', 'test_server.py']

    if coverage:
        cmd.extend(['--cov=youtube_client', '--cov=server', '--cov-report=term-missing'])

    if verbose:
        cmd.append('-v')

    print("Running unit tests...")
    print(f"Command: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd='.')
    return result.returncode


def run_all_tests(coverage=False, verbose=True):
    """Run all tests including slow ones."""
    cmd = ['python', '-m', 'pytest']

    if coverage:
        cmd.extend(['--cov=youtube_client', '--cov=server', '--cov-report=term-missing'])

    if verbose:
        cmd.append('-v')

    print("Running all tests...")
    print(f"Command: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd='.')
    return result.returncode


def main():
    """Parse arguments and run tests."""
    parser = argparse.ArgumentParser(
        description='Run tests for YouTube MCP Server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python run_tests.py              # Run unit tests
  python run_tests.py --coverage   # Run with coverage report
  python run_tests.py --all        # Run all tests
        '''
    )

    parser.add_argument(
        '--coverage', '-c',
        action='store_true',
        help='Run tests with coverage report'
    )

    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Run all tests (including slow/integration)'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Run tests quietly (less output)'
    )

    args = parser.parse_args()

    verbose = not args.quiet

    if args.all:
        return_code = run_all_tests(coverage=args.coverage, verbose=verbose)
    else:
        return_code = run_unit_tests(coverage=args.coverage, verbose=verbose)

    sys.exit(return_code)


if __name__ == '__main__':
    main()
