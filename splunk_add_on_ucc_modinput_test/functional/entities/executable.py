import inspect


class ExecutableBase:
    def __init__(self, function):
        assert callable(function)
        self._function = function
        self._inspect()

    @property
    def source_file(self):
        return self._fn_source_file

    @property
    def key(self):
        return (self._fn_source_file, self.fn_full_name)

    @property
    def original_name(self):
        if self._original_name == "__call__":
            return self._fn_bound_class.lower()
        return self._original_name

    @property
    def fn_full_name(self):
        if self._fn_bound_class:
            return f"{self._fn_bound_class}::{self._fn_name}"
        else:
            return self._fn_name

    def _inspect(self):
        if inspect.ismethod(self._function):
            self._fn_bound_class = self._function.__self__.__class__.__name__
            self._fn_name = self._function.__name__
            self._fn_source_file = inspect.getfile(self._function)
        elif inspect.isfunction(self._function):
            self._fn_bound_class = None
            res = repr(self._function).split(" ")[1].split(".")
            if len(res) > 1:
                self._fn_bound_class = res[0]
                self._fn_name = res[1]
            else:
                self._fn_name = res[0]
            self._fn_source_file = inspect.getfile(self._function)
        else:
            self._fn_name = "__call__"
            self._fn_bound_class = self._function.__class__.__name__
            self._fn_source_file = inspect.getfile(self._function.__class__)

        self._original_name = self._fn_name
        self._is_generatorfunction = inspect.isgeneratorfunction(
            self._function
        )

        sig = inspect.signature(self._function)
        self._required_args = list(sig.parameters.keys())

    @property
    def required_args_names(self):
        return tuple(self._required_args)

    def filter_requied_kwargs(self, kwargs):
        return {k: v for k, v in kwargs.items() if k in self._required_args}
