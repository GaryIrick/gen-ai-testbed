import logging
import json


class InMemoryHandler(logging.Handler):
    messages = []

    def __init__(self):
        super().__init__()

    def emit(self, record):
        self.messages.append(record)

    def get_logs(self):
        return self.messages


def get_in_memory_logger():
    logger = logging.getLogger("json_logger")
    logger.setLevel(logging.DEBUG)

    in_memory_handler = InMemoryHandler()
    logger.addHandler(in_memory_handler)

    return logger, in_memory_handler
