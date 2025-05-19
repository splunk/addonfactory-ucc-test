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
# mypy: disable-error-code="arg-type"

import argparse
import sys
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, Sequence
from splunk_add_on_ucc_modinput_test import commands, tools
from splunk_add_on_ucc_modinput_test.common import bootstrap, utils
import shutil


def main(argv: Optional[Sequence[str]] = None) -> int:
    class Platform:
        #   https://docs.docker.com/build/building/multi-platform/
        DEFAULT = None
        SUPPORTED = [
            "windows/amd64",
            "linux/amd64",
            "linux/arm64",
            "linux/arm/v7",
            "linux/arm64/v8",
        ]

        @staticmethod
        def validate(value: Optional[str]) -> Optional[str]:
            if value in {Platform.DEFAULT, *Platform.SUPPORTED}:
                return value
            raise argparse.ArgumentTypeError(
                f"""
                Given platform ({value}) is not supported. Supported platforms are:
                {Platform.SUPPORTED}
                """
            )

    class OpenApiPath:
        DEFAULT = "output/*/appserver/static/openapi.json"

        @staticmethod
        def validate(value: str) -> Path:
            if value != OpenApiPath.DEFAULT:
                p = Path(value)
                if not p.exists():
                    raise argparse.ArgumentTypeError(
                        f"""
                        Given openapi.json path ({value}) does not exist.
                        """
                    )
                return p
            else:
                pl = sorted(Path().glob(OpenApiPath.DEFAULT))
                if len(pl) != 1:
                    raise argparse.ArgumentTypeError(
                        f"""
                        Default path ({OpenApiPath.DEFAULT}) does not work in \
                            this case.
                        It returns {len(pl)} results: {[str(x) for x in pl]}
                        Define path to openapi.json
                        """
                    )
                return pl[0]

    class TmpPath:
        DEFAULT = str(Path(tempfile.gettempdir()) / "modinput")

        @staticmethod
        def validate(value: str) -> Path:
            p = Path(value)
            if p.exists():
                p_resolved = p.resolve()
                target = (
                    p_resolved.parent
                    / "backup"
                    / datetime.now().strftime("%Y%m%d%H%M%S")
                    / p_resolved.name
                )
                target.mkdir(parents=True)
                p.rename(target)
            p.mkdir(parents=True)
            return p

    class ClientCodePath:
        DEFAULT = "."

        @staticmethod
        def validate(value: str) -> Path:
            directory = Path(value)
            if not directory.exists():
                raise argparse.ArgumentTypeError(
                    f"Given directory ({value}) has to exist. Create \
                        {directory.resolve()}"
                )
            return directory

    class ModinputPath:
        DEFAULT = "tests/ucc_modinput_functional"

    class FilePath:
        @staticmethod
        def validate(value: str) -> Path:
            f = Path(value)
            if not f.exists():
                raise argparse.ArgumentTypeError(f"{value} does not exist")
            elif not f.is_file():
                raise argparse.ArgumentTypeError(f"{value} is not a file")
            return f

    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {commands.get_version()}",
    )
    subparsers = parser.add_subparsers(dest="command")
    gen_parser = subparsers.add_parser(
        "gen", description="Generate python client code from openapi.json"
    )
    init_parser = subparsers.add_parser(
        "init",
        description="Initialize modinput tests. This is one time action.",
    )
    base64encode_parser = subparsers.add_parser(
        "base64encode",
        description="Tool to convert complex string (due to special characters \
            or structure) to base64 string",
    )
    base64decode_parser = subparsers.add_parser(
        "base64decode", description="Tool to decode base64 string"
    )

    _p_args = (
        "-p",
        "--platform",
    )
    _p_kwargs = {
        "type": Platform.validate,
        "help": "--platform flag when running swaggerapi/swagger-codegen-cli-v3 docker image",
        "default": Platform.DEFAULT,
    }
    gen_parser.add_argument(*_p_args, **_p_kwargs)
    init_parser.add_argument(*_p_args, **_p_kwargs)

    _o_args = (
        "-o",
        "--openapi-json",
    )
    _o_kwargs = {
        "type": OpenApiPath.validate,
        "help": "openapi.json path. Client code will be generated from this.",
        "default": OpenApiPath.DEFAULT,
    }
    gen_parser.add_argument(*_o_args, **_o_kwargs)
    init_parser.add_argument(*_o_args, **_o_kwargs)

    _t_args = (
        "-t",
        "--tmp",
    )
    _t_kwargs = {
        "type": TmpPath.validate,
        "help": "Temporary directory, where resources needed for client code \
            creation will be stored",
        "default": TmpPath.DEFAULT,
    }
    gen_parser.add_argument(*_t_args, **_t_kwargs)
    init_parser.add_argument(*_t_args, **_t_kwargs)

    _c_args = (
        "-c",
        "--client-code",
    )
    _c_kwargs = {
        "type": ClientCodePath.validate,
        "help": "Path to client code directory. This is target directory.",
        "default": ClientCodePath.DEFAULT,
    }
    gen_parser.add_argument(*_c_args, **_c_kwargs)
    init_parser.add_argument(*_c_args, **_c_kwargs)

    _m_args = (
        "-m",
        "--modinput",
    )
    _m_kwargs = {
        "help": "Path to functional tests target directory.",
        "default": ModinputPath.DEFAULT,
    }
    gen_parser.add_argument(*_m_args, **_m_kwargs)
    init_parser.add_argument(*_m_args, **_m_kwargs)

    feature_group = gen_parser.add_mutually_exclusive_group()
    feature_group.add_argument(
        "--skip-splunk-client-check",
        action="store_true",
        help="Exisitng splunk client will not be checked aginst consistency with swagger client. WARNING: This may lead to inconsistent state of splunk client.",
    )
    feature_group.add_argument(
        "--force-splunk-client-overwritten",
        action="store_true",
        help="Existing splunk client will be overwritten by new one. WARNING: This may lead to loss of existing splunk client.",
    )

    base64decode_parser.add_argument(
        "-s",
        "--string",
        type=str,
        help="Base64 encoded string.",
        required=True,
    )

    group = base64encode_parser.add_mutually_exclusive_group()
    group.add_argument(
        "-f",
        "--file",
        type=FilePath.validate,
        help="Path to input text file.",
    )
    group.add_argument(
        "-s",
        "--string",
        type=str,
        help="String to be base64 encoded.",
    )

    args = parser.parse_args(argv)

    if args.command == "base64encode":
        print(
            tools.base64encode(
                text_file=args.file,
                string=args.string,
            )
        )
    elif args.command == "base64decode":
        print(tools.base64decode(base64_string=args.string))
    elif args.command in ["gen", "init"]:
        docker_err = tools.is_docker_running()
        if docker_err is not None:
            print(docker_err)
            return 1
        modinput_path = Path(args.modinput)
        if args.command == "init" and modinput_path.exists():
            print(
                f"{modinput_path} already exists. Did you want to run 'gen' command?"
            )
            return 1
        if args.command == "gen" and not modinput_path.exists():
            print(
                f"{modinput_path} does not exist. Run 'init' command first or use --modinput/-m with appropriate location."
            )
            return 1
        swagger_client = args.client_code / "swagger_client"
        if swagger_client.exists():
            shutil.rmtree(swagger_client)
        swagger_client = commands.generate_swagger_client(
            openapi=args.openapi_json,
            tmp=args.tmp,
            swagger_client=swagger_client,
            platform=args.platform,
        )

        if args.command == "init":
            bootstrap.write_other_classes(unified_tests_root_dir=modinput_path)
            splunk_client = commands.generate_splunk_client(
                swagger_client_readme_md=swagger_client / "README.md",
                splunk_client_py=bootstrap.get_splunk_client_path(
                    modinput_path
                ),
                rest_root=tools.get_rest_root(openapi=args.openapi_json),
            )
        elif args.command == "gen":
            current_splunk_client = bootstrap.get_splunk_client_path(
                modinput_path
            )
            splunk_client = commands.generate_splunk_client(
                swagger_client_readme_md=swagger_client / "README.md",
                splunk_client_py=args.tmp / bootstrap.CLIENT_FILE_NAME,
                rest_root=tools.get_rest_root(openapi=args.openapi_json),
            )
            if args.skip_splunk_client_check:
                pass
            elif args.force_splunk_client_overwritten:
                if (
                    current_splunk_client.parent.exists()
                    and current_splunk_client.exists()
                ):
                    backup_path = (
                        current_splunk_client.parent
                        / f"{current_splunk_client.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}_backup"
                    )
                    shutil.move(current_splunk_client, backup_path)
                elif not current_splunk_client.parent.exists():
                    current_splunk_client.parent.mkdir()
                shutil.copy(splunk_client, current_splunk_client)
            elif not current_splunk_client.exists():
                print(
                    f"Current splunk client ({current_splunk_client}) does not exist. Use --force-splunk-client-overwritten to create it."
                )
                return 1
            elif utils.md5(file_path=splunk_client) != utils.md5(
                file_path=bootstrap.get_splunk_client_path(modinput_path)
            ):
                print(
                    f"Existing splunk client ({current_splunk_client}) is outdated. Use --force-splunk-client-overwritten to overwrite it or --skip-splunk-client-check if you want to post."
                )
                return 1
            else:
                """
                Existing splunk client is up to date.
                """
                pass
    else:
        parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
