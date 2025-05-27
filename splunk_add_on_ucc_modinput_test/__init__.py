#
# Copyright 2025 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import logging

fh = logging.FileHandler("ucc_modinput_test.log")
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(process)d - %(filename)s - \
        %(funcName)s - %(message)s"
)
fh.setFormatter(formatter)
logger = logging.getLogger("ucc-modinput-test")
logger.addHandler(fh)
logging.root.propagate = False
logger.setLevel(logging.DEBUG)

logger.debug("Logger set")
