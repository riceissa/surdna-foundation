#!/usr/bin/env python3

import csv
import requests
import sys
from bs4 import BeautifulSoup

def main():
    if len(sys.argv) != 1+1:
        print("Unexpected arg count. Please specify output file.")
        sys.exit()

    url_base = "https://surdna.org/grants-database/{}/"
    page = 1

    with open(sys.argv[1], "w", newline="") as f:
        fieldnames = ["organization", "organization_url", "project_summary",
                      "year_approved", "status", "amount", "duration"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        while True:
            print("On page " + str(page), file=sys.stderr)
            url = url_base.format(page)
            r = requests.get(url)
            soup = BeautifulSoup(r.content, "lxml")

            if soup.body.find_all(text="No Results Found"):
                break

            tables = soup.find_all("table")
            # See comment below -- Surdna Foundation website has a bug where a
            # nested table appears in one of the pages, so this assertion
            # fails.
            # assert len(tables) == 1, "Error: there must be exactly one grants table on the page"
            table = tables[0]

            headers_found = list(map(lambda x: x.text.strip(), table.find_all("th")))
            headers_expected = ['Year Approved', 'Organization', 'Status', 'Amount',
                                'Duration']
            assert headers_found == headers_expected
            # Build header access map so that we can say cells[h[key]] rather than
            # cells[idx]
            h = {key: idx for idx, key in enumerate(headers_expected)}

            # The Surdna Foundation website has a strange bug on page 24 where
            # one cell has a nested table in it, which messes up a naive
            # iteration using find_all("tr"). So instead we loop through the
            # children and filter for "tr" tags to get the rows.
            for child in table.find("tbody").children:
                if child.name != "tr":
                    continue
                cells = list(filter(lambda t: t.name == "td", child.children))
                year_approved = cells[h["Year Approved"]].text.strip()
                status = cells[h["Status"]].text.strip()
                amount = cells[h["Amount"]].text.strip()
                duration = cells[h["Duration"]].text.strip()

                org_name = cells[h["Organization"]].find("span")
                org_url = ""
                try:
                    org_url = org_name.a.get("href")
                except AttributeError:
                    pass
                # There is an SVG tag that we don't want, so destroy it
                org_name.svg.decompose()
                org_name = org_name.text.strip()

                project_summary = cells[h["Organization"]].find("div", {"class": "project-summary"}).text.strip()

                writer.writerow({
                    "organization": org_name,
                    "organization_url": org_url,
                    "project_summary": project_summary,
                    "year_approved": year_approved,
                    "status": status,
                    "amount": amount,
                    "duration": duration,
                })

            page += 1


if __name__ == "__main__":
    main()
