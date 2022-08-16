# -*- coding: utf-8 -*-
"""Command line interface `aiida-pseudo`."""
from aiida.cmdline.params import options, types
from aiida.cmdline.groups.verdi import VerdiCommandGroup
import click


@click.group('aiida-pseudo', cls=VerdiCommandGroup, context_settings={'help_option_names': ['-h', '--help']})
@options.PROFILE(type=types.ProfileParamType(load_profile=True), expose_value=False)
def cmd_root():
    """CLI for the ``aiida-pseudo`` plugin."""
