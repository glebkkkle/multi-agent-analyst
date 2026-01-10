# src/multi_agent_analyst/logging.py
import logging
import sys
import os
from datetime import datetime

def setup_logging():
    system_logger = logging.getLogger("multi_agent_analyst")
    system_logger.setLevel(logging.INFO)
    system_logger.propagate = False
    if system_logger.handlers:
        system_logger.handlers.clear()
    system_handler = logging.StreamHandler(sys.stdout)
    system_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
    )
    system_logger.addHandler(system_handler)
    
    # Trace logger with both console and file output
    trace_logger = logging.getLogger("request_trace")
    trace_logger.setLevel(logging.INFO)
    trace_logger.propagate = False
    if trace_logger.handlers:
        trace_logger.handlers.clear()
    
    # Console handler
    trace_handler = logging.StreamHandler(sys.stdout)
    trace_handler.setFormatter(logging.Formatter("%(message)s"))
    trace_logger.addHandler(trace_handler)
    
    # File handler - create logs directory if it doesn't exist
    log_dir = "logs/traces"
    os.makedirs(log_dir, exist_ok=True)
    
    # Create a new file for each session/day
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    trace_file = os.path.join(log_dir, f"trace_{timestamp}.json")
    
    file_handler = logging.FileHandler(trace_file, mode='a')
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    trace_logger.addHandler(file_handler)
    
    return system_logger, trace_logger

logger, trace_logger = setup_logging()