#!/usr/bin/env python3
"""
Main entry point for Voice Control Application with stability fixes
"""

import argparse
import logging
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from voice_control.core.resource_manager import get_resource_manager
from voice_control.core.error_handler import get_error_handler, safe_execute
from voice_control.system.service_manager import ServiceManager


def setup_logging(level: str = "INFO", daemon: bool = False):
    """Setup logging configuration"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    if daemon:
        # For daemon mode, log to file
        log_dir = Path.home() / ".local/share/voice-control/logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "voice-control.log"
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    else:
        # For interactive mode, log to console
        logging.basicConfig(
            level=log_level,
            format='%(levelname)s: %(message)s'
        )


def main():
    """Main application entry point with stability fixes"""
    parser = argparse.ArgumentParser(description="Voice Control Application")
    parser.add_argument("--daemon", action="store_true", 
                       help="Run as daemon service")
    parser.add_argument("--log-level", default="INFO",
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Set logging level")
    parser.add_argument("--service", choices=["install", "uninstall", "start", "stop", "status"],
                       help="Service management commands")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.daemon)
    logger = logging.getLogger(__name__)
    
    # Initialize resource manager and error handler
    resource_manager = get_resource_manager()
    error_handler = get_error_handler()
    
    logger.info("Starting Voice Control Application with stability fixes")
    
    try:
        # Handle service management commands
        if args.service:
            return handle_service_command(args.service)
        
        # Import and run the original voice control logic
        # This is wrapped with our error handling
        return run_voice_control_safely(args, resource_manager, error_handler)
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down gracefully...")
        return 0
    except Exception as e:
        logger.critical(f"Critical error in main: {e}", exc_info=True)
        return 1
    finally:
        # Ensure cleanup
        resource_manager.cleanup_all()


def handle_service_command(command: str) -> int:
    """Handle service management commands"""
    logger = logging.getLogger(__name__)
    service_mgr = ServiceManager()
    
    try:
        if command == "install":
            success = service_mgr.setup_complete_service()
        elif command == "uninstall":
            success = service_mgr.uninstall_user_service()
        elif command == "start":
            success = service_mgr.start_service()
        elif command == "stop":
            success = service_mgr.stop_service()
        elif command == "status":
            status = service_mgr.get_service_status()
            print(f"Service Status:")
            print(f"  Installed: {status['installed']}")
            print(f"  Enabled: {status['enabled']}")
            print(f"  Running: {status['running']}")
            if status['error']:
                print(f"  Error: {status['error']}")
            success = True
        else:
            logger.error(f"Unknown service command: {command}")
            success = False
            
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"Service command failed: {e}")
        return 1


@safe_execute(get_error_handler(), "voice_control_main")
def run_voice_control_safely(args, resource_manager, error_handler):
    """Run the main voice control logic with error handling"""
    logger = logging.getLogger(__name__)
    
    try:
        # Import the voice control engine
        from voice_control.core.engine import VoiceControlEngine
        
        # Create and configure the engine
        engine = VoiceControlEngine(
            resource_manager=resource_manager,
            error_handler=error_handler,
            daemon_mode=args.daemon
        )
        
        # Register cleanup
        resource_manager.add_cleanup_handler(engine.shutdown)
        
        # Start the engine
        logger.info("Starting voice control engine...")
        engine.start()
        
        if args.daemon:
            # In daemon mode, run indefinitely
            logger.info("Running in daemon mode...")
            engine.run_daemon()
        else:
            # In interactive mode, run until interrupted
            logger.info("Running in interactive mode (Ctrl+C to stop)...")
            engine.run_interactive()
        
        return 0
        
    except ImportError as e:
        # If the new engine doesn't exist yet, fall back to original
        logger.warning(f"New engine not available ({e}), using original voice-control logic")
        return run_original_voice_control(args)
    except Exception as e:
        logger.error(f"Engine failed to start: {e}")
        return run_original_voice_control(args)


def run_original_voice_control(args):
    """Run the original voice-control script logic"""
    logger = logging.getLogger(__name__)
    
    try:
        # Import and execute the original voice-control script
        # This is a temporary fallback until we fully integrate
        original_script = Path(__file__).parent.parent / "voice-control"
        
        if original_script.exists():
            logger.info("Executing original voice-control script...")
            import subprocess
            
            cmd = [sys.executable, str(original_script)]
            if args.daemon:
                cmd.append("--daemon")
                
            result = subprocess.run(cmd)
            return result.returncode
        else:
            logger.error("Original voice-control script not found")
            return 1
            
    except Exception as e:
        logger.error(f"Failed to run original voice-control: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())