Using AI to generate precise ISO 8601 timestamps
================================================

UTMS integrates with the Gemini AI model to generate ISO 8601 timestamps based on natural language input. This tutorial covers the process.

Prerequisites
-------------
- Gemini API key configured in UTMS.
- Internet connectivity for API requests.

Steps
-----
1. **Verify API Configuration**:
   Ensure the Gemini API key is set:

   .. code-block:: bash

      poetry run utms config print gemini.api_key

2. **Generate a Timestamp**:
   Use the `ai timestamp` command to create a timestamp:

   .. code-block:: bash

      poetry run utms ai timestamp "next Friday at 3 PM"

   Output:

   .. code-block::

      2025-01-17T15:00:00Z

3. **Refine with Context**:
   Provide additional details to improve precision:

   .. code-block:: bash

      poetry run utms ai timestamp "6 months from project_deadline"

4. **Handle Errors**:
   If the command fails, troubleshoot by:
   - Checking your API key validity.
   - Verifying the input syntax.

This tutorial helps you unlock the power of AI for time management.
