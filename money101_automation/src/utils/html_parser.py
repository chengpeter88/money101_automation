def parse_html(html_content):
    """Parse HTML content and extract relevant information."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_content, 'html.parser')
    data = {}

    # Example of extracting specific data
    data['title'] = soup.title.string if soup.title else 'No title found'
    data['headings'] = [h.get_text() for h in soup.find_all(['h1', 'h2', 'h3'])]
    
    return data

def extract_card_info(card_element):
    """Extract information from a credit card HTML element."""
    card_info = {}
    card_info['name'] = card_element.find('h3').get_text(strip=True)
    card_info['details'] = card_element.find('p', class_='details').get_text(strip=True)
    return card_info

def extract_loan_info(loan_element):
    """Extract information from a loan HTML element."""
    loan_info = {}
    loan_info['name'] = loan_element.find('h3').get_text(strip=True)
    loan_info['interest_rate'] = loan_element.find('span', class_='interest-rate').get_text(strip=True)
    return loan_info