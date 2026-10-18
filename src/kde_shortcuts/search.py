def score(query: str, text: str):
    query, text = query.casefold(), text.casefold()
    total = 0
    for token in query.split():
        if token in text:
            total += text.index(token)
            continue
        position = -1
        for char in token:
            position = text.find(char, position + 1)
            if position < 0:
                return None
            total += position + 10
    return total


def search(rows, query):
    matches = []
    for row in rows:
        rank = score(query, " ".join((row.action, row.application, row.category, *row.keys)))
        if rank is not None:
            matches.append((rank, row))
    return [row for _, row in sorted(matches, key=lambda pair: (pair[1].category, pair[0], pair[1].action.casefold()))]
