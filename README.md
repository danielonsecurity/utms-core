
# UTMS - Universal Time Measurement System

#### 🚀 **Revolutionizing How We Measure Time**

The **Universal Time Measurement System (UTMS)** is a bold reimagining
of how humanity measures and communicates time. By leveraging the
fundamental, universal nature of **Planck time units**, this system
transcends the limitations of Earth-centric timekeeping, providing a
framework that is consistent across all observers—no matter their
location, velocity, or frame of reference in the universe.


UTMS introduces an innovative method of tracking time, spanning from
the Big Bang to the eventual heat death of the universe, based on a
decimalized time system. This reimagined timekeeping framework offers
significant advantages.


With UTMS, time measurement becomes:
- **Universal**: Accounts for relativistic effects and cosmic scales.
- **Practical**: Simplifies calculations with a decimal-based hierarchy.
- **Flexible**: Allows for multiple reference points, from the Unix epoch to your birthday.

---

#### 🌌 **The Problem with Current Timekeeping**

Traditional timekeeping systems are based on arbitrary historical and
astronomical events, such as Earth's rotation or the Gregorian
calendar. These systems:
- Lack universality: They cannot account for relativistic effects or cosmic time scales.
- Are overly complex: Using non-decimal units (e.g., 24-hour days, 60-minute hours).
- Are Earth-specific: Useless in contexts beyond our planet.

UTMS redefines time with **Planck time units**—the smallest meaningful
measurement of time—as the foundation. This universal metric is
invariant and provides a consistent reference for all observers,
regardless of relativistic effects.

---

#### 🧮 **Core Features**

1. **Planck Time Units as a Universal Metric**
   Time is measured as the total number of Planck time units since the
   Big Bang. This metric remains consistent for all observers,
   enabling communication across vastly different frames of reference.

2. **Decimal-Based Time Hierarchy**
   UTMS introduces logical, scalable time units:
   - **Kiloseconds (KSec)**: 1,000 seconds (~16.67 minutes)
   - **Megaseconds (MSec)**: 1,000,000 seconds (~11.57 days)
   - **Gigaseconds (GSec)**: 1,000,000,000 seconds (~31.7 years)
   - **Teraseconds (TSec)**: 1,000,000,000,000 seconds (~31,688 years)
   This eliminates the need for inconsistent units like hours, weeks, or months.

3. **Customizable Reference Points**
   Start measuring time relative to any point—be it the Unix epoch,
   the birth of civilization, or this very moment. The flexibility of
   UTMS accommodates both personal and scientific contexts.

4. **Earth-Centric Adaptation for Daily Life**
   Retains the concept of "days" but measures time as seconds since
   midnight, reset daily. This ensures compatibility with routines
   like work schedules while simplifying the traditional 24-hour
   format.

---

#### 🔧 **Applications**

- **Cosmic and Relativistic Communication**: Enable synchronization with observers in different inertial frames, including hypothetical relativistic aliens.
- **Scientific Research**: Provide a consistent framework for measuring time across cosmic and quantum scales.
- **Daily Usability**: Simplify everyday time tracking with decimalized, scalable units.

---

#### 🌟 **Getting Started**

This repository includes:
- A working prototype for calculating time in UTMS units.
- Conversion tools between traditional and UTMS units.
- Examples of how to use UTMS for historical and scientific events.

---

#### 💡 **Future Enhancements**

- Integration with Earth's rotation and celestial mechanics for local adaptability.
- Support for prehistoric and cosmic event timelines.
- Improved tools for visualization and human-centric usability.

---

#### 🤝 **Contribute**

Join us in redefining time!
If you have ideas, suggestions, or code to contribute, feel free to open an issue or submit a pull request.

## Prerequisites

Ensure that you have the following installed:
- **Python 3.10+**
- **Git**: For cloning the repository

## Steps to Get Started

### 1. Clone the Repository

Clone the repository to your local machine using the following command:

```bash
git clone https://github.com/danielonsecurity/utms.git
cd utms
```

### 2. Install Poetry

