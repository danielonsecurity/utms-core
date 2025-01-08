"""
This module integrates the Gemini model from the Google Generative AI API to generate precise date
and time strings in ISO 8601 format based on input descriptions of events or concepts.

The module is specifically designed to handle a wide range of date inputs, including:
- **Common Era (CE)** events, formatted in full ISO 8601 format.
- **Before Common Era (BCE)** events, using a leading minus (`-`) and ISO-like formatting.
- Events far in the future (beyond 9999 CE) or distant past (beyond -9999 BCE) using scientific
  notation or relative years.
- **Relative dates** (e.g., "yesterday", "5 days ago") by calculating the corresponding date
  in ISO 8601 format.
- **Unknown or uncertain dates**, where the model defaults to `UNKNOWN` if no valid date can be
  determined.

**Key Features**:
1. **Precise Formatting**:
   - ISO 8601 compliance for all generated dates, including timezone offsets.
   - Default values for unknown time components (e.g., `00:00:00` for time, `01` for unknown days).
   - Special handling for extreme ranges, such as prehistoric or far-future events.

2. **Configurable Generation**:
   - The model is pre-configured with parameters for controlling output length, randomness, and
     sampling strategies:
     - `max_output_tokens=30`: Limits the response length.
     - `temperature=0.7`: Balances randomness and determinism in output.
     - `top_p=0.9`: Enables nucleus sampling for high-probability outputs.
     - `top_k=50`: Limits the model's output options to the top 50 tokens.

3. **Error Handling**:
   - Robust error handling for API connectivity issues, invalid responses, and unexpected model
     outputs.
   - Provides clear fallback messages in case of failures.

**Functions**:
- `ai_generate_date(input_text: str) -> str`:
  Takes a natural language description of an event or date concept and returns a formatted
  ISO 8601 date string, adhering to predefined formatting rules.

**Dependencies**:
- `google.generativeai`: For interacting with the Gemini model.
- `requests`: For handling API connectivity.

**Usage Example**:
```python
>>> ai_generate_date("When did the Apollo 11 moon landing occur?")
"1969-07-20T00:00:00+00:00"

>>> ai_generate_date("5 days before the fall of the Berlin Wall")
"1989-11-04T00:00:00+00:00"
"""

import os
from datetime import datetime
from decimal import Decimal
from typing import Union

import google.generativeai as genai
import requests
from google.api_core.exceptions import ResourceExhausted

from utms import constants
from utms.config import Config
from utms.utils import resolve_date_dateparser


