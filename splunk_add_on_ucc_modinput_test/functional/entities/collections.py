from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.entities.executable import ExecutableBase



class FrmwrkFunctionCollection(dict):
    def add(self, item):
        assert isinstance(item, ExecutableBase)
        if item.key not in self:
            self[item.key] = item

    def _get_item_key(self, item):
        if isinstance(item, ExecutableBase):
            return item.key
        elif isinstance(item, str):
            return item

        assert True, "Instance of FrameworkTest or str is expected as test argument"

    def lookup_by_function(self, fn):
        function = ExecutableBase(fn)
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