[Poetry](https://python-poetry.org/) is a Python dependency management
tool that simplifies the process of managing dependencies and
packaging.

Either install Poetry from your package manager, or follow the official installation method:

#### On macOS/Linux:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

#### On Windows:

For Windows, use the following command in PowerShell:

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicP) | python -
```

After installation, make sure Poetry is available in your system’s `PATH` by running:

```bash
poetry --version
```

### 3. Install Project Dependencies

Now, install the project dependencies using Poetry. In the project directory, run:

```bash
poetry install
```

This will install all the necessary dependencies listed in the `pyproject.toml` file.

### 4. Activate the Virtual Environment

Poetry automatically creates a virtual environment for your project. To activate it, run:

```bash
poetry shell
```

This will activate the environment where you can run the package and its dependencies.

### Setting up Environment Variables

Copy the `.env.example` file to a new file named `.env`:
```bash
cp .env.example .env
```

Create an Gemini API key here https://aistudio.google.com/app/apikey and add it to `.env`.


### 5. Run the Python Package

Once the virtual environment is activated, you can run UTMS command line:
```bash
$ utms

Welcome to UTMS CLI (Version 0.1.0)!

Input the date you want to check. If not a standard date format, AI will be used to convert your
text into a parseable date. If your input starts with a dot (`.`) it'll be interpreted as a command.

Available Commands:

.unit [unit] [columns] [rows]
    Display a conversion table for a specific unit. The parameters are optional:
    - [unit]: The base unit for the conversion table ("s", "m", etc)
      Defaults to "s" if omitted.
    - [columns]: Number of columns before and after the base unit in
      the table. Defaults to a standard layout if omitted.
    - [rows]: Number of rows before and after the base unit in
      the table. Defaults to a standard layout if omitted.
    Examples:
        .unit s
        .unit m 5
        .unit h 3 10

.conv <value> <source_unit> [target_unit]
    Convert a value from one unit to another. The `target_unit` is optional:
    - <value>: The numerical value to be converted.
    - <source_unit>: The unit of the value to be converted.
    - [target_unit]: The desired unit to convert to. If omitted,
      defaults to a standard unit conversion.
    Examples:
        .conv 60 s m
        .conv 1 h

General:
    .exit
        Exit the UTMS CLI.
    .help
        Display this help message.

Notes:
- Commands are case-sensitive and must begin with a period (`.`).
```

#### Look up a date

Just type the date in any format you can think of, and UTMS will try to make sense of it, first using python's dateparser, and if that fails it'll use the Gemini AI to look up any event known to the AI and get a parseable time value out of it:

```bash
Prompt> today
2024-12-15 03:34:29.518541+01:00
CE Time:
  + 63 GSec, 901 MSec, 384 KSec, 469 Sec
  + 2024 Years, 333 Days, 8 Hours, 34 Minutes, 29 Seconds
Millenium Time:
  + 787 MSec, 545 KSec, 269 Sec
  + 24 Years, 349 Days, 2 Hours, 34 Minutes, 29 Seconds
Now Time:
  - 0 Sec
  - 0 Seconds
Unix Time:
  + 1 GSec, 734 MSec, 230 KSec, 69 Sec
  + 54 Years, 348 Days, 14 Hours, 34 Minutes, 29 Seconds
UPC Time:
  + 435 PSec, 494 TSec, 883 GSec, 468 MSec, 460 KSec, 139 Sec
  + 13800000109 Years, 331 Days, 23 Hours, 8 Minutes, 59 Seconds
Life Time:
  + 1 GSec, 24 MSec, 626 KSec, 869 Sec
  + 32 Years, 171 Days, 2 Hours, 34 Minutes, 29 Seconds
Prompt> 5 days ago
2024-12-10 03:34:36.179889+01:00
CE Time:
  + 63 GSec, 900 MSec, 952 KSec, 476 Sec
  + 2024 Years, 328 Days, 8 Hours, 34 Minutes, 36 Seconds
Millenium Time:
  + 787 MSec, 113 KSec, 276 Sec
  + 24 Years, 344 Days, 2 Hours, 34 Minutes, 36 Seconds
Now Time:
  - 432 KSec
  - 5 Days
