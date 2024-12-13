
import os
import pytest

def pytest_collection_modifyitems(config, items):
    if os.getenv("CI") == "true":
        # Define the file and test(s) to run in CI
        target_file = "test_ai.py"  # Replace with the name of your test file
        tests_to_run_in_ci = {"test_ai_generate_date_ww2"}  # Add test names here

        # Iterate over all collected tests
        for item in items:
            # Check if the test is in the target file
            if target_file in str(item.fspath):
                # Skip the test if it's not in the list to run
                if item.name not in tests_to_run_in_ci:
                    item.add_marker(
                        pytest.mark.skip(reason="Skipping test to avoid API rate limit on CI")
                    )
