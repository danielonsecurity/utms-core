Time Anchors Reference
======================

Time anchors are fundamental to UTMS. They allow you to create and manipulate reference points in time. These anchors can be used for calculating differences, making comparisons, and performing other time-related operations.

Anchor Commands
---------------
- **`create`**: Create a new time anchor.
    - Example: `poetry run utms anchor create "start_of_sprint" "2025-01-10T09:00:00"`
- **`list`**: List all created anchors.
    - Example: `poetry run utms anchor list`
- **`diff`**: Calculate the difference between two anchors.
    - Example: `poetry run utms anchor diff "start_of_sprint" "project_deadline"`
- **`delete`**: Remove an anchor.
    - Example: `poetry run utms anchor delete "start_of_sprint"`

Time Anchor Example
-------------------
1. **Create anchor**:

   .. code-block:: bash

      poetry run utms anchor create "project_deadline" "2025-01-20T17:00:00"

2. **View all anchors**:

   .. code-block:: bash

      poetry run utms anchor list

3. **Calculate time difference**:

   .. code-block:: bash

      poetry run utms anchor diff "start_of_sprint" "project_deadline" --unit days
