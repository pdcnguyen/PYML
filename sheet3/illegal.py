"""
A module that provides a context manager, in which functions can be declared illegal
and will throw an exception when called
"""

from warnings import warn


class IllegalFunctionException(
    RuntimeError
):  # pylint: disable=missing-docstring,missing-docstring
    pass


class IllegalFunction:
    """
    Class for dummy functions that replace functions that have to made illegal
    """

    def __init__(self, func):
        self.name = func.__name__

    def __call__(self, *args, **kwargs):
        raise IllegalFunctionException(f"Used illegal function: {self.name}")


class CounterFunction:
    def __init__(self, func):
        self.name = func.__name__
        self.func = func
        self.count = 0

    def __call__(self, *args, **kwargs):
        self.count += 1
        print(self.name, "called")
        return self.func(*args, **kwargs)


class IllegalContext:
    """
    A context manager that makes some functions illegal
    that will throw an exception when they are run

    Instance Attributes:
        illegals (list): List of tuples, where in each tuple
            the first element is the module of the function
            and the second element is the name of the function
            as a string
        global_var (dict): The global variables `globals()` in the calling module
            If no global variables should be overwritten an empty dict can be
            provided as input
    """

    def __init__(self, illegals, global_variables):
        self.illegals = illegals
        self.global_variables = global_variables
        self.override_type = IllegalFunction
        self.overwritten_functions = dict()
        self.overwritten_globals = dict()

    def __enter__(self):
        # make all the functions illegal
        for module, function_name in self.illegals:
            self._overwrite_function(module, function_name, self.global_variables)

    def __exit__(self, *args, **kwargs):
        for module, function_name in self.illegals:
            self._reset_function(module, function_name, self.global_variables)

        # we want to propagate any exceptions so return false
        return False

    def _overwrite_function(self, module, function_name, global_vars):
        func = getattr(module, function_name)
        # overwrite function from module
        self._overwrite_function_from_module(module, function_name)
        # overwrite any globals that have the same value as this function
        self._overwrite_global_with_value(global_vars, function_name, func)
        return True

    def _overwrite_function_from_module(self, module, function_name):
        # don't forget the original function
        old_func = getattr(module, function_name)
        self.overwritten_functions[(module, function_name)] = old_func
        setattr(module, function_name, self.override_type(old_func))
        return old_func

    def _overwrite_global_with_value(self, glob_var, function_name, function):
        for name, value in glob_var.items():
            if callable(value) and value == function:
                self.overwritten_globals[name] = value
                glob_var[name] = self.override_type(function_name)

    def _reset_function(self, module, function_name, global_vars):
        func = getattr(module, function_name)
        if not isinstance(func, self.override_type):
            warn("This function is not illegal")
            return False

        # reset the function in the module
        original_function = self._reset_function_in_module(module, function_name)
        # reset the function in the all the global variables
        self._reset_global_with_value(global_vars, original_function)
        return True

    def _reset_function_in_module(self, module, function_name):
        original_function = self.overwritten_functions[(module, function_name)]
        setattr(module, function_name, original_function)
        return original_function

    def _reset_global_with_value(self, glob_var, function):
        for var_name in glob_var:
            if (
                var_name in self.overwritten_globals
                and self.overwritten_globals[var_name] == function
            ):
                glob_var[var_name] = function


def create_no_loop_illegals(numpy_module, builtins_module):
    """
    Creates a list of illegal functions that simulate
    a for loop in Python/Numpy

    Args:
        numpy_module (module): The numpy module
        builtins_module (module): The builtins module

    Returns:
        list: List of illegal tuples
    """
    return [
        (numpy_module, "vectorize"),
        (numpy_module, "fromiter"),
        (numpy_module, "fromfunction"),
        (numpy_module, "apply_along_axis"),
        (builtins_module, "map"),
        (builtins_module, "sum"),
        (builtins_module, "filter"),
    ]
