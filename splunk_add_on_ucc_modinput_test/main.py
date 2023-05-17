import argparse
import sys
from typing import Optional, Sequence
import logging
from splunk_add_on_ucc_modinput_test import setup_environment

logger = logging.getLogger("ucc_test")

class DefaultSubcommandArgumentParser(argparse.ArgumentParser):
    __default_subparser = None

    def set_default_subparser(self, name):
        self.__default_subparser = name

    def _parse_known_args(self, arg_strings, *args, **kwargs):
        in_args = set(arg_strings)
        d_sp = self.__default_subparser
        if d_sp is not None and not {"-h", "--help"}.intersection(in_args):
            for x in self._subparsers._actions:
                subparser_found = isinstance(
                    x, argparse._SubParsersAction
                ) and in_args.intersection(x._name_parser_map.keys())
                if subparser_found:
                    break
            else:
                logger.warning(
                    "Please use `ucc-gen build` if you want to build "
                    "an add-on, using just `ucc-gen` will be deprecated"
                )
                arg_strings = [d_sp] + arg_strings
        return super()._parse_known_args(arg_strings, *args, **kwargs)

def main(argv: Optional[Sequence[str]] = None):
    argv = argv if argv is not None else sys.argv[1:]
    parser = DefaultSubcommandArgumentParser()
    parser.set_default_subparser("build")
    subparsers = parser.add_subparsers(dest="command", description="Build an add-on")

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument(
        "--source",
        type=str,
        nargs="?",
        help="Folder containing the app.manifest and app source.",
        default="package",
    )

    args = parser.parse_args(argv)
    if args.command == "build":
        pass
        # build.generate(
        #     source=args.source,
        #     config_path=args.config,
        #     addon_version=args.ta_version,
        #     python_binary_name=args.python_binary_name,
        # )

if __name__ == "__main__":
    raise SystemExit(main())