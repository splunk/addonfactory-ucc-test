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
from pathlib import Path
from typing import Tuple, List, Dict
from jinja2 import Environment, Template, select_autoescape, FileSystemLoader
from splunk_add_on_ucc_modinput_test import resources
from importlib_resources import files


CLIENT_FILE_NAME = "_managed_client.py"


def get_splunk_client_path(ucc_modinput_functional: Path) -> Path:
    return ucc_modinput_functional / "splunk" / "client" / CLIENT_FILE_NAME


def load_readme_examples(swagger_client_readme_md: Path) -> List[str]:
    split_marker = "# create an instance of the API class"
    end_marker = "## Documentation for API Endpoints"

    with open(swagger_client_readme_md) as file:
        content = file.read()

    from_pos = content.find(split_marker)
    to_pos = content.find(end_marker)
    if from_pos < 0:
        raise ValueError(
            f"Could not find start marker '{split_marker}' in README.md"
        )
    if to_pos < 0:
        raise ValueError(
            f"Could not find end marker '{end_marker}' in README.md"
        )
    if to_pos < from_pos:
        raise ValueError(
            f"End marker '{end_marker}' is before start marker \
                '{split_marker}' in README.md"
        )

    splited_content = content[from_pos:to_pos].split(split_marker)[
        1:
    ]  # eliminates everything before the first split_marker
    return [x.strip() for x in splited_content]


def get_jinja_env() -> Environment:
    templates_search_path = files(resources).joinpath("templates")
    return Environment(
        loader=FileSystemLoader(templates_search_path),
        autoescape=select_autoescape(),
    )


def remove_prefix(*, api_name: str, ta_api_prefix: str) -> str:
    if api_name.lower().startswith(ta_api_prefix.lower()):
        skip = len(ta_api_prefix)
        api_name_no_prefix = api_name[skip:]
        while api_name_no_prefix and not api_name_no_prefix[0].isalpha():
            api_name_no_prefix = api_name_no_prefix[1:]
        return api_name_no_prefix
    return api_name


def make_method_name(
    *, api_name_no_prefix: str, args_specs: Dict[str, List[str]]
) -> Tuple[str, str]:
    if api_name_no_prefix.endswith("_name_get"):
        if "name" in args_specs:
            return ("get_" + api_name_no_prefix[:-9], "get")
        else:
            return ("get_" + api_name_no_prefix[:-4], "get")

    if api_name_no_prefix.endswith("_get"):
        for check in ["proxy", "settings", "logging"]:
            if check in api_name_no_prefix:
                return ("get_" + api_name_no_prefix[:-4], "get")

        if "name" not in args_specs:
            return ("get_" + api_name_no_prefix[:-4] + "_list", "list")

    if api_name_no_prefix.endswith("_name_post"):
        if "name" in args_specs:
            return ("update_" + api_name_no_prefix[:-10], "create")
        else:
            return ("create_" + api_name_no_prefix[:-5], "create")

    if api_name_no_prefix.endswith("_post"):
        for check in ["proxy", "settings", "logging"]:
            if check in api_name_no_prefix:
                return ("update_" + api_name_no_prefix[:-5], "update")

        return ("create_" + api_name_no_prefix[:-5], "create")

    if api_name_no_prefix.endswith("_name_delete"):
        if "name" in args_specs:
            return ("delete_" + api_name_no_prefix[:-12], "delete")
        else:
            return ("delete_" + api_name_no_prefix[:-7], "delete")

    return api_name_no_prefix, "unknown"


# def _parse_arg_descriptor(self, arg_name: str, right_part: str) -> None:
def parse_arg_descriptor(right_part: str) -> List[str]:
    descriptors = right_part.strip().split("#")
    spec = []
    if len(descriptors) > 1:
        spec_str = descriptors[1].strip()
        for item in spec_str.split("|"):
            spec.append(item.strip())
    # self.args_specs[arg_name] = spec
    return spec


def parse_args(
    *, call_args: List[str], args_specs: Dict[str, List[str]]
) -> Tuple[str, str]:
    api_args = []
    method_args = []
    method_kwargs = []
    for arg in call_args:
        arg = arg.strip()
        kv = arg.split("=")
        if len(kv) > 1:
            arg_name = kv[0].strip()
            api_arg_str = f"{arg_name}={kv[0].strip()}"
        else:
            arg_name = arg
            api_arg_str = f"{arg_name}={arg_name}"

        if arg_name == "output_mode":
            api_args.append("output_mode=self._OUTPUT_MODE")
            continue

        api_args.append(api_arg_str)

        arg_str = arg_name
        if arg_name in args_specs:
            spec = args_specs[arg_name]
            spec_str = ""
            if len(spec) > 0:
                spec_str = f": {spec[0]}"

            if len(spec) > 1 and spec[1] == "(optional)":
                spec_str = f": Optional[{spec[0]}] = None"
            arg_str += spec_str

        if arg_str != arg_name:
            method_kwargs.append(arg_str)
        else:
            method_args.append(arg_str)

    method_args_str = ", ".join(method_args)
    if method_kwargs:
        method_args_str += ", " + ", ".join(method_kwargs)
    api_args_str = ", ".join(api_args)

    return api_args_str, method_args_str

    # method_template = get_jinja_env().get_template(
    #     "splunk_client_class_method.tmpl"
    # )


