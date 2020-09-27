import requests
import json
from bs4 import BeautifulSoup


def update_results(results, tab_id: str, tab_name: str, section_name: str, link_text: str, link_url: str):
    record = {
        "tab_id": tab_id,
        "tab_name": tab_name,
        "section_name": section_name,
        "text": link_text,
        "url": link_url
        }
    results.append(record)


def get_raif_disclosure_docs():

    root_url = "https://www.raiffeisen.ru"
    disclosure_url = root_url + "/about/investors/disclosure/"
    results = []

    try:
        req = requests.get(disclosure_url)
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError):
        return []

    soup = BeautifulSoup(req.text, 'html.parser')

    # Get the tabs names as a dict {tab_id: tab_name}
    s_tabs_div = soup.find('div', attrs={'class': 'b-tabs loaded-block', 'id': 'tabs-1'})
    tabs_names = {}
    for item in s_tabs_div.find_all('li'):
        tabs_names[item.get('data-tab')] = item.get_text(separator=" ").strip()

    # Parse data from the specific tab
    for tab_id, tab_name in tabs_names.items():
        s_tab_data = soup.find('div', attrs={'class': 'b-tabs-items__item', 'id': tab_id})
        if s_tab_data:
            # Parse divs "b-block-text" for current tab
            for block_item in s_tab_data.find_all('div', attrs={'class': 'b-block-text'}, recursive=False):
                s_block_text_accordion = block_item.find('div', attrs={'class': 'accordion'})
                if not s_block_text_accordion:
                    # Parse div "b-block-text" --> links
                    for link in block_item.find_all('a'):
                        link_text = " ".join(link.get_text(separator=" ").split())
                        update_results(results, tab_id, tab_name, "", link_text, root_url + link.get('href'))
                else:
                    # Parse div "b-block-text" --> div "accordion" --> div "accordion_section"
                    s_accordion_sections = s_block_text_accordion.find_all('div', attrs={'class': 'accordion__section'})
                    for s_accordion_section in s_accordion_sections:
                        s_spoiler_head = s_accordion_section.find('div', attrs={'class': 'accordion__head'})
                        spoiler_title = s_spoiler_head.text.strip()
                        # Parse ... --> div "accordion_section" --> div "tips-links-content"
                        s_tips_links_items = s_accordion_section.find_all('div', attrs={'class': 'tips__links-content'})
                        for s_tips_links_item in s_tips_links_items:
                            link_text = " ".join(s_tips_links_item.get_text(separator=" ").split())
                            link_url = s_tips_links_item.find('a').get('href')
                            update_results(results, tab_id, tab_name, spoiler_title, link_text, root_url + link_url)
                        # Parse ... --> div "accordion_section" --> div "tips"
                        for s_tips_item in s_accordion_section.find_all('div', attrs={'class': 'tips'}):
                            spoiler_tab_title = ""
                            spoiler_tab_subtitle = ""
                            s_spoiler_tab_title = s_tips_item.find('h2', attrs={'class': 'e-title'})
                            if s_spoiler_tab_title:
                                spoiler_tab_title_raw = s_spoiler_tab_title.get_text(separator=" ")
                                spoiler_tab_title = ", " + " ".join(spoiler_tab_title_raw.split())
                            for s_tips_content_item in s_tips_item.find_all('div', attrs={'class': 'tips__content'}):
                                s_spoiler_tab_subtitle = s_tips_content_item.find('div', attrs={'class': 'tips__title'})
                                if s_spoiler_tab_subtitle:
                                    spoiler_tab_subtitle_raw = s_spoiler_tab_subtitle.get_text(separator=" ")
                                    spoiler_tab_subtitle = ", " + " ".join(spoiler_tab_subtitle_raw.split())
                                for s_tips_links_item in s_tips_content_item.find_all('a',
                                                                                attrs={'class': 'tips__links-content'}):
                                    sec_name = spoiler_title + spoiler_tab_title + spoiler_tab_subtitle
                                    link_text = " ".join(s_tips_links_item.get_text(separator=" ").split())
                                    link_url = s_tips_links_item.get('href')
                                    update_results(results, tab_id, tab_name, sec_name, link_text, root_url + link_url)

            # Parse divs "b-tabs-items" for current tab
            for block_item in s_tab_data.find_all('div', attrs={'class': 'b-tabs-items'}, recursive=False):
                # Parse nested tab (years)
                for nested_tab_item in s_tab_data.find_all('div', attrs={'class': 'b-tabs-items__item'}):
                    # Get title for nested tab
                    nested_tab_name = nested_tab_item.find('div', attrs={'class': 'tips__title'}).text.strip()
                    # Parse div "b-tabs-items" --> div "b-tabs-items__item" --> links
                    for link in nested_tab_item.find_all('a'):
                        link_text = " ".join(link.get_text(separator=" ").split())
                        update_results(results, tab_id, tab_name, nested_tab_name,
                                       link_text, root_url + link.get('href'))
    return results


if __name__ == "__main__":
    raif_disclosure = get_raif_disclosure_docs()
    print(json.dumps(raif_disclosure, indent=2, ensure_ascii=False))
    # with open("raif_disclosure.log", "w") as f:
    #     f.write(json.dumps(raif_disclosure, indent=2, ensure_ascii=False))
