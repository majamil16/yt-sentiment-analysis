from functools import wraps


def mapper(func):
    print('mapper')

    @wraps(func)
    def inner(list_of_values: list) -> list:
        print('inner')
        return [func(x) for x in list_of_values]
    return inner
