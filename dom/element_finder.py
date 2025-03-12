def find_elements_by_attribute(dom_state, attribute, value):
    """
    Find and return all elements in the processed DOM state that have the specified attribute
    containing the given value.

    Args:
        dom_state (dict): The processed DOM state (from dom_processor.process_dom).
        attribute (str): The attribute name to search for (e.g., "id", "class").
        value (str): The value or substring to match within the attribute.

    Returns:
        list: A list of elements (dicts) matching the criteria.
    """
    results = []
    for element in dom_state.get("elements", []):
        attrs = element.get("attributes", {})
        # Check if the attribute exists and contains the search value (case-insensitive)
        if attribute in attrs and value.lower() in str(attrs[attribute]).lower():
            results.append(element)
    return results


def find_elements_by_tag(dom_state, tag_name):
    """
    Find and return all elements in the processed DOM state with the given tag name.

    Args:
        dom_state (dict): The processed DOM state (from dom_processor.process_dom).
        tag_name (str): The tag name to search for (e.g., "button", "input").

    Returns:
        list: A list of elements (dicts) with the specified tag name.
    """
    return [
        element for element in dom_state.get("elements", [])
        if element.get("tag", "").lower() == tag_name.lower()
    ]


# For testing purposes:
if __name__ == "__main__":
    # Example DOM state from the dom_processor
    sample_dom_state = {
        "elements": [
            {"tag": "a", "attributes": {"href": "https://example.com", "class": "link"}, "text": "Example Link"},
            {"tag": "button", "attributes": {"id": "submitBtn", "class": "btn primary"}, "text": "Submit"},
            {"tag": "input", "attributes": {"name": "username", "type": "text"}, "text": ""},
        ],
        "raw_html": "<html>...</html>"
    }

    # Find elements by attribute
    links = find_elements_by_attribute(sample_dom_state, "href", "example.com")
    print("Elements with 'href' containing 'example.com':", links)

    # Find elements by tag
    buttons = find_elements_by_tag(sample_dom_state, "button")
    print("Button elements:", buttons)
