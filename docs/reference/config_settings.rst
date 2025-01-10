UTMS allows extensive configuration via its `config.py` file, where you can adjust settings related to time, anchors, synchronization, and more.

Common Configuration Options
----------------------------
- **ntp.servers**: List of NTP servers for synchronization.
- **default_units**: Default time unit for outputs (e.g., `seconds`, `minutes`).
- **time_format**: Defines the format for displaying time (e.g., `ISO 8601`).

Example Configuration
---------------------
The following is an example configuration section for NTP synchronization:

.. code-block:: json

    {
        "ntp": {
            "servers": ["pool.ntp.org", "time.google.com"],
            "sync_interval": 60
        },
        "default_units": "hours",
        "time_format": "ISO8601"
    }

Modifying Configuration
-----------------------
To modify the configuration, use the `utms config set` command:

.. code-block:: bash

    poetry run utms config set ntp.servers[+] "time.windows.com"
