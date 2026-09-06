import argparse

from fc27trader.collectors.manual_import import load_market_csv

parser = argparse.ArgumentParser()
parser.add_argument("path")
args = parser.parse_args()
rows = load_market_csv(args.path)
print(f"validated {len(rows)} manual PC market rows; persistence hook is next")
