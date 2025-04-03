cd ../..
poetry install
rm dist/*.whl
poetry build
deactivate

cd tests/functional/

mv splunk-example-ta/tests/ucc_modinput_functional "ucc_modinput_functional_$(date +%s)"
rm -rf splunk-example-ta
git clone https://github.com/splunk/splunk-example-ta.git
cd splunk-example-ta
./scripts/run_locally.sh

source .venv/bin/activate
pip install ../../../dist/*.whl
ucc-test-modinput init

export MODINPUT_TEST_SPLUNK_HOST=localhost
export MODINPUT_TEST_SPLUNK_PORT=8089
export MODINPUT_TEST_SPLUNK_USERNAME=admin
export MODINPUT_TEST_SPLUNK_PASSWORD_BASE64=$(ucc-test-modinput base64encode -s 'Chang3d!')

# export HTTP_HOST="aG9zdC5kb2NrZXIuaW50ZXJuYWwK"
# export HTTP_USERNAME="dXNlcm5hbWUK"
# export HTTP_PASSWORD="cGFzc3dvcmQK"
# export SOCKS5_HOST="aG9zdC5kb2NrZXIuaW50ZXJuYWwK"
# export SOCKS5_USERNAME="dXNlcm5hbWUK"
# export SOCKS5_PASSWORD="cGFzc3dvcmQK"

export MODINPUT_TEST_EXAMPLE_API_KEY_BASE64=$(ucc-test-modinput base64encode -s 'super-secret-api-token')

pytest tests/ucc_modinput_functional
# ln -s ../../../splunk_add_on_ucc_modinput_test splunk_add_on_ucc_modinput_test
