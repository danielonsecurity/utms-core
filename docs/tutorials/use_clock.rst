

Show/use decimal clock
=======================

.. _decimal_time_tutorial:

Decimal Time is an alternative system for measuring time that divides
the day into a base-10 structure instead of the traditional 24-hour
(duodecimal) system. This tutorial explains how to interpret decimal
time and the advantages it offers for measuring and conceptualizing
daytime.

Decimal Time System
--------------------

In the decimal time system, the day is divided as follows:

**Decidays (D)**: 10 equal parts of the day (1 deciday = 8640 seconds).

**Centidays (C)**: 100 equal parts of a deciday (1 centiday = 864
seconds).

**Seconds (SSS)**: The smallest unit, corresponding to regular seconds.

**Kiloseconds (KS)**: A larger unit representing 1000 seconds, used as an
auxiliary representation.

A decimal time value is represented in two formats:

- D.C.SSS: Decidays, centidays, and seconds (e.g., 5.7.752).
- Decimal float: A floating-point representation from 0.0000 to 10.0000 (e.g., 5.78704).

For comparison, traditional time is displayed in HH:MM:SS, while
kiloseconds count up to 86.4 (as there are 86,400 seconds in a day).

Interpretation Examples
-----------------------

The following table demonstrates how to interpret the time in
different formats:

+------------------------+------------------+--------------------------+--------------------+
| Decimal Time (D.C.SSS) | Decidays (float) | Standard Time (HH:MM:SS) | Kiloseconds (86.4) |
+------------------------+------------------+--------------------------+--------------------+
|        0.0.000         |     0.00000      |         00:00:00         |        0.00        |
+------------------------+------------------+--------------------------+--------------------+
|        0.4.144         |     0.41667      |         01:00:00         |        3.60        |
+------------------------+------------------+--------------------------+--------------------+
|        1.0.000         |     1.00000      |         02:24:00         |        8.64        |
+------------------------+------------------+--------------------------+--------------------+
|        1.5.000         |     1.50000      |         03:36:00         |       12.96        |
+------------------------+------------------+--------------------------+--------------------+
|        5.7.752         |     5.78704      |         13:53:20         |       50.00        |
+------------------------+------------------+--------------------------+--------------------+
|        8.3.288         |     8.33333      |         20:00:00         |       72.00        |
+------------------------+------------------+--------------------------+--------------------+
|        9.5.000         |     9.50000      |         22:48:00         |       82.08        |
+------------------------+------------------+--------------------------+--------------------+
|       10.0.000         |    10.00000      |         24:00:00         |       86.40        |
+------------------------+------------------+--------------------------+--------------------+

Benefits of Decimal Time
------------------------

Using a decimal-based time system offers several advantages:

- Simplified Arithmetic:

  Decimal fractions make time calculations (e.g., elapsed time)
  simpler and more intuitive.  Comparing and converting values is
  easier due to consistent base-10 scaling.

- Global Consistency:

  A decimal system aligns better with metric units, fostering
  consistency across scientific and technical fields.

- Precision in Measurements:

  The fractional representation (e.g., 0.41667 decidays) facilitates
  precise timekeeping, especially for engineering or computational
  purposes.

- Streamlined Conceptualization:

  Conceptualizing a day as 10 units instead of 24 hours simplifies
  mental modeling of time intervals.

- Comparison with Duodecimal System

  The traditional 24-hour (duodecimal) system divides the day into
  uneven divisions (24 hours, 60 minutes per hour, 60 seconds per
  minute). While familiar, it complicates calculations and is not
  compatible with the base-10 metric standard. Decimal time eliminates
  these irregularities.

Use Cases
----------

Decimal time is particularly useful in:

**Scientific research**: Where precise time measurement and calculations
are critical.

**Education**: Helping students better understand time as a quantitative
concept.

**Software development**: Simplifying time-related computations in
applications and simulations.

Decimal time in UTMS
---------------------

To show the conversion table in UTMS with all those formats, use the
`utms daytime` command (shortcut for `utms daytime timetable`):

