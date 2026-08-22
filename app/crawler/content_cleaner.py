"""Readable content extraction from crawled HTML."""

from bs4 import BeautifulSoup


def extract_page_content(html: str) -> tuple[str, str]:
    """Return a page title and whitespace-normalized readable text."""

    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    for element in soup(["script", "style", "noscript", "template", "svg"]):
        element.decompose()
    content = " ".join(soup.stripped_strings)
    return title, content