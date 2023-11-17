
import import_declare_test

from demo_addon_for_splunk_utils import Validator
from splunktaucclib.rest_handler.endpoint import (
    field,
    validator,
    RestModel,
    SingleModel,
)
from splunktaucclib.rest_handler import admin_external, util
from splunktaucclib.rest_handler.admin_external import AdminExternalHandler
import logging

util.remove_http_proxy_env_vars()


fields = [
    field.RestField(
        'uri',
        required=True,
        encrypted=False,
        default=None,
        validator=None
    )
]
model = RestModel(fields, name=None)


endpoint = SingleModel(
    'demo_addon_for_splunk_endpoint',
    model,
    config_name='endpoint'
)

class demo_addon_for_splunkExternalHandler(AdminExternalHandler):
    def __init__(self, *args, **kwargs):
        AdminExternalHandler.__init__(self, *args, **kwargs)

    def handleEdit(self, confInfo):
        Validator(session_key=self.getSessionKey()).validate(
            uri=self.payload.get("uri")
        )
        AdminExternalHandler.handleEdit(self, confInfo)

    def handleCreate(self, confInfo):
        Validator(session_key=self.getSessionKey()).validate(
            uri=self.payload.get("uri")
        )
        AdminExternalHandler.handleCreate(self, confInfo)

    def handleRemove(self, confInfo):
        AdminExternalHandler.handleRemove(self, confInfo)

if __name__ == '__main__':
    logging.getLogger().addHandler(logging.NullHandler())
    admin_external.handle(
        endpoint,
        handler=demo_addon_for_splunkExternalHandler,
    )
