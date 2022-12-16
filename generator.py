#!/bin/python3
from datetime import datetime
from pathlib import Path
from json import load, dumps
import argparse

empty_sitemap_start = """<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">"""

empty_sitemap_end = "</urlset>"

empty_site = """<url>
    <loc>{}</loc>
    <lastmod>{}</lastmod>
</url>"""

base_url = "https://aral.nickwasused.com/station/{}"

def load_json(file):
    f = open(file, encoding="utf8")
    return load(f)

station_path = Path(__file__).parent.absolute().joinpath('stations.json')
output_path = Path(__file__).parent.absolute().joinpath('./static/sitemap.xml')
output_path_facilities = Path(__file__).parent.absolute().joinpath('./facilities.json')
output_path_fuel = Path(__file__).parent.absolute().joinpath('./fuel.json')

def generate_sitemap():
    station_data = load_json(station_path)
    now = datetime.now().strftime("%Y-%m-%dT00:00:00+00:00")
    with open(output_path, "w+") as f:
        f.write(empty_sitemap_start)
        for station in station_data:
            f.write(empty_site.format(base_url.format(station["id"]), now))
        f.write(empty_sitemap_end)

def export_facilities():
    station_data = load_json(station_path)
    unique_facilities = []
    for station in station_data:
        for facilitie in station["facilities"]:
            if facilitie not in unique_facilities:
                unique_facilities.append(facilitie)

    with open(output_path_facilities, "w+") as f:
        f.write(dumps(unique_facilities, indent=4))

def export_fuel():
    station_data = load_json(station_path)
    unique_fuel = []
    for station in station_data:
        for fuel in station["products"]:
            if fuel not in unique_fuel:
                unique_fuel.append(fuel)

    with open(output_path_fuel, "w+") as f:
        f.write(dumps(unique_fuel, indent=4))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="generator")
    parser.add_argument("-s", "--sitemap", help="generate sitemap", action="store_true")
    parser.add_argument("-f", "--facilities", help="generate unique facilities", action="store_true")
    parser.add_argument("-ff", "--fuel", help="generate unique fuel types", action="store_true")
    args = parser.parse_args()

    if args.sitemap:
        generate_sitemap()

    if args.facilities:
        export_facilities()

    if args.fuel:
        export_fuel()
