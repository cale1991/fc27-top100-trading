from fc27trader.scheduler.tasks import collect_ea_news


def collect_once() -> None:
    print(collect_ea_news.run(26))
