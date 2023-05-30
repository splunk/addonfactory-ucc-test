#
# Copyright 2021 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import logging
from pathlib import Path
import shutil
from python_on_whales import docker
# from importlib import resources as resources_lib
# from splunk_add_on_ucc_modinput_test import resources as resources_dir
from importlib_resources import files
from splunk_add_on_ucc_modinput_test import resources

# from cookiecutter import exceptions, main

logger = logging.getLogger("ucc_gen")


def init(
    openapi: Path,
    tmp: Path,
    client: Path,
) -> Path:
# Create directory structure and open the tmp directory (run in terminal: mkdir -p tmp/restapi_client ; mkdir -p tmp/generator ; cd tmp)
    RESTAPI_CLIENT = "restapi_client"
    GENERATOR = "generator"
    restapi_client_path = tmp / RESTAPI_CLIENT
    generator_path = tmp / GENERATOR
    restapi_client_path.mkdir()
    generator_path.mkdir()
# Save your openapi.json file to the directory
    shutil.copy(str(openapi), str(tmp))
# Download the rest.mustache file (wget https://raw.githubusercontent.com/swagger-api/swagger-codegen/master/modules/swagger-codegen/src/main/resources/python/rest.mustache)
# Splunk does not expect body for DELETE requests, so we need to revert modifications done for https://github.com/swagger-api/swagger-codegen/issues/9558 (sed "s/request_body[[:blank:]]=[[:blank:]]\'{}\'/request_body = None/g" rest.mustache > generator/rest.mustache). If you want to understand exactly which line of rest.mustache is affected: https://github.com/swagger-api/swagger-codegen/blob/master/modules/swagger-codegen/src/main/resources/python/rest.mustache#L150
    # cp -R ${PWD}/swagger-codegen-generators/ ${TMP}
    shutil.copy(str(files(resources).joinpath('swagger-codegen-generators/src/main/resources/handlebars/python/rest.mustache')), str(generator_path))
# Create client (docker run --rm -v ${PWD}:/local swaggerapi/swagger-codegen-cli-v3 generate -i /local/openapi.json -l python -o /local/restapi_client -t /local/generator/); it should appear in restapi_client directory
    docker.run(
        "swaggerapi/swagger-codegen-cli-v3",
        ["generate", "-i", f"/local/{openapi.name}", "-l", "python", "-o", f"/local/{RESTAPI_CLIENT}", "-t", f"/local/{GENERATOR}/"],
        volumes=[(str(tmp.resolve()), "/local")],
        remove=True,
    )
    shutil.copytree(str(restapi_client_path / "swagger_client"), str(client / "swagger_client"))
    shutil.copy(str(restapi_client_path / "README.md"), str(client / "swagger_client"))
# Open restapi_client directory and read README.md to find out the details of how the client should be installed, imported and used. (cd restapi_client ; more README.md)
# Install the client (python setup.py install --user)
# You can use below code as an inspiration for your own script that imports the client and uses for TA configuration

