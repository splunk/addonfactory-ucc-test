
# Create directory structure and open the tmp directory (run in terminal: mkdir -p tmp/restapi_client ; mkdir -p tmp/generator ; cd tmp)

from pathlib import Path 

def create_directory_structure(root_directory: Path):
    root_directory.mkdir()

# Save your openapi.json file to the directory
# Download the rest.mustache file (wget https://raw.githubusercontent.com/swagger-api/swagger-codegen/master/modules/swagger-codegen/src/main/resources/python/rest.mustache)
# Splunk does not expect body for DELETE requests, so we need to revert modifications done for https://github.com/swagger-api/swagger-codegen/issues/9558 (sed "s/request_body[[:blank:]]=[[:blank:]]\'{}\'/request_body = None/g" rest.mustache > generator/rest.mustache). If you want to understand exactly which line of rest.mustache is affected: https://github.com/swagger-api/swagger-codegen/blob/master/modules/swagger-codegen/src/main/resources/python/rest.mustache#L150
# Create client (docker run --rm -v ${PWD}:/local swaggerapi/swagger-codegen-cli-v3 generate -i /local/openapi.json -l python -o /local/restapi_client -t /local/generator/); it should appear in restapi_client directory
# Open restapi_client directory and read README.md to find out the details of how the client should be installed, imported and used. (cd restapi_client ; more README.md)
# Install the client (python setup.py install --user)
# You can use below code as an inspiration for your own script that imports the client and uses for TA configuration