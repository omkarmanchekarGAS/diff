from os import system
import subprocess

from logger.log_groups import UserDefinedLogGroups, LogPriority

class Logger:
    def __init__(self, tag):
        self.tag = tag

    def log(self, message, priority: str = LogPriority.NOTICE):
        """Writes a log to logread, logged at /tmp/log/syslog
        """
        system(f"logger -p {priority} -t {self.tag} \"{str(message)}\"")

    def retrieve(self, tag: str):
        """
        Retrieves logs based on matching content, can be used to retrieve logs based on tag
        """
        if not tag or tag == UserDefinedLogGroups.ALL:
            return subprocess.check_output([f"logread"]).decode("utf-8");

        logs = subprocess.check_output(["logread", "-e", tag]).decode("utf-8");
        return logs