Unix Time:
  + 1 GSec, 733 MSec, 798 KSec, 76 Sec
  + 54 Years, 343 Days, 14 Hours, 34 Minutes, 36 Seconds
UPC Time:
  + 435 PSec, 494 TSec, 883 GSec, 468 MSec, 28 KSec, 152 Sec
  + 13800000109 Years, 326 Days, 23 Hours, 9 Minutes, 12 Seconds
Life Time:
  + 1 GSec, 24 MSec, 194 KSec, 876 Sec
  + 32 Years, 166 Days, 2 Hours, 34 Minutes, 36 Seconds
Prompt> beginning of world war 1
1914-07-28T00:00:00+00:00

CE Time:
  + 60 GSec, 417 MSec, 900 KSec
  + 1914 Years, 192 Days, 18 Hours
Millenium Time:
  - 2 GSec, 695 MSec, 939 KSec, 200 Sec
  - 85 Years, 156 Days, 18 Hours
Now Time:
  - 3 GSec, 483 MSec, 484 KSec, 501 Sec
  - 110 Years, 140 Days, 14 Hours, 35 Minutes, 1 Seconds
Unix Time:
  - 1 GSec, 749 MSec, 254 KSec, 400 Sec
  - 55 Years, 157 Days, 6 Hours
UPC Time:
  + 435 PSec, 494 TSec, 879 GSec, 984 MSec, 975 KSec, 701 Sec
  + 13799999999 Years, 191 Days, 8 Hours, 35 Minutes, 1 Seconds
Life Time:
  - 2 GSec, 458 MSec, 857 KSec, 600 Sec
  - 77 Years, 334 Days, 18 Hours
Prompt> extinction of dinosaurs
-0000066000000

Resolved date (integer timestamp): 2082801600000000.00
  + 2 PSec, 82 TSec, 801 GSec, 600 MSec
  + 66000000 Years
Prompt> fall of roman empire
0476-09-04T00:00:00+00:00

CE Time:
  + 15 GSec, 42 MSec, 434 KSec, 400 Sec
  + 476 Years, 243 Days, 6 Hours
Millenium Time:
  - 48 GSec, 71 MSec, 404 KSec, 800 Sec
  - 1523 Years, 106 Days, 6 Hours
Now Time:
  - 48 GSec, 858 MSec, 950 KSec, 129 Sec
  - 1548 Years, 90 Days, 2 Hours, 35 Minutes, 29 Seconds
Unix Time:
  - 47 GSec, 124 MSec, 720 KSec
  - 1493 Years, 106 Days, 18 Hours
UPC Time:
  + 435 PSec, 494 TSec, 834 GSec, 609 MSec, 510 KSec, 129 Sec
  + 13799998561 Years, 241 Days, 20 Hours, 35 Minutes, 29 Seconds
Life Time:
  - 47 GSec, 834 MSec, 323 KSec, 200 Sec
  - 1515 Years, 284 Days, 6 Hours
