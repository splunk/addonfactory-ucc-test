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
import os
from pathlib import Path
import shutil
from typing import Optional
from importlib_resources import files
from splunk_add_on_ucc_modinput_test import resources
from splunk_add_on_ucc_modinput_test.common import bootstrap
import subprocess
from importlib_metadata import version, PackageNotFoundError

SWAGGER_CODEGEN_CLI_VERSION = "3.0.68"


def get_version() -> str:
    try:
        return version("splunk_add_on_ucc_modinput_test")
    except PackageNotFoundError:
        return "unknown"


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


def generate_swagger_client(
    *,
    openapi: Path,
    tmp: Path,
    swagger_client: Path,
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
    docker_run_command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{str(tmp.resolve())}:/local",
    ]
    if platform:
        docker_run_command.extend(["--platform", platform])
    docker_run_command.extend(
        [
            f"swaggerapi/swagger-codegen-cli-v3:{SWAGGER_CODEGEN_CLI_VERSION}",
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

    subprocess.run(
        docker_run_command,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    shutil.copytree(
        str(restapi_client_path / "swagger_client"),
        str(swagger_client),
    )
    shutil.copy(str(restapi_client_path / "README.md"), str(swagger_client))

    return swagger_client


def generate_splunk_client(
    *,
    swagger_client_readme_md: Path,
    splunk_client_py: Path,
    rest_root: str,
) -> Path:
    """
    Generate the Splunk client from the swagger client README.md
    :param swagger_client_readme_md: Path to the swagger client README.md
    :param splunk_client_py: Path to client.py
    :param rest_root: The REST root
    :return: Path to the generated Splunk client
    """
    jinja_env = bootstrap.get_jinja_env()
    samples = bootstrap.load_readme_examples(
        swagger_client_readme_md=swagger_client_readme_md
    )
    methods = bootstrap.extract_methods(
        method_template=jinja_env.get_template(
            "managed_splunk_client_class_method.tmpl"
        ),
        samples=samples,
        ta_api_prefix=rest_root,
    )
    bootstrap.write_splunk_client(
        splunk_client_py=splunk_client_py,
        splunk_client_content=jinja_env.get_template(
            "managed_splunk_client_class_header.tmpl"
        ).render(),
        methods=methods,
    )
    return splunk_client_py
