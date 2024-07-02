def get_tokens_batches(addresses: list) -> list:
    max_batch = 30
    batches = []
    addresses = list(set(addresses))
    for i in range(0, len(addresses), max_batch):
        batches.append(addresses[i:i + max_batch])
    return batches
