def print_row(items_list, separator="   "):
    """Prints a row of items with formatting."""
    formatted_items = []
    for items in items_list:
        formatted_items.append(f"{items}")
    print(separator.join(formatted_items))

