Creating and managing time anchors
==================================

Time anchors are a core concept in UTMS, allowing you to manage and calculate time references efficiently. This tutorial demonstrates how to create, update, and delete anchors.

Prerequisites
-------------
- UTMS installed and configured.

Steps
-----
1. **List existing anchors**:
   Use the `anchor list` or the shortcut `anchor` to show current anchors. The anchors in the `default` group will show up on your queries **BY DEFAULT** if you don't specify which anchors to display. If using the UTMS prompt, prefix the commands with the dot char.

   .. code-block:: bash

      $ utms anchor
      Label: NT
      Name: Now Time (2025-01-08 20:18:11)
      Value: 1736363892.270
      Groups: default, dynamic, modern
      Precision: 1.000e-6
      Breakdowns:
        - Y
      --------------------------------------------------
      Label: DT
      Name: Day Time (2025-01-08 00:00:00)
      Value: 1736290800.000
      Groups: dynamic, modern
      Precision: 1.000e-6
      Breakdowns:
        - dd, cd, s, ms
        - h, m, s, ms
        - KS, s, ms
      --------------------------------------------------
      Label: MT
      Name: Month Time (2025-01-01 00:00:00)
      Value: 1735686000.000
      Groups: dynamic, modern
      Precision: 1.000e-6
      Breakdowns:
        - d, dd, cd, s, ms
        - w, d, dd, cd, s, ms
        - MS, KS, s, ms
      --------------------------------------------------
      Label: YT
      Name: Year Time (2025-01-01 00:00:00)
      Value: 1735686000.000
      Groups: dynamic, modern
      Precision: 1.000e-6
      Breakdowns:
        - d, dd, cd, s, ms
        - w, d, dd, cd, s, ms
        - M, d, dd, cd, s, ms
        - MS, KS, s, ms
      --------------------------------------------------
      Label: UT
      Name: Unix Time (1970-01-01)
      Value: 0.000
      Groups: default, standard, fixed, modern
      Precision: 1.000e-6
      Breakdowns:
        - s
        - Y
        - PS, TS, GS, MS, KS, s, ms
        - Ga, Ma, Mn, Y, d, h, m, s
      --------------------------------------------------
      Label: mT
      Name: Millennium Time (2000-01-01)
      Value: 946684800.000
      Groups: default, standard, fixed, modern
      Precision: 1.000e-6
      Breakdowns:
        - Y
        - Ga, Ma, Mn, Y, d, h, m, s
        - PS, TS, GS, MS, KS, s
      --------------------------------------------------
      Label: CE
      Name: CE Time (1 CE)
      Value: -62167153726.000
      Groups: default, standard, fixed, historical
      Precision: 1.000e-6
      Breakdowns:
        - Y
        - Ga, Ma, Mn, Y, d, h, m, s
        - PS, TS, GS, MS, KS, s
      --------------------------------------------------
      Label: BB
      Name: Big Bang Time (13.8e9 years ago)
      Value: -435485579904000000.000
      Groups: astronomical, fixed
      Precision: 1.000e-6
      Breakdowns:
        - Y
        - Ga, Ma
        - TS, GS, MS, KS, s, ms


2. **Create a new anchor**
   You can create a new anchor by giving it a name and a value, which can be as well resolved by the AI into a date. Everything else besides the name and the value are optional and have default values.

   .. code-block:: console

       $ utms anchor create Biden -n "Joe Biden" -v "when was Joe Biden elected president"
       AI: 2020-11-03T00:00:00+00:00

       Anchors successfully saved to '/home/daniel/.config/utms/anchors.json'		   


   Verify creation:

   .. code-block:: console

      $ utms anchor get Biden
      Label: Biden
      Name: Joe Biden
      Value: 1604361600.000
      Groups:
      Precision: 1.000e-6
      Breakdowns:
        - Y
        - Ga, Ma, Mn, Y, d, h, m, s
        - PS, TS, GS, MS, KS, s
      --------------------------------------------------

2. **Update an Existing Anchor**:
   You can use `anchor set` command to change anchor's values.

   .. code-block:: console

      usage: utms anchor set [-h] [-n NAME] [-v VALUE] [-g GROUPS] [-p PRECISION] [-b BREAKDOWNS] label
      
      Set an anchor parameters by label
      
      Set the parameters of an anchor by its label
      
      positional arguments:
        label                 Label of the anchor
      
      options:
        -h, --help            show this help message and exit
        -n NAME, --name NAME  Full name of the anchor
        -v VALUE, --value VALUE
                              Set the value of the anchor. If it cannot be casted to Decimal, resolve it
                              using dateparser/AI
        -g GROUPS, --groups GROUPS
                              Comma separated list of groups for the anchor i.e. `default,fixed`
        -p PRECISION, --precision PRECISION
                              Precision of the anchor
        -b BREAKDOWNS, --breakdowns BREAKDOWNS
                              List of lists of units to break down the time measurements relative to this
                              anchor i.e. Y;Ga,Ma;TS,GS,MS,KS,s,ms



      poetry run utms anchor update "start_of_sprint" "2025-01-16T10:00:00Z"

