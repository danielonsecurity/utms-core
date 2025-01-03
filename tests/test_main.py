import subprocess


def test_main_entry_point():
    """Test the application entry point."""
    result = subprocess.run(
        ["python", "-m", "utms"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Welcome to UTMS CLI" in result.stdout
