import requests
from bs4 import BeautifulSoup

def scrape():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/138.0.0.0 Safari/537.36"
        )
    }

    # List of (city, bounds) tuples
    bounds = [
        ("Gradignan", "bounds=-0.6471483_44.7938687_-0.5854508_44.7423986"),
        ("Talence", "bounds=-0.6111634_44.8252468_-0.5726706_44.7868187"),
        ("Mérignac", "bounds=-0.7569779_44.8627846_-0.6069396_44.7998378"),
        ("Pessac", "bounds=-0.7587897_44.8225797_-0.6029478_44.749435"),       
    ]

    base_url = "https://trouverunlogement.lescrous.fr/tools/41/search"

    all_results = []  # List of (city, listings) tuples

    for city, bound in bounds:
        url = f"{base_url}?{bound}"
        print(f"Fetching URL: {url}")

        resp = requests.get(url, headers=headers)
        if not resp.ok:
            print(f"Failed to fetch {url}: HTTP {resp.status_code}")
            continue

        soup = BeautifulSoup(resp.text, "html.parser")

        ul = soup.select_one(
            "#main > div.fr-container.fr-mt-8v.fr-mt-md-14v > div.fr-grid-row.fr-mt-md-1w "
            "> div.fr-col-12.SearchResults-container.svelte-8mr8g.fr-col-lg-9 "
            "> div.fr-grid-row.offsetCollapseFilter.svelte-8mr8g > div > ul"
        )

        if ul is None:
            print(f"No <ul> container found for {city}.")
            continue

        listings = []

        for li in ul.find_all("li", recursive=False):
            a_tag = li.select_one("div > div.fr-card__body > div > h3 > a")
            if a_tag:
                link_text = a_tag.get_text(strip=True)
                link_href = a_tag.get("href")
                full_link = f"https://trouverunlogement.lescrous.fr/{link_href}"
                listings.append((link_text, full_link))
            else:
                print(f"Warning: <a> tag missing in a listing for {city}.")

        all_results.append((city, listings))

    return all_results

    
import json
import os

def compare_results(new_results, json_path="previous_results.json"):
    """
    Compare new_results with saved JSON, return dicts of new and removed listings.
    """
    # Load previous results if they exist
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            old_results = json.load(f)
    else:
        old_results = []

    # Convert to dicts for easier comparison
    old_dict = dict(old_results)
    new_dict = dict(new_results)

    new_entries = {}
    removed_entries = {}

    for city, listings in new_dict.items():
        old_listings = old_dict.get(city, [])
        old_links = {link for _, link in old_listings}
        new_links = {link for _, link in listings}

        # New listings
        new_links_set = new_links - old_links
        new_entries[city] = [item for item in listings if item[1] in new_links_set]

        # Removed listings
        removed_links_set = old_links - new_links
        removed_entries[city] = [item for item in old_listings if item[1] in removed_links_set]

    return new_entries, removed_entries
def update_json(new_results, json_path="previous_results.json"):
    """
    Write the new results to JSON file.
    """
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(new_results, f, ensure_ascii=False, indent=2)
    print("Updated JSON saved.")

import requests

def notify_telegram(new_entries, removed_entries, bot_token, chat_id):
    """
    Send notifications to Telegram for new and removed listings.
    """
    base_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    # Notify about new listings
    for city, items in new_entries.items():
        if items:
            message = f"✅ Nouveaux logements trouvés pour *{city}*:\n"
            for text, link in items:
                message += f"- [{text}]({link})\n"

            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            r = requests.post(base_url, data=payload)
            if not r.ok:
                print(f"Telegram error for new listings: {r.text}")

    # Notify about removed listings
    for city, items in removed_entries.items():
        if items:
            message = f"❌ Logements supprimés pour *{city}*:\n"
            for text, _ in items:
                message += f"- {text}\n"

            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            r = requests.post(base_url, data=payload)
            if not r.ok:
                print(f"Telegram error for removed listings: {r.text}")
if __name__ == "__main__":
    # 1. Scrape
    results = scrape()

    # 2. Compare to previous
    new_entries, removed_entries = compare_results(results)

    # 3. Notify via Telegram
    notify_telegram(
        new_entries,
        removed_entries,
        bot_token="8096616407:AAGwZmmHxSkWBR7yb97HsAjw0AbryvhhP7U",
        chat_id="-4953065837"
    )

    # 4. Save the updated data
    update_json(results)