.. code-block:: console

   $ utms daytime 
   +------------------------+------------------+--------------------------+--------------------+
   | Decimal Time (D.C.SSS) | Decidays (float) | Standard Time (HH:MM:SS) | Kiloseconds (86.4) |
   +------------------------+------------------+--------------------------+--------------------+
   |        0.0.000         |     0.00000      |         00:00:00         |        0.00        |
   |        0.4.144         |     0.41667      |         01:00:00         |        3.60        |
   |        0.5.000         |     0.50000      |         01:12:00         |        4.32        |
   |        0.8.288         |     0.83333      |         02:00:00         |        7.20        |
   |        1.0.000         |     1.00000      |         02:24:00         |        8.64        |
   |        1.1.496         |     1.15741      |         02:46:40         |       10.00        |
   |        1.2.432         |     1.25000      |         03:00:00         |       10.80        |
   |        1.5.000         |     1.50000      |         03:36:00         |       12.96        |
   |        1.6.576         |     1.66667      |         04:00:00         |       14.40        |
   |        2.0.000         |     2.00000      |         04:48:00         |       17.28        |
   |        2.0.720         |     2.08333      |         05:00:00         |       18.00        |
   |        2.3.128         |     2.31481      |         05:33:20         |       20.00        |
   |        2.5.000         |     2.50000      |         06:00:00         |       21.60        |
   |        2.9.144         |     2.91667      |         07:00:00         |       25.20        |
   |        3.0.000         |     3.00000      |         07:12:00         |       25.92        |
   |        3.3.288         |     3.33333      |         08:00:00         |       28.80        |
   |        3.4.624         |     3.47222      |         08:20:00         |       30.00        |
   |        3.5.000         |     3.50000      |         08:24:00         |       30.24        |
   |        3.7.432         |     3.75000      |         09:00:00         |       32.40        |
   |        4.0.000         |     4.00000      |         09:36:00         |       34.56        |
   |        4.1.576         |     4.16667      |         10:00:00         |       36.00        |
   |        4.5.000         |     4.50000      |         10:48:00         |       38.88        |
   |        4.5.720         |     4.58333      |         11:00:00         |       39.60        |
   |        4.6.256         |     4.62963      |         11:06:40         |       40.00        |
   |        5.0.000         |     5.00000      |         12:00:00         |       43.20        |
   |        5.4.144         |     5.41667      |         13:00:00         |       46.80        |
   |        5.5.000         |     5.50000      |         13:12:00         |       47.52        |
   |        5.7.752         |     5.78704      |         13:53:20         |       50.00        |
   |        5.8.288         |     5.83333      |         14:00:00         |       50.40        |
   |        6.0.000         |     6.00000      |         14:24:00         |       51.84        |
   |        6.2.432         |     6.25000      |         15:00:00         |       54.00        |
   |        6.5.000         |     6.50000      |         15:36:00         |       56.16        |
   |        6.6.576         |     6.66667      |         16:00:00         |       57.60        |
   |        6.9.384         |     6.94444      |         16:40:00         |       60.00        |
   |        7.0.000         |     7.00000      |         16:48:00         |       60.48        |
   |        7.0.720         |     7.08333      |         17:00:00         |       61.20        |
   |        7.5.000         |     7.50000      |         18:00:00         |       64.80        |
   |        7.9.144         |     7.91667      |         19:00:00         |       68.40        |
   |        8.0.000         |     8.00000      |         19:12:00         |       69.12        |
   |        8.1.016         |     8.10185      |         19:26:40         |       70.00        |
   |        8.3.288         |     8.33333      |         20:00:00         |       72.00        |
   |        8.5.000         |     8.50000      |         20:24:00         |       73.44        |
   |        8.7.432         |     8.75000      |         21:00:00         |       75.60        |
   |        9.0.000         |     9.00000      |         21:36:00         |       77.76        |
   |        9.1.576         |     9.16667      |         22:00:00         |       79.20        |
   |        9.2.512         |     9.25926      |         22:13:20         |       80.00        |
   |        9.5.000         |     9.50000      |         22:48:00         |       82.08        |
   |        9.5.720         |     9.58333      |         23:00:00         |       82.80        |
   +------------------------+------------------+--------------------------+--------------------+   


To convert between D.C.SSS and HH:MM:SS formats, use the `utms daytime convert` command:

.. code-block:: console

   $ utms daytime convert 5.8.288
   14:00:00

   $ utms daytime convert 2.8
   06:43:12

   $ utms daytime convert 13:05
   5.4.443

   $ utms daytime convert 22:05:47
   9.2.059

And if you want to show analog clocks with all those units in one
place, use the `utms clock` command. It will open a window with 2
clocks in both decimal and duodecimal systems, and show all units in
it:

.. code-block:: console

   $ utms clock


.. image:: ../images/clock.png




Conclusion
-----------

The decimal time system is an efficient, intuitive, and precise method
of measuring and representing time. While its adoption may require
initial adjustments, its advantages make it a powerful alternative to
the traditional 24-hour system. By understanding and utilizing decimal
time, users can streamline calculations, enhance precision, and align
with the metric standard.
