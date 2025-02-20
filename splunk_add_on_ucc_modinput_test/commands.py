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
import os
from pathlib import Path
import shutil
from typing import Optional
from python_on_whales import docker
from importlib_resources import files
from splunk_add_on_ucc_modinput_test import resources

SWAGGER_CODEGEN_CLI_VERSION = "3.0.46"


def initialize(
    *,
    modinput: Path,
) -> Path:
    src = files(resources).joinpath("ucc_modinput_functional")
    for root, _, fls in os.walk(src):
        dest_path = Path(modinput) / Path(root).relative_to(src)
        if not dest_path.exists():
            dest_path.mkdir(parents=True)
        for file in fls:
            shutil.copy2(Path(root) / file, dest_path)

    init_in_tests = modinput.parent / "__init__.py"
    if not init_in_tests.exists():
        init_in_tests.touch()
    return modinput


def generate(
    *,
    openapi: Path,
    tmp: Path,
    client: Path,
    platform: Optional[str],
) -> Path:
    RESTAPI_CLIENT = "restapi_client"
    GENERATOR = "generator"
    restapi_client_path = tmp / RESTAPI_CLIENT
    generator_path = tmp / GENERATOR
    restapi_client_path.mkdir()
    generator_path.mkdir()
    shutil.copy(str(openapi), str(tmp))
    shutil.copy(
        str(
            files(resources).joinpath(
                "swagger-codegen-generators/src/main/resources/handlebars/python/api_client.mustache"  # noqa: E501
            )
        ),
        str(generator_path),
    )
    shutil.copy(
        str(
            files(resources).joinpath(
                "swagger-codegen-generators/src/main/resources/handlebars/python/rest.mustache"  # noqa: E501
            )
        ),
        str(generator_path),
    )
    docker_run_command = []
    if platform:
        docker_run_command.extend(["--platform", platform])
    docker_run_command.extend(
        [
            "generate",
            "-i",
            f"/local/{openapi.name}",
            "-l",
            "python",
            "-o",
            f"/local/{RESTAPI_CLIENT}",
            "-t",
            f"/local/{GENERATOR}/",
        ]
    )

    docker.run(
        f"swaggerapi/swagger-codegen-cli-v3:{SWAGGER_CODEGEN_CLI_VERSION}",
        docker_run_command,
        volumes=[(str(tmp.resolve()), "/local")],
        remove=True,
    )
    shutil.copytree(
        str(restapi_client_path / "swagger_client"),
        str(client / "swagger_client"),
    )
    shutil.copy(
        str(restapi_client_path / "README.md"), str(client / "swagger_client")
    )
    return restapi_client_path
