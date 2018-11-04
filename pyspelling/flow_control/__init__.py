"""Flow control."""

ALLOW = 0
SKIP = 1
HALT = 2


class FlowControl(object):
    """Control flow of objects in the pipeline."""

    def __init__(self, config):
        """Initialization."""

    def reset(self):
        """Reset anything needed on each iteration."""

    def _run(self, category):
        """Run as chained plugin."""

        return self.adjust_flow(category)

    def adjust_flow(self, category):
        """Adjust the flow of source control objects."""

        return ALLOW
