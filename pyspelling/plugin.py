"""Base plugin class."""
from collections import OrderedDict
import warnings


class Plugin:
    """Base plugin."""

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
            # Reject names not in the default configuration
            if k not in self.config:
                raise KeyError("'{}' is not a valid option for '{}'".format(k, self.__class__.__name__))
            self.validate_options(k, v)
            self.config[k] = v

    def validate_options(self, k, v):
        """Validate options."""

        args = [self.__class__.__name__, k]
        # Booleans
        if isinstance(self.config[k], bool) and not isinstance(v, bool):
            raise ValueError("{}: option '{}' must be a bool type.".format(*args))
        # Strings
        elif isinstance(self.config[k], str) and not isinstance(v, str):
            raise ValueError("{}: option '{}' must be a str type.".format(*args))
        # Integers (whole floats allowed)
        elif (
            isinstance(self.config[k], int) and
            (not isinstance(v, int) and not (isinstance(v, float) and v.is_integer()))
        ):
            raise ValueError("{}: option '{}' must be a int type.".format(*args))
        # Floats (integers allowed)
        elif isinstance(self.config[k], float) and not isinstance(v, (int, float)):
            raise ValueError("{}: option '{}' must be a float type.".format(*args))
        # Basic iterables (list, tuple, sets)
        elif isinstance(self.config[k], (list, tuple, set)) and not isinstance(v, list):
            raise ValueError("{}: option '{}' must be a float type.".format(*args))
        # Dictionaries
        elif isinstance(self.config[k], (dict, OrderedDict)) and not isinstance(v, (dict, OrderedDict)):
            raise ValueError("{}: option '{}' must be a dict type.".format(*args))

    def reset(self):
        """Reset anything needed on each iteration."""
