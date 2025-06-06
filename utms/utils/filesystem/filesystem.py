import re
import unicodedata


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """
    Sanitizes a string to be used as a valid filename.
    - Converts to lowercase.
    - Normalizes unicode characters.
    - Replaces spaces and common problematic characters with a replacement string (default: '_').
    - Removes any characters not in a safe set (alphanumeric, underscore, hyphen, dot).
    - Prevents names that are just dots or empty.
    """
    if not isinstance(filename, str):
        filename = str(filename)

    filename = filename.lower().strip()

    # Normalize unicode characters (e.g., accented characters to their base)
    filename = unicodedata.normalize("NFKD", filename).encode("ascii", "ignore").decode("ascii")

    # Replace spaces and common separators with the replacement character
    filename = re.sub(r"[\s\/\\]+", replacement, filename)

    # Keep only alphanumeric, underscore, hyphen, and dot. Replace others.
    # Ensure the replacement character itself is allowed in the final step or it will be removed.
    # Here, we assume replacement is typically '_' or '-' which are in the allowed set.
    filename = re.sub(rf"[^\w.{replacement}-]", "", filename)  # \w is [a-zA-Z0-9_]

    # Prevent names like "..", ".", or just consisting of replacements
    filename = re.sub(
        rf"^[{replacement}]+|[{replacement}]+$", "", filename
    )  # Trim leading/trailing replacements
    filename = re.sub(
        rf"[{replacement}]{{2,}}", replacement, filename
    )  # Collapse multiple replacements

    if not filename or filename == "." or filename == "..":
        return "invalid_name"  # Or raise an error, or generate a unique ID

    max_len = 100
    if len(filename) > max_len:
        name_part, dot, ext_part = filename.rpartition(".")
        if dot:  # Has an extension
            name_part = name_part[: max_len - len(ext_part) - 1]
            filename = name_part + dot + ext_part
        else:
            filename = filename[:max_len]

    return filename if filename else "default_sanitized"
