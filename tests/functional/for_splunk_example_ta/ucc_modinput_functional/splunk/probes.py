from splunk_add_on_ucc_modinput_test.common import utils
from tests.ucc_modinput_functional.splunk.client import SplunkClient
from typing import Generator


def events_ingested(
    splunk_client: SplunkClient, probe_spl: str, probes_wait_time: int = 10
) -> Generator[int, None, None]:
    start_time = utils.get_epoch_timestamp()
    utils.logger.debug(f"started at {start_time}")
    utils.logger.debug(probe_spl)
    while True:
        search = splunk_client.search(searchquery=probe_spl)
        if search.result_count != 0:
            break
        utils.logger.debug(
            f"failed, let's wait another {probes_wait_time} \
                seconds and try again"
        )
        yield probes_wait_time

    utils.logger.debug(
        "successfully finished after "
        f"{utils.get_epoch_timestamp()-start_time} seconds"
    )


def account_input_events_ingested(
    splunk_client: SplunkClient, example_input_spl: str
) -> Generator[int, None, None]:
    yield from events_ingested(splunk_client, example_input_spl)
