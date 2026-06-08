from bs4 import BeautifulSoup


class PageParser:
    @staticmethod
    def parse(html: str):
        soup = BeautifulSoup(html, "lxml")

        title = soup.title.text.strip() if soup.title else "N/A"

        return {
            "title": title,
        }
