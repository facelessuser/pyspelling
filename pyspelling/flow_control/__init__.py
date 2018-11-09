"""Flow control."""
from .. import plugin

ALLOW = 0
SKIP = 1
HALT = 2


class FlowControl(plugin.Plugin):
    """Control flow of objects in the pipeline."""

    def __init__(self, options):
        """Initialization."""

        super().__init__(options)
        self.setup()

    def _run(self, category):
        """Run as chained plugin."""

        return self.adjust_flow(category)

    def adjust_flow(self, category):
        """Adjust the flow of source control objects."""

        return ALLOW
