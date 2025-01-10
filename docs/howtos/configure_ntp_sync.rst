Configuring NTP Synchronization
===============================

This guide explains how to synchronize your system's time with NTP servers using UTMS.

Prerequisites
-------------
- UTMS installed and configured.
- Administrative privileges for system time adjustments.

Steps
-----
1. **Verify NTP Server Settings**:
   List the configured NTP servers:

   .. code-block:: bash

      poetry run utms config print ntp.servers

2. **Add or Update NTP Servers**:
   Add a new NTP server:

   .. code-block:: bash

      poetry run utms config set ntp.servers[+] "pool.ntp.org"

3. **Perform a Time Sync**:
   Run the sync command:

   .. code-block:: bash

      poetry run utms ntp sync

   Output:

   .. code-block::

      System time synchronized with NTP servers.

4. **Schedule Regular Syncs**:
   Use a cron job or systemd timer to automate synchronization:

   .. code-block:: bash

      poetry run utms ntp sync --cron
