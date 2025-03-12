from bs4 import BeautifulSoup

def process_dom(html_content):
    """
    Process the HTML content to extract a simplified DOM state.
    
    Extracts interactive elements (e.g., <a>, <button>, <input>, <select>, <textarea>) 
    and returns a dictionary with:
        - "elements": List of interactive elements with their tag, attributes, and text.
        - "raw_html": A snippet of the raw HTML (first 1000 characters) for context.
    
    Args:
        html_content (str): The HTML content as a string.
    
    Returns:
        dict: A dictionary containing the extracted elements and a snippet of the HTML.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    interactive_tags = ["a", "button", "input", "select", "textarea"]
    elements = []
    
    for tag in soup.find_all(interactive_tags):
        element_info = {
            "tag": tag.name,
            "attributes": tag.attrs,
            "text": tag.get_text(strip=True)
        }
        elements.append(element_info)
    
    return {
        "elements": elements,
        "raw_html": html_content[:1000]  # Limit snippet to first 1000 characters
    }

# For testing purposes:
if __name__ == "__main__":
    sample_html = """
    <html>
      <head><title>Test Page</title></head>
      <body>
        <h1>Welcome</h1>
        <a href="https://example.com">Example Link</a>
        <button id="btn1">Click me</button>
        <input type="text" name="username" />
      </body>
    </html>
    """
    dom_state = process_dom(sample_html)
    print("DOM State:", dom_state)
