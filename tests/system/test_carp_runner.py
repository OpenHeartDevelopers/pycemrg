#!/usr/bin/env python3
"""
Test script for CarpRunner class.

This script validates that CarpRunner can properly load a CARPentry installation
and execute commands. It uses the 'cusummary' command to display information
about the CARPentry installation.

Usage:
    python test_carp_runner.py /path/to/carpentry_bundle/config.sh
    
    # Or let it auto-discover:
    python test_carp_runner.py --auto
"""

import sys
import logging
import argparse
from pathlib import Path

# Adjust this import based on your actual package structure
try:
    from pycemrg.system import CommandRunner, CarpRunner
    from pycemrg.system.carp_runner import CarpEnvironmentError
except ImportError as e:
    print(f"Error: Could not import pycemrg modules: {e}")
    print("Make sure pycemrg is in your PYTHONPATH")
    sys.exit(1)


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='[pycemrg:CarpRunner:%(name)s] %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)


def test_carp_installation(config_path: Path, logger: logging.Logger) -> bool:
    """
    Test CARPentry installation by running cusummary.
    
    Args:
        config_path: Path to config.sh file
        logger: Logger instance
        
    Returns:
        True if test successful, False otherwise
    """
    logger.info("="*70)
    logger.info("CarpRunner Test Script")
    logger.info("="*70)
    logger.info(f"Config file: {config_path}")
    logger.info("")
    
    try:
        # Initialize CommandRunner
        logger.info("Step 1: Initializing CommandRunner...")
        runner = CommandRunner(logger=logger)
        logger.info("CommandRunner initialized")
        logger.info("")
        
        # Initialize CarpRunner
        logger.info("Step 2: Initializing CarpRunner...")
        carp = CarpRunner(
            runner=runner,
            carp_config_path=config_path,
            logger=logger
        )
        logger.info("CarpRunner initialized")
        logger.info(f"  Installation root: {carp.installation_root}")
        logger.info("")
        
        # Display environment info
        logger.info("Step 3: Loading CARPentry environment...")
        env = carp.carp_env
        logger.info(f"Environment loaded with {len(env)} variables")
        logger.info("")
        
        # Show key environment variables
        logger.info("Key CARPentry environment variables:")
        key_vars = [
            'CARPENTRY_LICENSE',
            'CARPUTILS_SETTINGS',
            'VIRTUAL_ENV',
            'OPAL_PREFIX'
        ]
        for var in key_vars:
            value = env.get(var, 'Not set')
            logger.info(f"  {var}: {value}")
        logger.info("")
        
        # Check for important paths
        logger.info("Step 4: Checking CARPentry paths...")
        license_path = carp.get_license_path()
        settings_path = carp.get_carputils_settings_path()
        
        if license_path:
            logger.info(f"  License file: {license_path}")
            if license_path.exists():
                logger.info(f"    License file exists")
            else:
                logger.warning(f"    License file not found!")
        
        if settings_path:
            logger.info(f"  Carputils settings: {settings_path}")
            if settings_path.exists():
                logger.info(f"    Settings file exists")
            else:
                logger.warning(f"    Settings file not found!")
        logger.info("")
        
        # Validate key commands
        logger.info("Step 5: Validating CARPentry commands...")
        commands_to_check = [
            'cusummary',
            'openCARP',
            'meshtool',
            'meshalyzer'
        ]
        
        available_commands = []
        missing_commands = []
        
        for cmd in commands_to_check:
            if carp.validate_command_exists(cmd):
                available_commands.append(cmd)
                logger.info(f"  {cmd} found")
            else:
                missing_commands.append(cmd)
                logger.warning(f"  ✗ {cmd} not found")
        
        logger.info("")
        logger.info(f"Available: {len(available_commands)}/{len(commands_to_check)} commands")
        logger.info("")
        
        # Run cusummary
        if 'cusummary' in available_commands:
            logger.info("Step 6: Running 'cusummary' command...")
            logger.info("-"*70)
            try:
                output = carp.run(['cusummary'])
                print(output)  # Print cusummary output directly to stdout
                logger.info("-"*70)
                logger.info("cusummary executed successfully")
            except Exception as e:
                logger.error(f"✗ Failed to run cusummary: {e}")
                return False
        else:
            logger.error("✗ cusummary command not available, cannot complete test")
            return False
        
        logger.info("")
        logger.info("="*70)
        logger.info("Test completed successfully!")
        logger.info("="*70)
        return True
        
    except CarpEnvironmentError as e:
        logger.error(f"CARPentry environment error: {e}")
        return False
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return False


def main(args):
    """Main entry point."""
        
    # Setup logging
    logger = setup_logging(args.verbose)
    
    # Determine config path
    config_path = args.config_path
        
    # Validate config path
    if not config_path.exists():
        logger.error(f"Config file does not exist: {config_path}")
        sys.exit(1)
    
    # Run test
    success = test_carp_installation(config_path, logger)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Test CarpRunner by running cusummary command',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with explicit config path
  python test_carp_runner.py /home/user/carpentry_bundle/config.sh
  
  # Try to auto-discover installation
  python test_carp_runner.py --auto
  
  # Verbose output
  python test_carp_runner.py --auto --verbose
        """
    )
    
    parser.add_argument(
        '--config-path', 
        required=True,
        type=Path,
        help='Path to CARPentry config.sh file'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose debug logging'
    )
    
    args = parser.parse_args()

    main(args)