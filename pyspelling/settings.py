"""Settings."""
from __future__ import unicode_literals
import yaml
import codecs
import os
from . import util

__all__ = ("yaml_load", "read_config")


def yaml_load(source, loader=yaml.Loader):
    """
    Wrap PyYaml's loader so we can extend it to suit our needs.

    Load all strings as Unicode: http://stackoverflow.com/a/2967461/3609487.
    """

    def construct_yaml_str(self, node):
        """Override the default string handling function to always return Unicode objects."""
        return self.construct_scalar(node)

    class Loader(loader):
        """Define a custom loader to leave the global loader unaltered."""

    # Attach our Unicode constructor to our custom loader ensuring all strings
    # will be Unicode on translation.
    Loader.add_constructor('tag:yaml.org,2002:str', construct_yaml_str)

    return yaml.load(source, Loader)


def read_config(file_name):
    """Read configuration."""

    config = {}
    for name in (['.pyspelling.yml', '.spelling.yml'] if not file_name else [file_name]):
        if os.path.exists(name):
            if not file_name and name == '.spelling.yml':
                util.warn_deprecated(
                    "Using '.spelling.yml' as the default is deprecated. Default config is now '.pyspelling.yml'"
                )
            with codecs.open(name, 'r', encoding='utf-8') as f:
                config = yaml_load(f.read())
            break
    return config