Prompt>
```

#### Print units conversion table

Use the `.unit` command to display a conversion table between time units:

```bash
Prompt> .unit
Time Unit                Femtosecond (fs)    Picosecond (ps)     Nanosecond (ns)     Microsecond (us)    Millisecond (ms)    Second (s)          Minute (m)          Centiday (cd)       Kilosecond (KS)     Hour (h)            Deciday (dd)
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Planck Time (pt)         5.391e-29           5.391e-32           5.391e-35           5.391e-38           5.391e-41           5.391e-44           8.985e-46           6.240e-47           5.391e-47           1.498e-47           6.240e-48
Quectosecond (qs)        1.000e-15           1.000e-18           1.000e-21           1.000e-24           1.000e-27           1.000e-30           1.667e-32           1.157e-33           1.000e-33           2.778e-34           1.157e-34
Rontosecond (rs)         1.000e-12           1.000e-15           1.000e-18           1.000e-21           1.000e-24           1.000e-27           1.667e-29           1.157e-30           1.000e-30           2.778e-31           1.157e-31
Yoctosecond (ys)         1.000e-9            1.000e-12           1.000e-15           1.000e-18           1.000e-21           1.000e-24           1.667e-26           1.157e-27           1.000e-27           2.778e-28           1.157e-28
Zeptosecond (zs)         1.000e-6            1.000e-9            1.000e-12           1.000e-15           1.000e-18           1.000e-21           1.667e-23           1.157e-24           1.000e-24           2.778e-25           1.157e-25
Attosecond (as)          0.001               1.000e-6            1.000e-9            1.000e-12           1.000e-15           1.000e-18           1.667e-20           1.157e-21           1.000e-21           2.778e-22           1.157e-22
Femtosecond (fs)         1                   0.001               1.000e-6            1.000e-9            1.000e-12           1.000e-15           1.667e-17           1.157e-18           1.000e-18           2.778e-19           1.157e-19
Picosecond (ps)          1000                1                   0.001               1.000e-6            1.000e-9            1.000e-12           1.667e-14           1.157e-15           1.000e-15           2.778e-16           1.157e-16
Nanosecond (ns)          1000000             1000                1                   0.001               1.000e-6            1.000e-9            1.667e-11           1.157e-12           1.000e-12           2.778e-13           1.157e-13
Microsecond (us)         1.000e+9            1000000             1000                1                   0.001               1.000e-6            1.667e-8            1.157e-9            1.000e-9            2.778e-10           1.157e-10
Millisecond (ms)         1.000e+12           1.000e+9            1000000             1000                1                   0.001               1.667e-5            1.157e-6            1.000e-6            2.778e-7            1.157e-7
Second (s)               1.000e+15           1.000e+12           1.000e+9            1000000             1000                1                   0.01667             0.00116             0.001               2.778e-4            1.157e-4
Minute (m)               6.000e+16           6.000e+13           6.000e+10           6.000e+7            60000               60                  1                   0.06944             0.060               0.01667             0.00694
Centiday (cd)            8.640e+17           8.640e+14           8.640e+11           8.640e+8            864000              864                 14.40000            1                   0.864               0.240               0.100
Kilosecond (KS)          1.000e+18           1.000e+15           1.000e+12           1.000e+9            1000000             1000                16.66667            1.15741             1                   0.27778             0.11574
Hour (h)                 3.600e+18           3.600e+15           3.600e+12           3.600e+9            3600000             3600                60                  4.16667             3.60000             1                   0.41667
Deciday (dd)             8.640e+18           8.640e+15           8.640e+12           8.640e+9            8640000             8640                144                 10                  8.64000             2.40000             1
Day (d)                  8.640e+19           8.640e+16           8.640e+13           8.640e+10           8.640e+7            86400               1440                100                 86.40000            24                  10
Week (w)                 6.048e+20           6.048e+17           6.048e+14           6.048e+11           6.048e+8            604800              10080               700                 604.80000           168                 70
Megasecond (MS)          1.000e+21           1.000e+18           1.000e+15           1.000e+12           1.000e+9            1000000             16666.66667         1157.40741          1000                277.77778           115.74074
Lunar Cycle (lc)         2.551e+21           2.551e+18           2.551e+15           2.551e+12           2.551e+9            2551442.80000       42524.04667         2953.05880          2551.44280          708.73411           295.30588
Month (M)                2.592e+21           2.592e+18           2.592e+15           2.592e+12           2.592e+9            2592000             43200               3000                2592                720                 300
Year (Y)                 3.156e+22           3.156e+19           3.156e+16           3.156e+13           3.156e+10           3.156e+7            525960              36525               31557.60000         8766                3652.50000
Decade (D)               3.156e+23           3.156e+20           3.156e+17           3.156e+14           3.156e+11           3.156e+8            5259600             365250              315576              87660               36525
Gigasecond (GS)          1.000e+24           1.000e+21           1.000e+18           1.000e+15           1.000e+12           1.000e+9            1.667e+7            1157407.40741       1000000             277777.77778        115740.74074
Century (C)              3.156e+24           3.156e+21           3.156e+18           3.156e+15           3.156e+12           3.156e+9            5.260e+7            3652500             3155760             876600              365250
Millennium (Mn)          3.156e+25           3.156e+22           3.156e+19           3.156e+16           3.156e+13           3.156e+10           5.260e+8            3.652e+7            3.156e+7            8766000             3652500
Terasecond (TS)          1.000e+27           1.000e+24           1.000e+21           1.000e+18           1.000e+15           1.000e+12           1.667e+10           1.157e+9            1.000e+9            2.778e+8            1.157e+8
Megaannum (Ma)           3.156e+28           3.156e+25           3.156e+22           3.156e+19           3.156e+16           3.156e+13           5.260e+11           3.652e+10           3.156e+10           8.766e+9            3.652e+9
Petasecond (PS)          1.000e+30           1.000e+27           1.000e+24           1.000e+21           1.000e+18           1.000e+15           1.667e+13           1.157e+12           1.000e+12           2.778e+11           1.157e+11
Gigaannum (Ga)           3.156e+31           3.156e+28           3.156e+25           3.156e+22           3.156e+19           3.156e+16           5.260e+14           3.652e+13           3.156e+13           8.766e+12           3.652e+12
Age of Universe (au)     4.355e+32           4.355e+29           4.355e+26           4.355e+23           4.355e+20           4.355e+17           7.258e+15           5.040e+14           4.355e+14           1.210e+14           5.040e+13
Hubble Time (ht)         4.544e+32           4.544e+29           4.544e+26           4.544e+23           4.544e+20           4.544e+17           7.574e+15           5.260e+14           4.544e+14           1.262e+14           5.260e+13
Exasecond (ES)           1.000e+33           1.000e+30           1.000e+27           1.000e+24           1.000e+21           1.000e+18           1.667e+16           1.157e+15           1.000e+15           2.778e+14           1.157e+14
Teraannum (Ta)           3.156e+34           3.156e+31           3.156e+28           3.156e+25           3.156e+22           3.156e+19           5.260e+17           3.652e+16           3.156e+16           8.766e+15           3.652e+15
Zettasecond (ZS)         1.000e+36           1.000e+33           1.000e+30           1.000e+27           1.000e+24           1.000e+21           1.667e+19           1.157e+18           1.000e+18           2.778e+17           1.157e+17
Yottasecond (YS)         1.000e+39           1.000e+36           1.000e+33           1.000e+30           1.000e+27           1.000e+24           1.667e+22           1.157e+21           1.000e+21           2.778e+20           1.157e+20
Ronnasecond (RS)         1.000e+42           1.000e+39           1.000e+36           1.000e+33           1.000e+30           1.000e+27           1.667e+25           1.157e+24           1.000e+24           2.778e+23           1.157e+23
Quettasecond (QS)        1.000e+45           1.000e+42           1.000e+39           1.000e+36           1.000e+33           1.000e+30           1.667e+28           1.157e+27           1.000e+27           2.778e+26           1.157e+26
Galaxial Era (GE)        3.156e+142          3.156e+139          3.156e+136          3.156e+133          3.156e+130          3.156e+127          5.260e+125          3.652e+124          3.156e+124          8.766e+123          3.652e+123
```

If you want to only print the relevant ones, choose the unit you want to center the table to and the number of columns and rows to display inbetween:

```bash
Prompt> .unit h 3 5
Time Unit                Minute (m)          Centiday (cd)       Kilosecond (KS)     Hour (h)            Deciday (dd)        Day (d)             Week (w)
---------------------------------------------------------------------------------------------------------------------------------------------------------------------
Millisecond (ms)         1.667e-5            1.157e-6            1.000e-6            2.778e-7            1.157e-7            1.157e-8            1.653e-9
Second (s)               0.01667             0.00116             0.001               2.778e-4            1.157e-4            1.157e-5            1.653e-6
Minute (m)               1                   0.06944             0.060               0.01667             0.00694             6.944e-4            9.921e-5
Centiday (cd)            14.40000            1                   0.864               0.240               0.100               0.010               0.00143
Kilosecond (KS)          16.66667            1.15741             1                   0.27778             0.11574             0.01157             0.00165
Hour (h)                 60                  4.16667             3.60000             1                   0.41667             0.04167             0.00595
Deciday (dd)             144                 10                  8.64000             2.40000             1                   0.100               0.01429
Day (d)                  1440                100                 86.40000            24                  10                  1                   0.14286
Week (w)                 10080               700                 604.80000           168                 70                  7                   1
Megasecond (MS)          16666.66667         1157.40741          1000                277.77778           115.74074           11.57407            1.65344
Lunar Cycle (lc)         42524.04667         2953.05880          2551.44280          708.73411           295.30588           29.53059            4.21866
Prompt>
```

#### Convert units

Use the `.conv` command to convert between units:

```bash
Prompt> .conv 5 h
Converting 5 h:
--------------------------------------------------
Planck Time (pt):        3.339e+47
Quectosecond (qs):       1.800e+34
Rontosecond (rs):        1.800e+31
Yoctosecond (ys):        1.800e+28
Zeptosecond (zs):        1.800e+25
Attosecond (as):         1.800e+22
Femtosecond (fs):        1.800e+19
Picosecond (ps):         1.800e+16
Nanosecond (ns):         1.800e+13
Microsecond (us):        1.800e+10
Millisecond (ms):        1.800e+7
Second (s):              18000
Minute (m):              300
Centiday (cd):           20.83333
Kilosecond (KS):         18
Hour (h):                5
Deciday (dd):            2.08333
Day (d):                 0.20833
Week (w):                0.02976
Megasecond (MS):         0.018
Lunar Cycle (lc):        0.00705
Month (M):               0.00694
Year (Y):                5.704e-4
Decade (D):              5.704e-5
Gigasecond (GS):         1.800e-5
Century (C):             5.704e-6
Millennium (Mn):         5.704e-7
Terasecond (TS):         1.800e-8
Megaannum (Ma):          5.704e-10
Petasecond (PS):         1.800e-11
Gigaannum (Ga):          5.704e-13
Age of Universe (au):    4.133e-14
Hubble Time (ht):        3.961e-14
Exasecond (ES):          1.800e-14
Teraannum (Ta):          5.704e-16
Zettasecond (ZS):        1.800e-17
Yottasecond (YS):        1.800e-20
Ronnasecond (RS):        1.800e-23
Quettasecond (QS):       1.800e-26
Galaxial Era (GE):       5.704e-124

