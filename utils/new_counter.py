def new_counter():
    count: int = 0

    def increment() -> int:
        nonlocal count
        count += 1
        return count

    return increment
