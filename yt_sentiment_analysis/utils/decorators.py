from functools import wraps


def mapper(func):
    print('mapper')

    @wraps(func)
    # def inner(*args, **kwargs) -> list:
    def inner(list_of_values) -> list:
        return [func(x) for x in list_of_values]
    return inner


def mapper2(func):
    """
    Assume either a list or a singleton will be passed in.

    If 2 args, then
    """
    print('self callable?')
    print(func.__name__)
    print(callable(func))

    @wraps(func)
    def inner(self, *args, **kwargs) -> list:

        # if the first arg is not a list, try putting it in a list
        if not isinstance(args[0], list):
            list_of_values = args[0]
            return [func(x) for x in list_of_values]

        # if it's just a singleton
        elif type(args[0]) == dict:
            # list_of_values = [args[0]]

            return func(args[0])
        else:
            return "Not supported"
    return inner