Prompt> .conv 1.25e7 s
Converting 1.25e7 s:
--------------------------------------------------
Planck Time (pt):        2.319e+50
Quectosecond (qs):       1.250e+37
Rontosecond (rs):        1.250e+34
Yoctosecond (ys):        1.250e+31
Zeptosecond (zs):        1.250e+28
Attosecond (as):         1.250e+25
Femtosecond (fs):        1.250e+22
Picosecond (ps):         1.250e+19
Nanosecond (ns):         1.250e+16
Microsecond (us):        1.250e+13
Millisecond (ms):        1.250e+10
Second (s):              1.250e+7
Minute (m):              208333.33333
Centiday (cd):           14467.59259
Kilosecond (KS):         12500
Hour (h):                3472.22222
Deciday (dd):            1446.75926
Day (d):                 144.67593
Week (w):                20.66799
Megasecond (MS):         12.50000
Lunar Cycle (lc):        4.89919
Month (M):               4.82253
Year (Y):                0.39610
Decade (D):              0.03961
Gigasecond (GS):         0.01250
Century (C):             0.00396
Millennium (Mn):         3.961e-4
Terasecond (TS):         1.250e-5
Megaannum (Ma):          3.961e-7
Petasecond (PS):         1.250e-8
Gigaannum (Ga):          3.961e-10
Age of Universe (au):    2.870e-11
Hubble Time (ht):        2.751e-11
Exasecond (ES):          1.250e-11
Teraannum (Ta):          3.961e-13
Zettasecond (ZS):        1.250e-14
Yottasecond (YS):        1.250e-17
Ronnasecond (RS):        1.250e-20
Quettasecond (QS):       1.250e-23
Galaxial Era (GE):       3.961e-121
Prompt> .conv 1.25e7 s h
Converting 1.25e7 s:
--------------------------------------------------
Hour (h):                3472.22222
Prompt>
```
