"""Flow control."""
import warnings

ALLOW = 0
SKIP = 1
HALT = 2


class FlowControl(object):
    """Control flow of objects in the pipeline."""

    def __init__(self, options):
        """Initialization."""

        self.config = self.get_default_config()
        if self.config is None:
            warnings.warn(
                "'{}' did not provide a default config. ".format(self.__class__.__name__) +
                "All plugins in the future should provide a default config.",
                category=FutureWarning,
                stacklevel=1
            )
            self.config = options
        else:
            self.override_config(options)
        self.setup()

    def get_default_config(self):
        """Get default configuration."""

        return None

    def setup(self):
        """Setup."""

    def override_config(self, options):
        """Override the default configuration."""

        for k, v in options.items():
            if k not in self.config:
                raise ValueError("'{}' is not a valid option for '{}'".format(k, self.__class__.__name__))
            self.validate_options(k, v)
            self.config[k] = v

    def validate_options(self, k, v):
        """Validate options."""

    def reset(self):
        """Reset anything needed on each iteration."""

    def _run(self, category):
        """Run as chained plugin."""

        return self.adjust_flow(category)

    def adjust_flow(self, category):
        """Adjust the flow of source control objects."""

        return ALLOW
