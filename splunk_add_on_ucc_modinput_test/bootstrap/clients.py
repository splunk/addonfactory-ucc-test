import json
import os
import os.path
from datetime import datetime
from typing import Tuple, List, Optional, Dict
from jinja2 import Environment, select_autoescape, FileSystemLoader


class SplunkClientBootstrup:
    tests_root_dir = "tests"
    unified_tests_root_dir = os.path.join(
        tests_root_dir, "ucc_modinput_functional"
    )

    splunk_base_dir = os.path.join(unified_tests_root_dir, "splunk")
    splunk_client_dir = os.path.join(splunk_base_dir, "client")

    vendor_base_dir = os.path.join(unified_tests_root_dir, "vendor")
    vendor_client_dir = os.path.join(vendor_base_dir, "client")

    schema = {
        tests_root_dir: [
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
                "file": "tests_settings.py",
                "template": "tests_settings.tmpl",
                "overwrite": False,
            },
            {
                "file": "defaults.py",
                "template": "defaults.tmpl",
                "overwrite": False,
            },
        ],
        splunk_base_dir: [
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
        splunk_client_dir: [
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
        ],
        vendor_base_dir: [
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
        vendor_client_dir: [
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

    def __init__(self, ta_project_path: Optional[str] = None):
        self.ta_project_path = (
            ta_project_path if ta_project_path else os.getcwd()
        )
        self.args_specs: Dict[str, List[str]] = {}
        self.ta_api_prefixes: List[str] = []
        self.methods: List[str] = []
        self.method_specs: Dict[str, Dict[str, List[str]]] = {}

        templates_search_path = os.path.join(
            os.path.dirname(__file__), "templates"
        )

        self.jinja_env = Environment(
            loader=FileSystemLoader(templates_search_path),
            autoescape=select_autoescape(),
        )

    def _make_method_name(self, api_name_no_prefix: str) -> Tuple[str, str]:
        if api_name_no_prefix.endswith("_name_get"):
            if "name" in self.args_specs:
                return ("get_" + api_name_no_prefix[:-9], "get")
            else:
                return ("get_" + api_name_no_prefix[:-4], "get")

        if api_name_no_prefix.endswith("_get"):
            for check in ["proxy", "settings", "logging"]:
                if check in api_name_no_prefix:
                    return ("get_" + api_name_no_prefix[:-4], "get")

            if "name" not in self.args_specs:
                return ("get_" + api_name_no_prefix[:-4] + "_list", "list")

        if api_name_no_prefix.endswith("_name_post"):
            if "name" in self.args_specs:
                return ("update_" + api_name_no_prefix[:-10], "create")
            else:
                return ("create_" + api_name_no_prefix[:-5], "create")

        if api_name_no_prefix.endswith("_post"):
            for check in ["proxy", "settings", "logging"]:
                if check in api_name_no_prefix:
                    return ("update_" + api_name_no_prefix[:-5], "update")

            return ("create_" + api_name_no_prefix[:-5], "create")

        if api_name_no_prefix.endswith("_name_delete"):
            if "name" in self.args_specs:
                return ("delete_" + api_name_no_prefix[:-12], "delete")
            else:
                return ("delete_" + api_name_no_prefix[:-7], "delete")

        return api_name_no_prefix, "unknown"

    def _remove_prefix(self, api_name: str) -> str:
        for prefix in self.ta_api_prefixes:
            if prefix and api_name.startswith(prefix):
                skip = len(prefix)
                api_name_no_prefix = api_name[skip:]
                while (
                    api_name_no_prefix and not api_name_no_prefix[0].isalpha()
                ):
                    api_name_no_prefix = api_name_no_prefix[1:]
                return api_name_no_prefix

        return api_name

    def _parse_args(self, call_args: List[str]) -> Tuple[str, str]:
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
            if arg_name in self.args_specs:
                spec = self.args_specs[arg_name]
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

    def _parse_arg_descriptor(self, arg_name: str, right_part: str) -> None:
        descriptors = right_part.strip().split("#")
        spec = []
        if len(descriptors) > 1:
            spec_str = descriptors[1].strip()
            for item in spec_str.split("|"):
                spec.append(item.strip())

        self.args_specs[arg_name] = spec

    def _load_prefixes(self) -> None:
        config_file = os.path.join(self.ta_project_path, "globalConfig.json")
        self.ta_api_prefixes = []
        with open(config_file) as file:
            config = json.load(file)
            self.ta_api_prefixes.append(config["meta"]["restRoot"])

    def _load_readme_examples(self) -> List[str]:
        end_marker = "## Documentation for API Endpoints"
        split_marker = "# create an instance of the API class"

        readme_file = os.path.join(
            self.ta_project_path, "swagger_client", "README.md"
        )
        with open(readme_file) as file:
            content = file.read()

        pos = content.find(end_marker)
        if pos > 0:
            content = content[:pos]

        return content.split(split_marker)

    def _extract_methods(self, samples: List[str]) -> None:
        method_template = self.jinja_env.get_template(
            "splunk_client_class_method.tmpl"
        )

        self.methods = []
        for sample in samples:
            self.args_specs = {}
            for line in sample.splitlines():
                line = line.strip()
                if not line:
                    continue
                res = line.split("=", 1)
                if len(res) < 2:
                    continue
                arg_name = res[0].strip()
                if arg_name == "api_response":
                    call = res[1].strip()
                    if call.startswith("api_instance."):
                        call = call[13:].strip()

                    api_name = call[: call.find("(")]

                    api_name_no_prefix = self._remove_prefix(api_name)
                    method_name, method_type = self._make_method_name(
                        api_name_no_prefix
                    )

                    fst = call.find("(") + 1
                    lst = call.rfind(")")
                    call_args = call[fst:lst].split(",")
                    api_args_str, method_args_str = self._parse_args(call_args)

                    method_str = method_template.render(
                        method_type=method_type,
                        method_name=method_name,
                        method_args=method_args_str,
                        api_name=api_name,
                        api_args=api_args_str,
                    )
                    self.methods.append(method_str)
                    self.method_specs[method_str] = self.args_specs
                    self.args_specs = {}
                    break

                self._parse_arg_descriptor(arg_name, res[1])

    def _backup_file(self, file_path: str) -> None:
        now = datetime.now().strftime("%Y%m%d%H%M%S")
        if os.path.isfile(file_path):
            _backup_file = f"{file_path}.{now}.backup"
            os.rename(file_path, _backup_file)

    def _backup_and_overwrite_file(
        self, file_path: str, content: str = ""
    ) -> None:
        self._backup_file(file_path)
        with open(file_path, "w") as file:
            file.write(content)

    def _create_file_if_missing(
        self, file_path: str, content: str = ""
    ) -> None:
        if not os.path.isfile(file_path):
            with open(file_path, "w") as file:
                file.write(content)

    def _write_other_classes(self) -> None:
        for folder_path, folder_files in self.schema.items():
            os.makedirs(folder_path, exist_ok=True)
            for file_info in folder_files:
                file_name = str(file_info["file"])
                file_path = os.path.join(folder_path, file_name)
                template = str(file_info.get("template", ""))
                if template:
                    template = self.jinja_env.get_template(template).render()

                if file_info.get("overwrite", False):
                    self._backup_and_overwrite_file(file_path, template)
                else:
                    self._create_file_if_missing(file_path, template)

    def _write_splunk_client(self) -> None:
        os.makedirs(self.splunk_client_dir, exist_ok=True)
        client_file = f"{self.splunk_client_dir}/client.py"
        self._backup_file(client_file)

        with open(client_file, "w") as file:
            content = self.jinja_env.get_template(
                "splunk_client_class_header.tmpl"
            ).render()
            file.write(content)
            for method in self.methods:
                file.write(method)

    def make_splunk_client(self) -> None:
        self._load_prefixes()
        samples = self._load_readme_examples()
        self._extract_methods(samples)
        self._write_splunk_client()

    def init(self) -> None:
        self.make_splunk_client()
        self._write_other_classes()


if __name__ == "__main__":
    SplunkClientBootstrup().init()
    # SplunkClientBootstrup().make_splunk_client()
