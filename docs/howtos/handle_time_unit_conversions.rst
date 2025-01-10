Handling Time Unit Conversions
==============================

This guide demonstrates how to convert between time units using UTMS.

Prerequisites
-------------
- UTMS installed.

Steps
-----
1. **Convert Between Units**:
   Use the `unit convert` command:

   .. code-block:: bash

      poetry run utms unit convert 3600 seconds to hours

   Output:

   .. code-block::

      1 hour.

2. **Convert with Anchors**:
   Combine with time anchors:

   .. code-block:: bash

      poetry run utms anchor diff "start_of_sprint" "project_deadline" --unit days

3. **Set Default Units**:
   Configure default units for results:

   .. code-block:: bash

      poetry run utms config set default_units "days"

4. **Validate Units**:
   Ensure compatibility of units:

   .. code-block:: bash

      poetry run utms unit validate "minutes"
