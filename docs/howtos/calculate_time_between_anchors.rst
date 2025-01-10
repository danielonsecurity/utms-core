Calculating Time Between Two Anchors
====================================

Learn how to compute the duration between two time anchors.

Prerequisites
-------------
- At least two time anchors created.

Steps
-----
1. **List Available Anchors**:
   View all anchors:

   .. code-block:: bash

      poetry run utms anchor list

2. **Calculate the Difference**:
   Use the `anchor diff` command:

   .. code-block:: bash

      poetry run utms anchor diff "start_of_sprint" "project_deadline"

   Output:

   .. code-block::

      Time difference: 16 days, 4 hours, 30 minutes.

3. **Convert the Result**:
   Convert the result to another unit (e.g., hours):

   .. code-block:: bash

      poetry run utms anchor diff "start_of_sprint" "project_deadline" --unit hours
