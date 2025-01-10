Commands Reference
==================

UTMS offers a command-line interface for interacting with various components of the system. Below is a detailed breakdown of the available commands.

List of Commands
-----------------
- **`config`**: Manage configuration settings.
    - `set`: Modify a configuration setting.
    - `print`: Display configuration.
- **`ntp`**: Control NTP synchronization.
    - `sync`: Synchronize the system time with NTP servers.
    - `status`: Display synchronization status.
- **`anchor`**: Manage time anchors.
    - `create`: Create a new time anchor.
    - `list`: List all created anchors.
    - `diff`: Calculate the difference between two anchors.
    - `delete`: Remove an anchor.
- **`unit`**: Manage time unit conversions.
    - `convert`: Convert time between different units.
    - `validate`: Ensure a unit is valid.

Example Usage
-------------
1. **View configuration**:

   .. code-block:: bash

      poetry run utms config print

2. **Sync system time**:

   .. code-block:: bash

      poetry run utms ntp sync

3. **Create a time anchor**:

   .. code-block:: bash

      poetry run utms anchor create "start_of_sprint" "2025-01-10T09:00:00"

4. **Convert time units**:

   .. code-block:: bash

      poetry run utms unit convert 3600 seconds to hours
