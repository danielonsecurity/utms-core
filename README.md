
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

Once the virtual environment is activated, you can run the package using the following command:

```bash
poetry run python -m utms
```

OR just simply run it like this:

```bash
utms
```


This will execute the package. If you have specific commands or
functionality to run, you can adjust the command accordingly.
