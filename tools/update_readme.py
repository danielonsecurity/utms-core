#!/usr/bin/env python3
"""
Module for Automating README File Updates Based on Command Outputs.

This module provides functionality to dynamically update a README file
by replacing placeholders in a template with the output of specified
shell commands. It is especially useful for keeping documentation up-to-date
with the latest output of command-line tools.

Usage
-----
This module can be executed as a script or imported into another Python program.

Features
--------
- Runs shell commands and captures their output.
- Replaces placeholders in a template with command output.
- Optionally wraps the command output in Markdown code blocks.

Functions
---------
- run_command(command: List[str]) -> str:
    Executes a shell command and returns its output.

- update_readme(template: str, output: str, commands: List[Tuple[str, str, bool]]) -> None:
    Updates a README file by replacing placeholders in a template with
    command outputs, optionally wrapping the outputs in code blocks.

Main Script
-----------
When run as a script, this module:
1. Reads a README template file (`README.template.md`) located in the project root.
2. Updates placeholders in the template with the output of specified commands.
3. Writes the updated content to the `README.md` file in the project root.

Example
-------
A typical usage scenario involves defining commands and their corresponding
placeholders, such as:

    commands_and_placeholders = [
        ("utms --help", "%%%UTMS_HELP%%%", True),
        ("utms --version", "%%%UTMS_VERSION%%%", False),
        ("utms --help-prompt", "%%%UTMS_HELP_PROMPT%%%", True),
    ]

These are then passed to the `update_readme` function, which performs the
placeholder replacements.

Dependencies
------------
- Python 3.6 or later.
- Modules: `re`, `subprocess`, `pathlib`.

"""

import re
import subprocess  # nosec
from pathlib import Path
from typing import List, Tuple


def run_command(command: List[str]) -> str:
    """
    Executes a shell command securely, prepending `utms` to the command.

    :param command: List of strings representing the command and its arguments.
    :return: The standard output of the command as a string.
    :raises ValueError: If the command is invalid.
    :raises RuntimeError: If the command execution fails.
    """
    # Prepend 'utms' to the command
    full_command = ["utms"] + command
    print(f"Running command {full_command}")

    try:
        result = subprocess.run(  # nosec
            full_command,
            stdout=subprocess.PIPE,  # Capture only STDOUT
            stderr=subprocess.DEVNULL,  # Suppress STDERR
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command failed: {' '.join(full_command)}") from e


def update_readme(
    template: str,
    output: str,
    commands: List[Tuple[List[str], str, bool]],
    ignore_errors: bool = False,
) -> None:
    """
    Update the README file by replacing placeholders with the output of commands.

    :param template: Path to the README template file with placeholders.
    :param output: Path to write the updated README file.
    :param commands: A list of tuples where each tuple contains:
                        - A list representing the arguments for the `utms` command.
                        - The placeholder to replace in the README.
                        - A boolean indicating whether to wrap the output in a code block.
    :param ignore_errors: If True, ignore command errors and continue processing.
    """
    template_file = Path(template)
    output_file = Path(output)

    # Read the template content
    content = template_file.read_text(encoding="utf-8")

    for command_args, placeholder, wrap_in_code_block in commands:
        try:
            output = run_command(command_args)
        except RuntimeError as e:
            if ignore_errors:
                print(f"Warning: {e}")
                continue
            raise

        # Wrap in a code block if required
        if wrap_in_code_block:
            new_content = f"```bash\n$ {' '.join(['utms'] + command_args)}\n\n{output}\n```"
        else:
            new_content = output

        # Replace the placeholder with the generated content
        placeholder_pattern = rf"{re.escape(placeholder)}"
        content = re.sub(placeholder_pattern, new_content, content)

    # Write the updated content to the output file
    output_file.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    # Paths to the template and output README files
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    template_path = project_root / "README.template.md"
    output_path = project_root / "README.md"

    print("Generating README.md from template...")

    # List of commands and their corresponding placeholders, along with the wrap flag
    commands_and_placeholders = [
        (["--help"], "%%%UTMS_HELP%%%", True),
        (["--version"], "%%%UTMS_VERSION%%%", False),
        (["daytime", "convert", "15:30:25"], "%%%UTMS_DCONV1%%%", True),
        (["daytime", "convert", "1.2.205"], "%%%UTMS_DCONV2%%%", True),
        (["unit", "convert", "5", "h"], "%%%UTMS_CONV_5H%%%", True),
        (["unit", "convert", "1.25e7", "s"], "%%%UTMS_CONV_125S%%%", True),
        (["unit", "convert", "1.25e7", "s", "h"], "%%%UTMS_CONV_125SH%%%", True),
        (["unit"], "%%%UTMS_UNITS%%%", True),
        (["unit", "table", "h", "3", "5"], "%%%UTMS_UNITS_SHORT%%%", True),
        (["resolve", "today"], "%%%UTMS_RESOLVE_TODAY%%%", True),
        (["resolve", "beginning of world war 1"], "%%%UTMS_RESOLVE_WW2%%%", True),
        (["resolve", "extinction of dinosaurs"], "%%%UTMS_RESOLVE_EXTINCTION%%%", True),
        (["resolve", "fall of roman empire"], "%%%UTMS_RESOLVE_ROMAN%%%", True),
    ]

    # Update the README using the template
    update_readme(str(template_path), str(output_path), commands_and_placeholders)
