import argparse
import sys
from pathlib import Path
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

    class OpenApiPath():
        DEFAULT = "output/*/static/openapi.json"

        @staticmethod
        def validate(value):
            if value != OpenApiPath.DEFAULT:
                return value
            else:
                l = sorted(Path().glob(OpenApiPath.DEFAULT))
                print(l)
                if len(l) != 1:
                    raise argparse.ArgumentTypeError(
                        f"""Default path ({OpenApiPath.DEFAULT}) does not work in this case.
                        Define path to openapi.json
                        """
                        )
            return str(l[0].parents[0])

    parser.add_argument(
        "--openapi-json",
        type=OpenApiPath.validate,
        help=f"openapi.json path",
        default=OpenApiPath.DEFAULT,
    )
    args = parser.parse_args(argv)
    print(args)

if __name__ == "__main__":
    raise SystemExit(main())