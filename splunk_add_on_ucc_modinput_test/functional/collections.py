import inspect
from splunk_add_on_ucc_modinput_test.functional import logger


class FrmwkFunction:
    def __init__(self, function):
        assert callable(function)
        self._function = function
        self._inspect()

    @property
    def source_file(self):
        return self._fn_source_file

    @property
    def key(self):
        if self._fn_bound_class:
            fn_full_name = f"{self._fn_bound_class}::{self._fn_name}"
        else:
            fn_full_name = self._fn_name

        return (self._fn_source_file, fn_full_name)

    @property
    def original_name(self):
        if self._original_name == "__call__":
            return self._fn_bound_class.lower()
        return self._original_name

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
            self._fn_name = f"__call__"
            self._fn_bound_class = self._function.__class__.__name__
            self._fn_source_file = inspect.getfile(self._function.__class__)

        self._original_name = self._fn_name
        self._is_generatorfunction = inspect.isgeneratorfunction(self._function)

        sig = inspect.signature(self._function)
        self._required_args = list(sig.parameters.keys())

    @property
    def required_args_names(self):
        return tuple(self._required_args)

    def filter_requied_kwargs(self, kwargs):
        return {k: v for k, v in kwargs.items() if k in self._required_args}


class FrmwrkFunctionCollection(dict):
    def add(self, item):
        assert isinstance(item, FrmwkFunction)
        if item.key not in self:
            self[item.key] = item

    def _get_item_key(self, item):
        if isinstance(item, FrmwkFunction):
            return item.key
        elif isinstance(item, str):
            return item

        assert True, "Instance of FrmwkTest or str is expected as test argument"

    def lookup_by_function(self, fn):
        function = FrmwkFunction(fn)
        if function in self:
            return self.__getitem__(function)
        return None

    def __getitem__(self, item):
        return super().__getitem__(self._get_item_key(item))

    def __contains__(self, item):
        return super().__contains__(self._get_item_key(item))


class TestCollection(FrmwrkFunctionCollection):
    pass


class DependencyCollection(FrmwrkFunctionCollection):
    pass
