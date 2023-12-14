import logging


class WordReplacerFilter(logging.Filter):
    def filter(self, record):
        record.msg = record.msg.replace("flow", "action")
        record.msg = record.msg.replace("Flow", "Action")
        return True
