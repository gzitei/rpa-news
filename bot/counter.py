def counter():
    count: int = -1

    def increment():
        nonlocal count
        count += 1
        return count

    return increment
