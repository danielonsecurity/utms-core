import os
import signal
import subprocess
import time
from typing import Dict, Any, List
import pathlib

from utms import UTMSConfig
from utms.core.logger import get_logger

CURRENT_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parents[3]
FRONTEND_DIR = PROJECT_ROOT / "frontend"

logger = get_logger()

SERVICES: Dict[str, Dict[str, Any]] = {
    "api": {
        "cmd": ["uvicorn", "utms.web.main:app", "--host", "0.0.0.0", "--port", "8000"],
        "cwd": str(PROJECT_ROOT),
        "log_file": "api.log",
    },
    "agent": {
        "cmd": ["python", "-m", "utms.core.agent.main"],
        "cwd": str(PROJECT_ROOT),
        "log_file": "agent.log",
    },
    "arduino": {
        "cmd": ["python", "-m", "utms.core.listeners.arduino"],
        "cwd": str(PROJECT_ROOT),
        "log_file": "arduino.log",
    },
    "frontend": {
        "cmd": ["npm", "run", "dev"],
        "cwd": str(FRONTEND_DIR),
        "log_file": "frontend.log"
    }
}

def _get_pid_dir(config: UTMSConfig) -> str:
    """Gets the directory for storing PID files, creating it if necessary."""
    pid_dir = os.path.join(config.utms_dir, "run")
    os.makedirs(pid_dir, exist_ok=True)
    return pid_dir

def _get_pid_file_path(config: UTMSConfig, service_name: str) -> str:
    """Gets the full path to a service's PID file."""
    return os.path.join(_get_pid_dir(config), f"{service_name}.pid")

def is_process_running(pid: int) -> bool:
    """Checks if a process with the given PID is running."""
    if pid <= 0:
        return False
    try:
        # Sending signal 0 to a pid will raise an OSError if the pid is not running,
        # and do nothing otherwise.
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True

def get_service_status(config: UTMSConfig, service_name: str) -> (str, int):
    """
    Checks the status of a service.
    Returns a tuple of (status_string, pid).
    """
    pid_file = _get_pid_file_path(config, service_name)
    if not os.path.exists(pid_file):
        return ("STOPPED", -1)
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
    except (ValueError, FileNotFoundError):
        return ("UNKNOWN", -1) # PID file is corrupted or gone

    if is_process_running(pid):
        return ("RUNNING", pid)
    else:
        # The process is not running, but the PID file exists. This is a stale PID file.
        logger.warning(f"Found stale PID file for service '{service_name}' (PID: {pid}). Cleaning up.")
        os.remove(pid_file)
        return ("STOPPED (stale PID)", -1)


def start_service(config: UTMSConfig, service_name: str, foreground: bool = False):
    """Starts a service either in the foreground or background."""
    if service_name not in SERVICES:
        logger.error(f"Unknown service '{service_name}'. Cannot start.")
        return

    # Before starting, check if it's already running
    status, pid = get_service_status(config, service_name)
    if status == "RUNNING":
        logger.info(f"Service '{service_name}' is already running with PID {pid}. Skipping.")
        return

    service_config = SERVICES[service_name]
    pid_file = _get_pid_file_path(config, service_name)
    
    # We need a log directory within the main config dir
    log_dir = os.path.join(config.utms_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, service_config['log_file'])

    if foreground:
        logger.info(f"Starting service '{service_name}' in the foreground...")
        try:
            # subprocess.run blocks and streams output to the current console.
            # It's perfect for foreground mode.
            subprocess.run(service_config['cmd'], cwd=service_config['cwd'], check=True)
        except subprocess.CalledProcessError:
            logger.error(f"Service '{service_name}' exited with an error.")
        except KeyboardInterrupt:
            logger.info(f"Service '{service_name}' stopped by user (Ctrl+C).")
        except FileNotFoundError:
            logger.error(f"Command not found for service '{service_name}': {service_config['cmd'][0]}")

    else: # Background mode
        logger.info(f"Starting service '{service_name}' in the background...")
        try:
            # Open log files for stdout and stderr
            stdout_log = open(log_path, 'a')
            stderr_log = open(log_path, 'a')

            # Popen runs in the background and immediately returns.
            process = subprocess.Popen(
                service_config['cmd'],
                cwd=service_config['cwd'],
                stdout=stdout_log,
                stderr=stderr_log,
                # Create a new process group to prevent Ctrl+C in the main terminal
                # from killing the background services.
                preexec_fn=os.setsid 
            )
            # Write the new process's PID to the file.
            with open(pid_file, 'w') as f:
                f.write(str(process.pid))
            logger.info(f"Service '{service_name}' started with PID {process.pid}. Logs at: {log_path}")

        except FileNotFoundError:
             logger.error(f"Command not found for service '{service_name}': {service_config['cmd'][0]}")
        except Exception as e:
            logger.error(f"Failed to start service '{service_name}' in background: {e}", exc_info=True)


def stop_service(config: UTMSConfig, service_name: str):
    """Stops a running service."""
    if service_name not in SERVICES:
        logger.error(f"Unknown service '{service_name}'. Cannot stop.")
        return

    status, pid = get_service_status(config, service_name)
    
    if status != "RUNNING":
        logger.info(f"Service '{service_name}' is not running.")
        return
        
    pid_file = _get_pid_file_path(config, service_name)
    
    logger.info(f"Stopping service '{service_name}' (PID: {pid})...")
    try:
        # os.killpg sends the signal to the entire process group, which is safer.
        os.killpg(os.getpgid(pid), signal.SIGTERM)
        # Wait a moment for the process to terminate
        time.sleep(2)

        # Check if it terminated gracefully
        if is_process_running(pid):
            logger.warning(f"Service '{service_name}' did not terminate gracefully. Forcing kill (SIGKILL)...")
            os.killpg(os.getpgid(pid), signal.SIGKILL)
        
        logger.info(f"Service '{service_name}' stopped successfully.")

    except ProcessLookupError:
         logger.warning(f"Process with PID {pid} not found, but PID file existed. It may have crashed.")
    except Exception as e:
        logger.error(f"Error stopping service '{service_name}': {e}", exc_info=True)
    finally:
        # Always clean up the PID file
        if os.path.exists(pid_file):
            os.remove(pid_file)
