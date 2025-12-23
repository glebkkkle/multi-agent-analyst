# src/multi_agent_analyst/logging.py
import logging
import sys

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

    trace_logger = logging.getLogger("request_trace")
    trace_logger.setLevel(logging.INFO)
    trace_logger.propagate = False

    if trace_logger.handlers:
        trace_logger.handlers.clear()

    trace_handler = logging.StreamHandler(sys.stdout)
    trace_handler.setFormatter(logging.Formatter("%(message)s"))
    trace_logger.addHandler(trace_handler)

    return system_logger, trace_logger


logger, trace_logger = setup_logging()
