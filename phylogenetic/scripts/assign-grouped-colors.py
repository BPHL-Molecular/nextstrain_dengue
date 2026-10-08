#!/usr/bin/env python3

import argparse
import csv
import sys
from collections import OrderedDict

UNGROUPED = "Other"


def parse_args():
    parser = argparse.ArgumentParser(description="Assign colors to high-cardinality metadata columns.")
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--ordering", required=True, help="color_orderings.tsv")
    parser.add_argument("--color-schemes", required=True)
    parser.add_argument(
        "--grouped-columns",
        nargs="+",
        default=["country", "country_exposure"],
        help="columns whose values are grouped by region before being coloured",
    )
    parser.add_argument(
        "--flat-columns",
        nargs="+",
        default=["location"],
        help="columns coloured from a single ramp, with cycling if needed",
    )
    parser.add_argument("--output", default="-")
    return parser.parse_args()


def read_region_of_country(path):
    with open(path, encoding="utf-8") as handle:
        lines = handle.read().splitlines()

    regions = {
        line.split("\t", 1)[1].strip() for line in lines if line.startswith("region\t")
    }

    region_of = {}
    position = {}
    region = UNGROUPED
    for index, line in enumerate(lines):
        if line.startswith("#"):
            label = line.lstrip("#").strip()
            if label in regions:
                region = label
        elif line.startswith("country\t"):
            country = line.split("\t", 1)[1].strip()
            region_of.setdefault(country, region)
            position.setdefault(country, index)
    return region_of, position


def read_schemes(path):
    schemes = {}
    with open(path, encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            line = line.strip()
            if line:
                schemes[number] = line.split("\t")
    return schemes


def palette(schemes, count):
    if count < 1:
        return []
    largest = max(schemes)
    if count <= largest:
        return schemes[count]

    colors = []
    remaining = count
    while remaining > largest:
        colors.extend(schemes[largest])
        remaining -= largest
    colors.extend(schemes[remaining])
    return colors


def observed_values(rows, column):
    values = OrderedDict()
    for row in rows:
        value = (row.get(column) or "").strip()
        if value and value != "?":
            values[value] = None
    return list(values)


def main():
    args = parse_args()

    region_of, position = read_region_of_country(args.ordering)
    schemes = read_schemes(args.color_schemes)

    with open(args.metadata, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))

    out = sys.stdout if args.output == "-" else open(args.output, "w", encoding="utf-8")
    try:
        groups = OrderedDict()
        for column in args.grouped_columns:
            for value in observed_values(rows, column):
                groups.setdefault(region_of.get(value, UNGROUPED), OrderedDict())[value] = None

        color_of = {}
        for region, values in groups.items():
            ordered = sorted(values, key=lambda v: (position.get(v, len(position)), v))
            color_of.update(zip(ordered, palette(schemes, len(ordered))))
            print(f"{len(ordered)} values in {region}", file=sys.stderr)

        for column in args.grouped_columns:
            values = observed_values(rows, column)
            if not values:
                print(f"{column}: no values found, skipping", file=sys.stderr)
            for value in values:
                out.write(f"{column}\t{value}\t{color_of[value]}\n")

        for column in args.flat_columns:
            values = sorted(observed_values(rows, column))
            if not values:
                print(f"{column}: no values found, skipping", file=sys.stderr)
                continue
            for value, color in zip(values, palette(schemes, len(values))):
                out.write(f"{column}\t{value}\t{color}\n")
            print(f"{column}: {len(values)} values, ungrouped", file=sys.stderr)
    finally:
        if out is not sys.stdout:
            out.close()


if __name__ == "__main__":
    main()
