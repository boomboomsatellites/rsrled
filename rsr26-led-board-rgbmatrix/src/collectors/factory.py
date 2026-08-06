from src.collectors.mock_collector import MockCollector
from src.collectors.twscrape_collector import TwscrapeCollector


def create_collector(cfg):
    collector_type = cfg.get('collector', {}).get('type', 'mock')
    if collector_type == 'mock':
        return MockCollector()
    if collector_type == 'twscrape':
        return TwscrapeCollector(cfg)
    raise ValueError(f'Unknown collector type: {collector_type}')
