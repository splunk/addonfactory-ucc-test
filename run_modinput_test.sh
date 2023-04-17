OPENAPI_JSON=$1
if ! ([ -f "$OPENAPI_JSON" ] && [ "$(basename "$OPENAPI_JSON")" = "openapi.json" ]); then
  echo "Send path to openapi.json file as parameter"
  exit 1
fi

HERE=${PWD}
TMP=${HERE}/tmp
if [ -d "$TMP" ] && [ "$(ls -A $TMP)" ]; then
  timestamp=$(date +%Y-%m-%d_%H-%M-%S)
  mv $TMP "${TMP}_backedup_${timestamp}"
fi
CLIENT=restapi_client
mkdir -p ${TMP}/${CLIENT}
cp ${OPENAPI_JSON} ${TMP}
cp -R ${PWD}/swagger-codegen-generators/ ${TMP}
docker run --rm -v ${TMP}:/local swaggerapi/swagger-codegen-cli-v3 generate     -i /local/openapi.json     -l python     -o /local/${CLIENT} -t /local/swagger-codegen-generators/src/main/resources/handlebars/python/

cp test_wrapper.py ${TMP}/${CLIENT}
cd ${TMP}/${CLIENT}

python setup.py install --user
python test_wrapper.py

cd ${HERE}