Setting up and using UTMS for the first time
============================================

This tutorial walks you through the process of installing UTMS,
configuring it for the first time, and executing basic commands.

Prerequisites
-------------
- Python 3.10 or higher installed on your system.
- `Python PIP`_ available
- Google account available (for Gemini API)  

Steps
-----
1. **Install UTMS**:
   Make sure you have PIP available, and install UTMS from PyPi:

   .. code-block:: console

      $ pip install utms		   

2. **Verify Installation**:
   Check that the UTMS CLI is functional:

   .. code-block:: console

      $ utms --version
      0.1.10

      $ utms --help
      usage: utms [-h] [--version] [--debug]
                  {config,unit,daytime,resolve,anchor,clock} ...
      
      UTMS CLI version 0.1.10
      
      positional arguments:
        {config,unit,daytime,resolve,anchor,clock}
                              Main commands
          <config>              config management
          unit                unit management
          daytime             daytime management
          resolve             resolve management
          anchor              anchor management
          clock               clock management
      
      options:
        -h, --help            show this help message and exit
        --version             Show UTMS version
        --debug               Enter Python's PDB


3. **Configure UTMS**:
   To resolve arbitrary strings to dates, you need to use the Gemini API. `Create an Gemini API key here <Gemini API key_>`_  and configure it within UTMS:

   .. code-block:: console

      $ utms config set gemini.api_key YOUR_API_KEY
      Configuration for 'gemini.api_key' updated to 'YOUR_API_KEY'

4. **Run a Basic Command**:
   Test a basic command to see if UTMS works with Gemini:

   .. code-block:: console

      $ utms resolve end of ww2

   Output (yours may vary depending on configured :term:`Anchors` and :term:`Units`):

   .. code-block::

      AI: 1945-09-02T00:00:00+00:00
      
      NT: Now Time (2025-01-08 20:18:11)
        - 79.355 Y
      mT: Millennium Time (2000-01-01)
        - 54.331 Y
        - 54 Y             120 d            22 h             6 m              31.680 s
        - 1 GS             714 MS           521 KS           600 s
      HE: Human Era
        + 11944.691 Y
        + 376 GS           937 MS           746 KS           423 s
      UT: Unix Time (1970-01-01)
        - 767836800 s
        - 24.332 Y
        - 767 MS           836 KS           800 s            0E+3 ms
        - 24 Y             121 d            4 h              29 m             34.080 s
      CE: CE Time (1 CE)
        + 1945.668 Y
        + 1 Mn             945 Y            244 d            3 h              55 m             0.400 s
        + 61 GS            399 MS           316 KS           926 s      


Congratulations! You've successfully set up UTMS and executed your first command.


.. include:: ../links.rst
