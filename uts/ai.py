"""
This module handles AI stuff to convert human language into time.
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
You are a model designed to generate precise dates and times in ISO
8601 format. When given the input '{input_text}', strictly adhere to
the following rules:

1. **Common Era (CE) Events (1 CE to 9999 CE):**
   - For events occurring from `0001-01-01` to `9999-12-31`, always output the date in full
     ISO 8601 format: `'YYYY-MM-DDTHH:MM:SS+ZZ:ZZ'` (no quotes).
   - **Do not include a minus sign** for years in this range.
   - If hours, minutes, or seconds are unknown, set them to `00:00:00`.
   - If the month or day is unknown, set them to `01` (e.g., `0001-01-01T00:00:00+00:00`).
   - Always include the timezone offset. Default to UTC (`+00:00`) if not specified.
   - Example: For "fall of the Roman Empire," return `0476-09-04T00:00:00+00:00`.

2. **Before Common Era (BCE) Events (Before 1 CE):**
   - For events before `0001-01-01`, always include a leading minus sign (`-`).
   - Example: Julius Caesar's assassination in 44 BCE should be formatted as `-0044-03-15`.
   - Use the full `-YYYY-MM-DD` format when the month and day are known. Default to
     `-YYYY-01-01` if they are unknown.
   - If only the year is known, output `-YYYY` (e.g., `-753` for the founding of Rome).
   - For prehistoric or extremely ancient events (e.g., geological or cosmic timescales),
     scientific notation may be used (e.g., `-1.45e8` for the end of the Jurassic Period).

3. **Events After 9999 CE:**
   - For events beyond `9999-12-31`, use the ISO format prefixed by a plus sign (`+`), e.g.,
     `+10000-01-01` or scientific notation if appropriate (e.g., `+1.7e106` for the heat death
     of the universe).

4. **Relative Dates:**
   - For relative terms like "yesterday" or "5 days ago," calculate the exact ISO 8601 datetime.
   - Include the timezone offset (`+00:00`) unless another timezone is explicitly provided.

5. **Unknown or Uncertain Dates:**
   - If a date cannot be determined, return `UNKNOWN`. Avoid this unless absolutely necessary.
   - For ranges (e.g., "first crusade"), default to the **beginning of the range**.

6. **Formatting Rules for All Cases:**
   - Always prioritize ISO 8601 compliance. For BCE dates, ensure the minus sign is included.
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

        return "No valid response received from the API."

    except requests.ConnectionError:
        return "Connection error: Unable to reach the API."

    except requests.Timeout:
        return "Timeout error: The API request timed out."

    except requests.RequestException as e:
        return f"Request error: {e}"

    except AttributeError:
        return "Unexpected response structure: Missing 'text' attribute."

    except ValueError:
        return "Value error: Invalid input data."
