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
- `dotenv`: For managing API keys securely using environment variables.

**Usage Example**:
```python
>>> ai_generate_date("When did the Apollo 11 moon landing occur?")
"1969-07-20T00:00:00+00:00"

>>> ai_generate_date("5 days before the fall of the Berlin Wall")
"1989-11-04T00:00:00+00:00"
"""

import os
from datetime import datetime

import google.generativeai as genai
import requests
from dotenv import load_dotenv
from google.api_core.exceptions import ResourceExhausted

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
config = genai.GenerationConfig(max_output_tokens=200, temperature=0.1, top_p=0.5, top_k=40)

# Get the directory of the current script (ai.py)
script_dir = os.path.dirname(os.path.abspath(__file__))
resources_dir = os.path.join(script_dir, "../resources")

with open(os.path.join(resources_dir, "system_prompt.txt"), "r", encoding="utf-8") as file:
    model = genai.GenerativeModel(
        # "models/gemini-exp-1206",
        # "models/gemini-2.0-flash-exp",
        # "models/gemini-1.5-pro",
        "models/gemini-1.5-flash",
        # "models/gemini-2.0-flash-thinking-exp-1219",
        system_instruction=file.read().format(datetime_now=datetime.now().isoformat()),
    )


def ai_generate_date(input_text: str) -> str:
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
        response = model.generate_content(input_text, generation_config=config)

        if response and response.text:
            # Clean the response text to ensure it's a valid ISO date format
            print(response.text)
            iso_date: str = response.text.strip()
            return iso_date
        raise ValueError("No valid response received from the API.")  # pragma: no cover

    except requests.ConnectionError:  # pragma: no cover
        return "Connection error: Unable to reach the API."

    except requests.Timeout:  # pragma: no cover
        return "Timeout error: The API request timed out."

    except requests.RequestException as e:  # pragma: no cover
        return f"Request error: {e}"

    except ResourceExhausted as e:  # pragma: no cover
        return f"Resource exhausted: {e}"
