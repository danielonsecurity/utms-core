Error Handling
==============

UTMS provides error handling mechanisms for common scenarios like missing keys, invalid input, and system time issues.

Common Errors
-------------
- **KeyError**: Raised when a configuration key is missing or invalid.
    - Example: `KeyError: 'ntp.servers'`
- **ValueError**: Raised when an invalid value is provided (e.g., out-of-range index).
    - Example: `ValueError: Index out of range`
- **TypeError**: Raised when an operation is performed on incompatible data types.
    - Example: `TypeError: Expected a list, got a string`

Handling Errors in Scripts
--------------------------
UTMS provides useful error messages. For example, if you attempt to use a non-existent configuration key:

.. code-block:: bash

    poetry run utms config print nonexistent_key
    Output: KeyError: 'nonexistent_key'

To handle errors in Python scripts, use `try-except` blocks:

.. code-block:: python

    try:
        utms.config.get_value("ntp.servers")
    except KeyError as e:
        print(f"Error: {e}")