def extract_methods(
    *, method_template: Template, samples: List[str], ta_api_prefix: str
) -> List[str]:
    # method_specs: Dict[str, Dict[str, List[str]]] = {}
    methods: List[str] = []
    for sample in samples:
        args_specs: Dict[str, List[str]] = {}
        for line in sample.splitlines():
            line = line.strip()
            if not line:
                continue
            res = line.split("=", 1)
            if len(res) < 2:
                continue
            arg_name = res[0].strip()
            if arg_name != "api_response":
                args_specs[arg_name] = parse_arg_descriptor(res[1])
            else:  # if arg_name == "api_response":
                call = res[1].strip()
                if call.startswith("api_instance."):
                    call = call[13:].strip()

                api_name = call[: call.find("(")]

                api_name_no_prefix = remove_prefix(
                    api_name=api_name, ta_api_prefix=ta_api_prefix
                )
                method_name, method_type = make_method_name(
                    # api_name_no_prefix
                    api_name_no_prefix=api_name_no_prefix,
                    args_specs=args_specs,
                )

                fst = call.find("(") + 1
                lst = call.rfind(")")
                call_args = call[fst:lst].split(",")
                api_args_str, method_args_str = parse_args(
                    call_args=call_args, args_specs=args_specs
                )

                method_str = method_template.render(
                    method_type=method_type,
                    method_name=method_name,
                    method_args=method_args_str,
                    api_name=api_name,
                    api_args=api_args_str,
                )
                methods.append(method_str)
                # method_specs[method_str] = args_specs

                # self.args_specs = {}
                break
    # return method_specs
    return methods


def noqaE501check(block: str) -> List[str]:
    content: List[str] = []
    for line in block.split("\n"):
        if len(line) > 79:
            line += "  # noqa: E501"
        content.append(line)
    return content


def write_splunk_client(
    *, splunk_client_py: Path, splunk_client_content: str, methods: List[str]
) -> None:
    content = []
    content += noqaE501check("# fmt: off\n")
    content += noqaE501check(splunk_client_content)
    for method in methods:
        content += noqaE501check(method)
    content += noqaE501check("# fmt: on\n")

    with open(splunk_client_py, "w") as file:
        file.write("\n".join(content))


def write_other_classes(*, unified_tests_root_dir: Path) -> None:
    schema = {
        unified_tests_root_dir.parent: [
            {
                "file": "__init__.py",
                "overwrite": False,
            }
        ],
        unified_tests_root_dir: [
            {
                "file": "__init__.py",
                "template": "unified_tests_init.tmpl",
                "overwrite": False,
            },
            {
                "file": "test_settings.py",
                "template": "test_settings.tmpl",
                "overwrite": False,
            },
            {
                "file": "defaults.py",
                "template": "defaults.tmpl",
                "overwrite": False,
            },
            {
                "file": "README.md",
                "template": "README.tmpl",
                "overwrite": False,
            },
        ],
        unified_tests_root_dir
        / "splunk": [
            {
                "file": "__init__.py",
                "overwrite": False,
            },
            {
                "file": "forges.py",
                "template": "splunk_forges.tmpl",
                "overwrite": False,
            },
            {
                "file": "probes.py",
                "template": "splunk_probes.tmpl",
                "overwrite": False,
            },
        ],
        unified_tests_root_dir
        / "splunk"
        / "client": [
            {
                "file": "__init__.py",
                "template": "splunk_client_init.tmpl",
                "overwrite": False,
            },
            {
                "file": "configuration.py",
                "template": "splunk_configuration_class.tmpl",
                "overwrite": False,
            },
            {
                "file": "client.py",
                "template": "splunk_client_class.tmpl",
                "overwrite": False,
            },
        ],
        unified_tests_root_dir
        / "vendor": [
            {
                "file": "__init__.py",
                "overwrite": False,
            },
            {
                "file": "forges.py",
                "template": "vendor_forges.tmpl",
                "overwrite": False,
            },
            {
                "file": "probes.py",
                "template": "vendor_probes.tmpl",
                "overwrite": False,
            },
        ],
        unified_tests_root_dir
        / "vendor"
        / "client": [
            {
                "file": "__init__.py",
                "template": "vendor_client_init.tmpl",
                "overwrite": False,
            },
            {
                "file": "client.py",
                "template": "vendor_client_class.tmpl",
                "overwrite": False,
            },
            {
                "file": "configuration.py",
                "template": "vendor_configuration_class.tmpl",
                "overwrite": False,
            },
        ],
    }

    for folder_path, folder_files in schema.items():
        folder_path.mkdir(parents=True, exist_ok=True)
        for file_info in folder_files:
            file_name = str(file_info["file"])
            file_path = folder_path / file_name
            if (
                not file_path.exists()
                or file_path.exists()
                and file_info.get("overwrite", False)
            ):
                template = str(file_info.get("template", ""))
                if template:
                    template = get_jinja_env().get_template(template).render()
                with file_path.open(mode="w") as file:
                    file.write(template)
