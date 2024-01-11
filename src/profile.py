from functools import wraps
from typing import Callable, Any, Optional
from simple_profile import MemoryUnit, TimeUnit
from simple_profile.decorators import wraps_top_level
from simple_profile.utils import measure_average_execution_time, measure_peak_memory_usage


def my_simple_profile(
    name: Optional[str] = None,
    iterations=1,
    print_args=False,
    print_result=False,
    separator=" | ",
    memory_unit: Optional[MemoryUnit] = None,
    memory_precision=4,
    time_unit: Optional[TimeUnit] = None,
    time_precision=4,
    precision: Optional[int] = None,
    enable_gc=False
):
    """
    Logs the peak memory usage and the average execution time of each function call.
    :param name: the name to use in the logs
    :param iterations: the number of times to execute the function call
    :param print_args: whether to log the arguments
    :param print_result: whether to log the result
    :param separator: the separator to use between log values
    :param memory_unit: the memory unit to use
    :param memory_precision: the memory precision to use (in number of significant digits)
    :param time_unit: the time unit to use
    :param time_precision: the time precision to use (in number of significant digits)
    :param precision: the precision to use for all values (in number of significant digits)
    :param enable_gc: whether to enable garbage collection during the measurement
    :return: the decorated function
    """
    if precision is not None:
        memory_precision = precision
        time_precision = precision

    def decorator(function: Callable):
        @wraps_top_level(function)
        @wraps(function)
        def wrapper(*args: Any, **kwargs: Any):
            peak_memory_usage, result = measure_peak_memory_usage(function, args, kwargs)
            average_execution_time = measure_average_execution_time(function, args, kwargs, iterations, enable_gc)

            return result, peak_memory_usage, average_execution_time

        return wrapper

    return decorator
