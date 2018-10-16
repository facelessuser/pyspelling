"""Settings."""
from __future__ import unicode_literals
import yaml
import codecs

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
    with codecs.open(file_name, 'r', encoding='utf-8') as f:
        config = yaml_load(f.read())
    return config
