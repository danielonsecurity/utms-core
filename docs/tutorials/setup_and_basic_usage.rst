Setting up and using UTMS for the first time
============================================

This tutorial walks you through the process of installing UTMS, configuring it for the first time, and executing basic commands.

Prerequisites
-------------
- Python 3.12 installed on your system.
- Poetry package manager installed.

Steps
-----
1. **Install UTMS**:
   Clone the repository and set up the virtual environment:

   .. code-block:: bash

      git clone https://github.com/yourusername/utms.git
      cd utms
      poetry install

2. **Verify Installation**:
   Check that the UTMS CLI is functional:

   .. code-block:: bash

      poetry run utms --help

3. **Configure UTMS**:
   Open the configuration file and set your preferred values:

   .. code-block:: bash

      poetry run utms config edit

   Key settings to update:
   - Gemini API key
   - Default time units

4. **Run a Basic Command**:
   Test a basic time anchor command:

   .. code-block:: bash

      poetry run utms anchor create "project_deadline" "2025-12-31T23:59:59Z"


   Output:
   .. code-block::

      Anchor 'project_deadline' created for 2025-12-31T23:59:59Z.

Congratulations! You've successfully set up UTMS and executed your first command.
