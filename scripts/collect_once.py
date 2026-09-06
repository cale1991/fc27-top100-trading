import argparse

from fc27trader.scheduler.tasks import (
    collect_ea_news,
    collect_futzip_feed,
    collect_futzip_all,
    collect_futdb_reference_prices,
    collect_thecoinprinter_recent,
    collect_parse_futbin_catalogue,
    collect_parse_futbin_hot,
    sync_futdb_universe,
)

parser = argparse.ArgumentParser()
parser.add_argument("collector", choices=["ea26", "ea27", "tcp", "futdb-universe", "futdb-prices", "futzip-movers", "futzip-new", "futzip-sbc", "futzip-all", "parse-futbin-catalogue", "parse-futbin-hot"])
parser.add_argument("--max-pages", type=int, default=None)
args = parser.parse_args()

if args.collector == "ea26":
    print(collect_ea_news.run(26))
elif args.collector == "ea27":
    print(collect_ea_news.run(27))
elif args.collector == "tcp":
    print(collect_thecoinprinter_recent.run())
elif args.collector == "futzip-movers":
    print(collect_futzip_feed.run("movers"))
elif args.collector == "futzip-new":
    print(collect_futzip_feed.run("new"))
elif args.collector == "futzip-sbc":
    print(collect_futzip_feed.run("sbc"))
elif args.collector == "futzip-all":
    print(collect_futzip_all.run())
elif args.collector == "parse-futbin-catalogue":
    print(collect_parse_futbin_catalogue.run(args.max_pages or 1))
elif args.collector == "parse-futbin-hot":
    print(collect_parse_futbin_hot.run())
elif args.collector == "futdb-universe":
    print(sync_futdb_universe.run(args.max_pages))
else:
    print(collect_futdb_reference_prices.run())
