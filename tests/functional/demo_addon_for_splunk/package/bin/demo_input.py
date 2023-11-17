import json
import logging
import sys
import traceback

import import_declare_test
from solnlib import conf_manager, log
from splunklib import modularinput as smi

from demo_addon_for_splunk_utils import ADDON_NAME, Connect, set_logger_for_input

def get_endpoint_uri(session_key: str, endpoint_name: str):
    cfm = conf_manager.ConfManager(
        session_key,
        ADDON_NAME,
        realm=f"__REST_CREDENTIAL__#{ADDON_NAME}#configs/conf-demo_addon_for_splunk_endpoint",
    )
    endpoint_conf_file = cfm.get_conf("demo_addon_for_splunk_endpoint")
    return endpoint_conf_file.get(endpoint_name).get("uri")

def get_data(logger: logging.Logger, uri: str):
    logger.info(f"Getting data from an external URI {uri}")
    return Connect(logger=logger).get(uri=uri)

class Input(smi.Script):
    def __init__(self):
        super().__init__()

    def get_scheme(self):
        scheme = smi.Scheme("demo_input")
        scheme.description = "demo_input input"
        scheme.use_external_validation = True
        scheme.streaming_mode_xml = True
        scheme.use_single_instance = False
        scheme.add_argument(
            smi.Argument(
                "name", title="Name", description="Name", required_on_create=True
            )
        )
        return scheme

    def validate_input(self, definition: smi.ValidationDefinition):
        return

    def stream_events(self, inputs: smi.InputDefinition, event_writer: smi.EventWriter):
        for input_name, input_item in inputs.inputs.items():
            normalized_input_name = input_name.split("/")[-1]
            try:
                session_key = self._input_definition.metadata["session_key"]
                logger = set_logger_for_input(session_key, normalized_input_name)
                log.modular_input_start(logger, normalized_input_name)
                uri = get_endpoint_uri(session_key, input_item.get("endpoint"))
                response = get_data(logger, uri)
                data=json.dumps(response.__dict__, ensure_ascii=False, default=str)
                successul_or_not_successul = "successul" if response.ok else "not successul"
                log_msg = f"""Request to {uri} was {successul_or_not_successul}
Response details:
{data}"""
                if response.ok:
                    logger.debug(log_msg)
                    event_writer.write_event(
                        smi.Event(
                            data=data,
                            index=input_item.get("index"),
                            sourcetype=input_item.get("sourcetype"),
                            source=uri,
                        )
                    )
                    logger.info(
                        "Data was successfuly indexed"
                    )
                else:
                    logger.error(log_msg)
                log.modular_input_end(logger, normalized_input_name)
            except Exception as e:
                logger.error(
                    f"Exception raised while ingesting data for "
                    f"demo_input: {e}. Traceback: "
                    f"{traceback.format_exc()}"
                )


if __name__ == "__main__":
    exit_code = Input().run(sys.argv)
    sys.exit(exit_code)
