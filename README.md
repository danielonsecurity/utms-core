
# UTS - Python Package

UTS (Universal Time System) introduces an innovative method of
tracking time, spanning from the Big Bang to the eventual heat death
of the universe, based on a decimalized time system. This reimagined
timekeeping framework offers significant advantages:

Universal Scalability: By uniting cosmic and human timescales, UTS
enables seamless precision in scientific, astronomical, and everyday
contexts.  Simplicity and Consistency: Decimal-based units eliminate
irregularities found in traditional systems, such as leap years or
varying month lengths.  Future-Proofing: Designed to transcend
cultural and temporal boundaries, UTS provides a globally consistent
reference point, ideal for a spacefaring and technologically advanced
society.  UTS challenges conventional notions of time by emphasizing
universality, precision, and adaptability, creating a system that is
as relevant to cosmic events as it is to daily life.

## Prerequisites

Ensure that you have the following installed:
- **Python 3.10+**
- **Git**: For cloning the repository

## Steps to Get Started

### 1. Clone the Repository

Clone the repository to your local machine using the following command:

```bash
git clone https://github.com/danielonsecurity/uts.git
cd uts
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
poetry run python -m uts
```

OR just simply run it like this:

```bash
uts
```


This will execute the package. If you have specific commands or
functionality to run, you can adjust the command accordingly.
