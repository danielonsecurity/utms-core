"""
This module serves as the entry point for running the UTM's Command Line Interface (CLI).

It imports the `main` function from the `utms.cli` module and invokes it when the module is
executed as a standalone script.

Usage:
    python <this_module>.py

This will run the UTM CLI as defined in the `main` function of the `utms.cli` module.
"""

from utms.cli.shell import main

main()
