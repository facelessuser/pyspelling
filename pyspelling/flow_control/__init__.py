"""Flow control."""
from wcmatch import fnmatch


ALLOW = 0
SKIP = 1
HALT = 2


class FlowControl:
    """Control flow of objects in the pipeline."""

    FNMATCH_FLAGS = fnmatch.N | fnmatch.B

    def __init__(self, config):
        """Initialization."""

        self.allow = config.get('allow', ['*'])
        self.halt = config.get('halt', [])
        self.skip = config.get('skip', [])

    def adjust_flow(self, category):
        """Adjust the flow of source control objects."""

        status = SKIP
        for allow in self.allow:
            if fnmatch.fnmatch(category, allow, flags=self.FNMATCH_FLAGS):
                status = ALLOW
                for skip in self.skip:
                    if fnmatch.fnmatch(category, skip, flags=self.FNMATCH_FLAGS):
                        status = SKIP
                for halt in self.halt:
                    if fnmatch.fnmatch(category, halt, flags=self.FNMATCH_FLAGS):
                        status = HALT
                if status != ALLOW:
                    break
        return status


def get_filter():
    """Get flow controller."""

    return FlowControl
