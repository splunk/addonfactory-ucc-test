# ucc-test-modinput CLI tool

ucc-test-modinput CLI is a supporting tool.

It comes with following arguments:

- `--help` or `-h` ; shows help message and exits ; you can use it for arguments as well - eg. `ucc-test-modinput base64encode -h` will show help message for `base64encode`

- `--version` - shows program's version number and exit 

- `base64encode` - converts complex string (due to special characters or structure) to base64 string

    - `--string` or `-s` ; `-s [string you want to encode]` - eg. `base64encode -s ThisIsMyPassword`

    - `--file` or `-f` ; `-f [text file path; string from the file will be encoded]` - eg. `ucc-test-modinput base64encode -f ~/client_secret.json`

- `base64decode -s [string you want to decode]` - eg. `ucc-test-modinput base64decode -s VGghczEkTXlQQHNzdzByZA==`

- `gen` - does two things: 1. creates add-on SDK from given openapi.json and 2. creates splunk client module and checks if existing (`ucc_modinput_functional/splunk/client/client.py`) is the same. 

    - `--openapi-json` or `-o` ; `-o [path to openapi.json / source file ]` - default value is `output/*/appserver/static/openapi.json` ; refer to [UCC documentation](https://splunk.github.io/addonfactory-ucc-generator/openapi/#how-to-find-the-document) to learn more where you can find this document

    - `--client-code` or `-c` ; `-c [path to client code / target directory]` - default value is set to repo root directory ; this is where `swagger_client` directory will be saved or overwriten if some exists already. The directory contains client code for TA REST API and `swagger_client/README.md` file that documents the client API

    - `--tmp` or `-t` ; `-t [path to directory where temporary files are stored]` - default value is set to `/modinput/` subdirectory of [directory used for temporary files](https://docs.python.org/3/library/tempfile.html#tempfile.gettempdir)

    - `--platform` or `-p` - not used by default ; [`--platform`](https://docs.docker.com/build/building/multi-platform/) flag that can be used to run [swaggerapi/swagger-codegen-cli-v3 docker image](https://hub.docker.com/r/swaggerapi/swagger-codegen-cli-v3)

    - `--skip-splunk-client-check` - exisitng splunk client will not be checked aginst consistency with swagger client that may lead to inconsistent state of splunk client; this is `gen` specific flag and does not exists for `init`

    - `--force-splunk-client-overwritten` - existing splunk client will be backup and overwritten by new one; this is `gen` specific flag and does not exists for `init`

- `init` - initialize modinput tests (you can read more on that [here](./before_you_write_your_first_line_of_code.md/#ucc-test-modinput-init)) and runs `gen` to have add-on SDK created ; none additional argument is required for the initialization step, so argument list is as for `gen` (excluding `--skip-splunk-client-check`, `--force-splunk-client-overwritten`)