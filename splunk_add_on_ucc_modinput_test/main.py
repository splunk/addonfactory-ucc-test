import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Sequence
import logging
from splunk_add_on_ucc_modinput_test import init_command

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
    # parser.set_default_subparser("build")
    # subparsers = parser.add_subparsers(dest="command", description="Build an add-on")
    subparsers = parser.add_subparsers(dest="command")
    init_parser = subparsers.add_parser("init", description="Generate python client code from openapi.json")
    test_parser = subparsers.add_parser("test", description="Run end to end, modinput tests")

    class OpenApiPath():
        DEFAULT = "output/*/static/openapi.json"

        @staticmethod
        def validate(value):
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
                l = sorted(Path().glob(OpenApiPath.DEFAULT))
                if len(l) != 1:
                    raise argparse.ArgumentTypeError(
                        f"""
                        Default path ({OpenApiPath.DEFAULT}) does not work in this case.
                        It returns {len(l)} results: {[str(x) for x in l]}
                        Define path to openapi.json
                        """
                        )
            return l[0]

    class TmpPath():
        DEFAULT = "/tmp/modinput"

        @staticmethod
        def validate(value):
            p = Path(value)
            if p.exists():
                p_resolved = p.resolve()
                target = p_resolved.parent / "backup" / datetime.now().strftime('%Y%m%d%H%M%S') / p_resolved.name
                target.mkdir(parents=True)
                p.rename(target)
            p.mkdir(parents=True)
            return p

    class ClientCodePath():
        DEFAULT = "tests/modinput/client"

        @staticmethod
        def validate(value):
            directory = Path(value)
            if directory.exists():
                raise argparse.ArgumentTypeError(f"Given directory ({value}) must not exist. It will be created.")
            if not directory.resolve().parent.exists():
                raise argparse.ArgumentTypeError(f"Given directory ({value}) parent has to exist. Create {directory.resolve().parent}")
            return directory

    init_parser.add_argument(
        "-o",
        "--openapi-json",
        type=OpenApiPath.validate,
        help="openapi.json path",
        default=OpenApiPath.DEFAULT,
    )

    init_parser.add_argument(
        "-t",
        "--tmp",
        type=TmpPath.validate,
        help="Temporary directory, where resources needed for client code creation will be stored",
        default=TmpPath.DEFAULT,
    )

    init_parser.add_argument(
        "-c",
        "--client-code",
        type=ClientCodePath.validate,
        help="Path to client code",
        default=ClientCodePath.DEFAULT,
    )

    args = parser.parse_args(argv)
    if args.command == "init":
        init_command.init(
            openapi=args.openapi_json,
            tmp=args.tmp,
            client=args.client_code,
        )

if __name__ == "__main__":
    raise SystemExit(main())