"""Wildcard flow control."""
from .. import flow_control
from wcmatch import fnmatch


class WildcardFlowControl(flow_control.FlowControl):
    """Control flow of objects in the pipeline with wildcard patterns."""

    FNMATCH_FLAGS = fnmatch.N | fnmatch.B | fnmatch.I

    def __init__(self, config):
        """Initialization."""

        self.allow = config.get('allow', ['*'])
        self.halt = config.get('halt', [])
        self.skip = config.get('skip', [])

    def match(self, category, pattern):
        """Match the category."""

        return fnmatch.fnmatch(category, fnmatch.fnsplit(pattern, flags=self.FNMATCH_FLAGS), flags=self.FNMATCH_FLAGS)

    def adjust_flow(self, category):
        """Adjust the flow of source control objects."""

        status = flow_control.SKIP
        for allow in self.allow:
            if self.match(category, allow):
                status = flow_control.ALLOW
                for skip in self.skip:
                    if self.match(category, skip):
                        status = flow_control.SKIP
                for halt in self.halt:
                    if self.match(category, halt):
                        status = flow_control.HALT
                if status != flow_control.ALLOW:
                    break
        return status


def get_plugin():
    """Get flow controller."""

    return WildcardFlowControl
