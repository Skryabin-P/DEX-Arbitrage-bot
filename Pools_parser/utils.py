import requests, json


def collect_tokens(addresses: list) -> list:
    max_batch = 30
    addresses = set(addresses)
