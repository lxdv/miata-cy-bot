import cloudscraper
from bs4 import BeautifulSoup


def get_from_bazaraki(
    url="https://www.bazaraki.com/car-motorbikes-boats-and-parts/cars-trucks-and-vans/mazda/mazda-mx5/",
):
    with cloudscraper.create_scraper() as scraper:
        response = scraper.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        ads = soup.find_all("a", href=True, text=lambda t: t and "Mazda MX5" in t)

        results = []
        for tag in ads:
            title = tag.text.strip()
            link = "https://www.bazaraki.com" + tag["href"]
            results.append((title, link))
        return results
