Creating and managing time anchors
==================================

Time anchors are a core concept in UTMS, allowing you to manage and calculate time references efficiently. This tutorial demonstrates how to create, update, and delete anchors.

Prerequisites
-------------
- UTMS installed and configured.

Steps
-----
1. **Create a Time Anchor**:
   Use the `anchor create` command to define a new anchor:

   .. code-block:: bash

      poetry run utms anchor create "start_of_sprint" "2025-01-15T09:00:00Z"

   Verify creation:

   .. code-block:: bash

      poetry run utms anchor list

2. **Update an Existing Anchor**:
   Modify the date or time of an anchor:

   .. code-block:: bash

      poetry run utms anchor update "start_of_sprint" "2025-01-16T10:00:00Z"

3. **Delete an Anchor**:
   Remove an anchor when it's no longer needed:

   .. code-block:: bash

      poetry run utms anchor delete "start_of_sprint"

4. **Advanced Features**:
   - Break down an anchor into components:

   .. code-block:: bash

        poetry run utms anchor breakdown "project_deadline"
