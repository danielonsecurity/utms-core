
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

## Steps to Get Started

### Install UTMS

Make sure [you have pip installed](https://pip.pypa.io/en/stable/installation/), and install UTMS from PyPi:

```bash
$ pip install utms
```

### Configure Gemini API key:

Create an Gemini API key here https://aistudio.google.com/app/apikey and configure it within UTMS:

```bash
$ utms config set gemini.api_key YOUR_API_KEY
```

### Run UTMS


Once the API key is configured, you can run UTMS to query the AI about dates. If you want to just use the prompt simply run `utms`, and besides simply resolving arbitrary string to a time, it also supports several commands:

```bash
$ utms --help

usage: utms [-h] [--version] [--debug]
            {config,unit,daytime,resolve,anchor,clock} ...

UTMS CLI version 0.1.10

positional arguments:
  {config,unit,daytime,resolve,anchor,clock}
                        Main commands
    config              config management
    unit                unit management
    daytime             daytime management
    resolve             resolve management
    anchor              anchor management
    clock               clock management

options:
  -h, --help            show this help message and exit
  --version             Show UTMS version
  --debug               Enter Python's PDB
```


#### Clocks

To show current time with analog/digital clocks in both standard and decimal times use `utms clock` or run `.clock` command:


![Analog Clock](utms/resources/clock.png)

#### Convert units

##### Decimal/Duodecimal day times

To convert between day time formats use `daytime convert` commands:

```bash
$ utms daytime convert 15:30:25

6.4.529
```
```bash
$ utms daytime convert 1.2.205

02:56:13
```

##### Convert arbitrary time units

Use the `unit convert` command to convert between arbitrary time units:

```bash
$ utms unit convert 5 h

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
Quarter (Q):             0.00228             
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
```
```bash
$ utms unit convert 1.25e7 s

Converting 12500000 s:
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
Quarter (Q):             1.58444             
Year (Y):                0.39611             
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
```
```bash
$ utms unit convert 1.25e7 s h

Converting 12500000 s:
--------------------------------------------------
Hour (h):                3472.22222
```


#### Look up a date

Just type the date in any format you can think of, and UTMS will try to make sense of it, first using python's dateparser, and if that fails it'll use the Gemini AI to look up any event known to the AI and get a parseable time value out of it:

```bash
$ utms resolve today

2025-01-08 11:48:01.486462+00:00
NT: Now Time (2025-01-08)
  + 0.000 Y         
  + 0.044 s         
  + 0.044 s         
DT: Day Time (2025-01-08 00:00:00)
  + 4 dd             9 cd             145 s            486.462 ms      
  + 11 h             48 m             1 s              486.462 ms      
  + 42 KS            481 s            486.462 ms      
YT: Year Time (2025-01-01 00:00:00)
  + 7 d              4 dd             9 cd             145 s            486.462 ms      
  + 1 w              4 dd             9 cd             145 s            486.462 ms      
  + 7 d              4 dd             9 cd             145 s            486.462 ms      
  + 647 KS           281 s            486.462 ms      
MT: Month Time (2025-01-01 00:00:00)
  + 7 d              4 dd             9 cd             145 s            486.462 ms      
  + 1 w              4 dd             9 cd             145 s            486.462 ms      
  + 647 KS           281 s            486.462 ms      
LT: Life Time (1992-27-06)
  + 32.536 Y        
  + 32 Y             195 d            17 h             47 m             26.926 s        
  + 1 GS             26 MS            733 KS           681.486 s       
UT: Unix Time (1970-01-01)
  + 1736336881.486 s
  + 55.022 Y        
  + 1 GS             736 MS           336 KS           881 s            486.462 ms      
  + 55 Y             8 d              4 h              5 m              47.086 s        
mT: Millennium Time (2000-01-01)
  + 25.023 Y        
  + 25 Y             8 d              10 h             28 m             49.486 s        
  + 789 MS           652 KS           81.486 s        
CE: CE Time (1 CE)
  + 2025.023 Y      
  + 2 Mn             25 Y             8 d              6 h              41 m             35.486 s        
  + 63 GS            903 MS           490 KS           607.486 s       
BB: Big Bang Time (13.8e9 years ago)
  + 13800000055.022 Y
  + 13 Ga            800.000 Ma      
  + 435485 TS        581 GS           640 MS           336 KS           911 s            486.462 ms
```
```bash
$ utms resolve beginning of world war 1

1914-07-28T00:00:00+00:00

NT: Now Time (2025-01-08)
  - 110.454 Y       
  - 110 Y            165 d            20 h             23 m             33.517 s        
  - 3 GS             485 MS           591 KS           282.317 s       
DT: Day Time (2025-01-08 00:00:00)
  - 403420 dd        0E+3 ms         
  - 968208 h         0E+3 ms         
  - 3485548 KS       800 s            0E+3 ms         
YT: Year Time (2025-01-01 00:00:00)
  - 40335 d          0E+3 ms         
  - 5762 w           1 d              0E+3 ms         
  - 1344 M           15 d             0E+3 ms         
  - 3484 MS          944 KS           0E+3 ms         
MT: Month Time (2025-01-01 00:00:00)
  - 40335 d          0E+3 ms         
  - 5762 w           1 d              0E+3 ms         
  - 3484 MS          944 KS           0E+3 ms         
LT: Life Time (1992-27-06)
  - 77.918 Y        
  - 77 Y             335 d            8 h              24 m             51.840 s        
  - 2 GS             458 MS           857 KS           600 s           
UT: Unix Time (1970-01-01)
  - 1749254400 s    
  - 55.432 Y        
  - 1 GS             749 MS           254 KS           400 s            0E+3 ms         
  - 55 Y             157 d            16 h             17 m             45.600 s        
mT: Millennium Time (2000-01-01)
  - 85.431 Y        
  - 85 Y             157 d            9 h              54 m             43.200 s        
  - 2 GS             695 MS           939 KS           200 s           
CE: CE Time (1 CE)
  + 1914.569 Y      
  + 1 Mn             914 Y            207 d            16 h             6 m              48.880 s        
  + 60 GS            417 MS           899 KS           326 s           
BB: Big Bang Time (13.8e9 years ago)
  + 13799999944.568 Y
  + 13 Ga            800.000 Ma      
  + 435485 TS        578 GS           154 MS           745 KS           630 s            0E+3 ms
```
```bash
$ utms resolve extinction of dinosaurs

-6.6e7

NT: Now Time (2025-01-08)
  - 66002024.022 Y  
  - 66 Ma            2 Mn             24 Y             8 d              4 h              5 m              53.334 s        
  - 2 PS             82 TS            820 GS           993 MS           204 KS           339.398 s       
DT: Day Time (2025-01-08 00:00:00)
  - 241067244578 dd  9 cd             155 s            664.184 ms      
  - 578561386989 h   24 m             11 s             664.184 ms      
  - 2082820993161 KS 851 s            664.184 ms      
YT: Year Time (2025-01-01 00:00:00)
  - 24106724450 d    8 dd             9 cd             155 s            664.184 ms      
  - 3443817778 w     4 d              8 dd             9 cd             155 s            664.184 ms      
  - 803557481 M      20 d             8 dd             9 cd             155 s            664.184 ms      
  - 2082820992 MS    557 KS           51 s             664.184 ms      
MT: Month Time (2025-01-01 00:00:00)
  - 24106724450 d    8 dd             9 cd             155 s            664.184 ms      
  - 3443817778 w     4 d              8 dd             9 cd             155 s            664.184 ms      
  - 2082820992 MS    557 KS           51 s             664.184 ms      
LT: Life Time (1992-27-06)
  - 66001991.486 Y  
  - 66 Ma            1 Mn             991 Y            177 d            16 h             7 m              6.240 s         
  - 2 PS             82 TS            819 GS           966 MS           470 KS           651.664 s       
UT: Unix Time (1970-01-01)
  - 2082819256867451.664 s
  - 66001969 Y      
  - 2 PS             82 TS            819 GS           256 MS           867 KS           451 s            664.184 ms      
  - 66 Ma            1 Mn             969 Y            0E-43 s         
mT: Millennium Time (2000-01-01)
  - 66001998.999 Y  
  - 66 Ma            1 Mn             998 Y            364 d            23 h             25 m             43.680 s        
  - 2 PS             82 TS            820 GS           203 MS           552 KS           251.664 s       
CE: CE Time (1 CE)
  - 65999999.000 Y  
  - 65 Ma            999 Mn           998 Y            365 d            3 h              12 m             57.680 s        
  - 2 PS             82 TS            757 GS           89 MS            713 KS           725.664 s       
BB: Big Bang Time (13.8e9 years ago)
  + 13733998031.000 Y
  + 13 Ga            733.998 Ma      
  + 433402 TS        760 GS           647 MS           132 KS           578 s            335.816 ms
```
```bash
$ utms resolve fall of roman empire

0476-09-04T00:00:00+00:00

NT: Now Time (2025-01-08)
  - 1548.347 Y      
  - 1 Mn             548 Y            126 d            13 h             35 m             20.895 s        
  - 48 GS            861 MS           56 KS            892.735 s       
DT: Day Time (2025-01-08 00:00:00)
  - 5655210 dd       0E+3 ms         
  - 13572504 h       0E+3 ms         
  - 48861014 KS      400 s            0E+3 ms         
YT: Year Time (2025-01-01 00:00:00)
  - 565514 d         0E+3 ms         
  - 80787 w          5 d              0E+3 ms         
  - 18850 M          14 d             0E+3 ms         
  - 48860 MS         409 KS           600 s            0E+3 ms         
MT: Month Time (2025-01-01 00:00:00)
  - 565514 d         0E+3 ms         
  - 80787 w          5 d              0E+3 ms         
  - 48860 MS         409 KS           600 s            0E+3 ms         
LT: Life Time (1992-27-06)
  - 1515.811 Y      
  - 1 Mn             515 Y            296 d            1 h              36 m             28.800 s        
  - 47 GS            834 MS           323 KS           200 s           
UT: Unix Time (1970-01-01)
  - 47124720000 s   
  - 1493.324 Y      
  - 47 GS            124 MS           720 KS           0E+3 ms         
  - 1 Mn             493 Y            118 d            9 h              29 m             22.560 s        
mT: Millennium Time (2000-01-01)
  - 1523.323 Y      
  - 1 Mn             523 Y            118 d            3 h              6 m              20.160 s        
  - 48 GS            71 MS            404 KS           800 s           
CE: CE Time (1 CE)
  + 476.676 Y       
  + 476 Y            246 d            22 h             55 m             11.920 s        
  + 15 GS            42 MS            433 KS           726 s           
BB: Big Bang Time (13.8e9 years ago)
  + 13799998506.676 Y
  + 13 Ga            799.999 Ma      
  + 435485 TS        532 GS           779 MS           280 KS           30 s             0E+3 ms
```


#### Print units conversion table

Use the `.unit` command to display a conversion table between time units:

```bash
$ utms unit

Planck Time (pt):        5.391e-44           
Quectosecond (qs):       1.000e-30           
Rontosecond (rs):        1.000e-27           
Yoctosecond (ys):        1.000e-24           
Zeptosecond (zs):        1.000e-21           
Attosecond (as):         1.000e-18           
Femtosecond (fs):        1.000e-15           
Picosecond (ps):         1.000e-12           
Nanosecond (ns):         1.000e-9            
Microsecond (us):        1.000e-6            
Millisecond (ms):        0.001               
Second (s):              1                   
Minute (m):              60                  
Centiday (cd):           864                 
Kilosecond (KS):         1000                
Hour (h):                3600                
Deciday (dd):            8640                
Day (d):                 86400               
Week (w):                604800              
Megasecond (MS):         1000000             
Lunar Cycle (lc):        2551442.80000       
Month (M):               2592000             
Quarter (Q):             7889231.52000       
Year (Y):                3.156e+7            
Decade (D):              3.156e+8            
Gigasecond (GS):         1.000e+9            
Century (C):             3.156e+9            
Millennium (Mn):         3.156e+10           
Terasecond (TS):         1.000e+12           
Megaannum (Ma):          3.156e+13           
Petasecond (PS):         1.000e+15           
Gigaannum (Ga):          3.156e+16           
Age of Universe (au):    4.355e+17           
Hubble Time (ht):        4.544e+17           
Exasecond (ES):          1.000e+18           
Teraannum (Ta):          3.156e+19           
Zettasecond (ZS):        1.000e+21           
Yottasecond (YS):        1.000e+24           
Ronnasecond (RS):        1.000e+27           
Quettasecond (QS):       1.000e+30           
Galaxial Era (GE):       3.156e+127
```

If you want to only print the relevant ones, choose the unit you want to center the table to and the number of columns and rows to display inbetween:

```bash
$ utms unit table h 3 5

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
```
