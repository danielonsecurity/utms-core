Customizing Command Aliases
===========================

This guide explains how to create custom aliases for frequently used commands.

Prerequisites
-------------
- Familiarity with UTMS CLI.

Steps
-----
1. **List Current Aliases**:
   Display existing aliases:

   .. code-block:: bash

      poetry run utms alias list

2. **Create a New Alias**:
   Add an alias for a long command:

   .. code-block:: bash

      poetry run utms alias set "sync" "ntp sync"

3. **Test the Alias**:
   Use the alias instead of the full command:

   .. code-block:: bash

      poetry run utms sync

4. **Delete an Alias**:
   Remove an alias no longer needed:

   .. code-block:: bash

      poetry run utms alias delete "sync"
