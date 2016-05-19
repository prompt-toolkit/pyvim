FILE_FILTER_FUNCTIONS = {}


def has_file_filter_handler(command):
    return command in FILE_FILTER_FUNCTIONS


def call_file_filter_handler(filter, filename):
    """
    Execute command.
    """
    FILE_FILTER_FUNCTIONS[filter](filename)


def get_file_filters():
    return FILE_FILTER_FUNCTIONS.keys()


def add_file_filter(name):
    """
    Decorator that registers a function that takes a filename as a
    parameter and returns True if valid.

    To use, in your ~/.pyvimrc::

        from pyvim.file_filter import file_filter

        @file_filter('filtername')
        def _(filename):
            return not filename.endswith('.pyc')
    """
    def decorator(func):
        FILE_FILTER_FUNCTIONS[name] = func
        return func
    return decorator


def file_filter(filename):
    if not get_file_filters():
        return True
    return all(
        func(filename)
        for filter, func in FILE_FILTER_FUNCTIONS.items()
    )