class AI:
    """
    A class for interfacing with the Gemini Generative AI model.

    This class manages the configuration, initialization, and interaction with the Gemini AI API.
    It includes functionality for generating date-related outputs in ISO format.

    Attributes:
        config (genai.GenerationConfig): The configuration for generation, including parameters
            such as maximum output tokens, temperature, top-p, and top-k.
        model (genai.GenerativeModel): The initialized generative AI model.

    Methods:
        generate_date(input_text: str) -> str:
            Generates a date based on the provided input text using the Gemini AI model.
    """

    def __init__(self, config: Config) -> None:
        """
        Initializes the AI class by setting up the Gemini API configuration and loading the model.

        Configuration values are loaded from a `Config` object, which retrieves settings from a
        persistent configuration store. If an API key is not present, the user is prompted to
        input one, which is then saved for future use.

        Model Configuration:
            - The model name is dynamically loaded from the configuration.
            - A system instruction prompt is loaded from a file (`system_prompt.txt`), with the
              current date and time injected into the prompt.

        Raises:
            FileNotFoundError: If the system prompt file does not exist.
            ValueError: If required configuration values are missing.
        """
        self.config = config
        if config.has_value("gemini.api_key"):
            api_key = config.get_value("gemini.api_key")
        else:
            api_key = input("Gemini API key: ")
            config.set_value("gemini.api_key", api_key)

        genai.configure(api_key=api_key)
        self.ai_config = genai.GenerationConfig(
            max_output_tokens=int(config.get_value("gemini.max_output_tokens")),
            temperature=float(config.get_value("gemini.temperature")),
            top_p=float(config.get_value("gemini.top_p")),
            top_k=int(config.get_value("gemini.top_k")),
        )

        with open(
            os.path.join(config.utms_dir, "system_prompt.txt"), "r", encoding="utf-8"
        ) as file:
            self.model = genai.GenerativeModel(
                "models/" + config.get_value("gemini.model"),
                system_instruction=file.read().format(datetime_now=datetime.now().isoformat()),
            )

    def generate_date(self, input_text: str) -> str:
        """
        Generate a date string in ISO 8601 format from an input text using the Gemini model.

        This function generates a precise date in ISO 8601 format based on
        the input text using the Gemini model.  The model is configured to
        handle dates in various ranges, including Common Era (CE), Before
        Common Era (BCE), events beyond 9999 CE, relative dates (e.g.,
        "yesterday", "5 days ago"), and uncertain or unknown dates.

        The generated date adheres to strict formatting rules, such as
        including the correct timezone offset (`+00:00` for UTC) and
        handling missing or uncertain date components by substituting
        default values like `01` for missing days and months, or
        `00:00:00` for missing time.

        If the model's response is valid and provides a correctly
        formatted ISO 8601 date, the function returns it.  If the response
        is invalid, an appropriate fallback message is returned. In case
        of errors during the model call, the error message is returned.

        Args:
            input_text (str): The input text describing the event or
            concept for which a date should be generated.

        Returns:
            str: The generated date in ISO 8601 format, or a fallback
                 message if the model's response is invalid or an error
                 occurs.

        Example:
            >>> ai_generate_date("What is the date of the Apollo 11 moon landing?")
            "1969-07-20T00:00:00+00:00"

            >>> ai_generate_date("Tell me a random date")
            "No valid response received from the API."

        **Model Configuration**:
            The model is configured with the following settings:

            - `max_output_tokens=30`: Limits the length of the model's response.
            - `temperature=0.7`: Controls the randomness of the generated content.
            - `top_p=0.9`: Implements nucleus sampling to select from the
              top 90% of possible outputs.
            - `top_k=50`: Limits the possible outputs to the top 50 tokens.

        **Date Formatting Rules**:
            The model is instructed to strictly adhere to the following date formatting rules:

            - **For Common Era (CE) events**: Output the date in full ISO
                8601 format (`YYYY-MM-DDTHH:MM:SS+ZZ:ZZ`).
            - **For Before Common Era (BCE) events**: Output the date with
                a leading minus (`-YYYY-MM-DD`).
            - **For events after 9999 CE**: Use a `+` prefix and ISO 8601 format.
            - **For relative dates**: Calculate the exact ISO 8601 date.
            - **For unknown dates**: Return `UNKNOWN`, but avoid unless absolutely necessary.
            - **For date ranges**: Default to the beginning of the range.

        The model is also instructed to avoid providing explanations or
        context; it should return only the date.
        """
        try:
            # Call the Gemini model
            response = self.model.generate_content(input_text, generation_config=self.ai_config)

            if response and response.text:
                # Clean the response text to ensure it's a valid ISO date format
                print(response.text)
                iso_date: str = response.text.strip()
                return iso_date
            raise ValueError("No valid response received from the API.")

        except requests.ConnectionError:
            return "Connection error: Unable to reach the API."

        except requests.Timeout:
            return "Timeout error: The API request timed out."

        except requests.RequestException as e:
            return f"Request error: {e}"

        except ResourceExhausted as e:
            return f"Resource exhausted: {e}"

    # Function to resolve dates
    def resolve_date(self, input_text: str) -> Union[datetime, Decimal, str, None]:
        """
        Resolves a date from a given string input. The function first
        attempts to parse the date using `dateparser`, and if unsuccessful,
        it uses an AI-based approach to generate a potential date.

        The function supports:

        - Parsing valid dates from input text (via `dateparser`).
        - Handling historical dates expressed as negative years (e.g., '-44' for 44 BCE).
        - Interpreting future events expressed with a '+' sign (e.g., '+10' for 10 years from now).
        - Processing ISO 8601 formatted dates returned by the AI.

        Args:
            input_text (str): The input string representing the date to resolve.
                The input can be in formats compatible with `dateparser` or in special
                formats (e.g., BCE or future years).

        Returns:
            Union[datetime, Decimal, None]:
                - `datetime` object if a valid date is resolved.
                - `Decimal` representing seconds for future events or years before the common era.
                - `None` if the date cannot be resolved.

        Raises:
            ValueError: If both `dateparser` and the AI approach fail to resolve a date.

        Example:
            >>> resolve_date("2024-12-11")
            datetime.datetime(2024, 12, 11, 0, 0, tzinfo=datetime.timezone.utc)

            >>> resolve_date("-44")  # 44 BCE
            Decimal('-69422400000')

            >>> resolve_date("+10")  # 10 years from now
            Decimal('315569520')

        Notes:
            - The function first attempts to parse the date using the `resolve_date_dateparser`
              function. If that fails, it invokes the AI-based date generator.
            - The AI response is expected to be one of:
                - A valid ISO 8601 date string.
                - A negative number representing historical years (BCE).
                - A positive number indicating future years (converted to seconds).
            - Historical dates are converted into seconds using a year-based approximation
              or ISO 8601 representation when available.
            - Future dates are expressed in seconds from the current time.
        """
        # First, try to parse using dateparser
        resolved_date = resolve_date_dateparser(input_text)
        if resolved_date:
            return resolved_date

        # If parsing fails, fallback to AI
        ai_result = self.generate_date(input_text)
        if ai_result == "UNKNOWN":
            raise ValueError(f"Unable to resolve date for input: {input_text}")

        # Handle AI response for historical dates
        if ai_result.startswith("-"):
            if ai_result.count("-") == 3:  # -YYYY-MM-DD
                epoch = constants.UNIX_DATE
                bc_date = datetime.strptime(ai_result, "-%Y-%m-%d")
                delta_years = epoch.year + abs(bc_date.year) - 1
                delta_days = (epoch - epoch.replace(year=epoch.year, month=1, day=1)).days
                return -Decimal(
                    (delta_years * Decimal(365.25) + delta_days) * constants.SECONDS_IN_DAY
                )
            # -YYYYYYYY or -1.5e9
            epoch = constants.UNIX_DATE
            return -Decimal(
                Decimal(epoch.year + abs(Decimal(ai_result)) - 1) * constants.SECONDS_IN_YEAR
            )

        # Handle AI response for future events
        if ai_result.startswith("+"):
            return Decimal(Decimal(ai_result) * constants.SECONDS_IN_YEAR)
        try:
            # If the AI produces a valid ISO 8601 timestamp
            return datetime.fromisoformat(ai_result)
        except ValueError:  # pragma: no cover
            return ai_result
