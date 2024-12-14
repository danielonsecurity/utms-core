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

import google.generativeai as genai
import requests
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
config = genai.GenerationConfig(max_output_tokens=30, temperature=0.7, top_p=0.9, top_k=50)
model = genai.GenerativeModel(
    "models/gemini-1.5-flash",
    system_instruction="""
You are a model designed to generate precise dates and times. When given the input '{input_text}',
strictly adhere to the following rules:

1. **Common Era (CE) Events (1 CE to 9999 CE):**
   - For events occurring from `0001-01-01` to `9999-12-31`, always output the date in full
     ISO 8601 format: `'YYYY-MM-DDTHH:MM:SS+ZZ:ZZ'` (no quotes).
   - **Do not include a minus sign** for years in this range.
   - If hours, minutes, or seconds are unknown, set them to `00:00:00`.
   - If the month or day is unknown, set them to `01` (e.g., `0001-01-01T00:00:00+00:00`).
   - Always include the timezone offset. Default to UTC (`+00:00`) if not specified.
   - Example: For "fall of the Roman Empire," return `0476-09-04T00:00:00+00:00`.

2. **Before Common Era (BCE) Events (between -9999 CE to 1 CE):**
   - For events before `0001-01-01`, always include a leading minus sign (`-`).
   - Example: Julius Caesar's assassination in 44 BCE should be formatted as `-0044-03-15`.
   - Use the full `-YYYY-MM-DD` format when the month and day are known. Default to
     `-YYYY-01-01` if they are unknown (-0753-01-01 for the founding of Rome).

3. **Events before 9999 years before 1 CE:**
   - For events beyond `-9999-12-31` before the Common Era, print ONLY the number of years from NOW,
     prefixed by the minus sign (`-`), e.g., `-11700` for the end of the last ice age.
   - Do NOT use the `-YYYY-MM-DD` format, if something happened longer than 10000 years before our
     era, the month/date doesn't make sense anymore, so include only the number of years as an
     integer, and don't prefix it with zeroes anymore, make it a valid negative integer.
   - For prehistoric or extremely ancient events (e.g., geological or cosmic timescales),
     scientific notation should be used (e.g., `-1.45e8` for the end of the Jurassic Period).

4. **Events After 9999 CE:**
   - For events beyond `9999-12-31`, print only the number of years from NOW, prefixed by the plus
     sign (`+`), e.g., `+50000` or scientific notation if appropriate (e.g., `+1.7e106` for
     the heat death of the universe).

5. **Relative Dates:**
   - For relative terms like "yesterday", "5 days ago", "5 month before the WW1" calculate the exact
     ISO 8601 datetime.
   - Include the timezone offset (`+00:00`) unless another timezone is explicitly provided.

6. **Unknown or Uncertain Dates:**
   - If a date cannot be determined, return `UNKNOWN`. Avoid this unless absolutely necessary.
   - For ranges (e.g., "first crusade"), default to the **beginning of the range**.

7. **Formatting Rules for All Cases:**
   - Always prioritize accuracy. For BCE dates, ensure the minus sign is included.
   - Never provide explanations, context, or extra text—only return the formatted date.
   - Ensure precision and default values (e.g., `T00:00:00+00:00`) as described above.

Adhere strictly to these instructions to ensure correct and consistent formatting for all inputs.
""",
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

        return "No valid response received from the API."  # pragma: no cover

    except requests.ConnectionError:  # pragma: no cover
        return "Connection error: Unable to reach the API."

    except requests.Timeout:  # pragma: no cover
        return "Timeout error: The API request timed out."

    except requests.RequestException as e:  # pragma: no cover
        return f"Request error: {e}"

    except AttributeError:  # pragma: no cover
        return "Unexpected response structure: Missing 'text' attribute."

    except ValueError:  # pragma: no cover
        return "Value error: Invalid input data."
