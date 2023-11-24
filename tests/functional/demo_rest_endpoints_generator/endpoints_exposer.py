from typing import Dict
from flask import Flask, request, jsonify

app = Flask(__name__)

endpoints_data: Dict[str, str] = {}


def patch_endpoint(*, endpoint_name: str, request_data: str) -> str:
    global endpoints_data
    endpoints_data[endpoint_name] = request_data
    return jsonify({"patch_request_data": f"{endpoint_name} patched"})


def get_endpoint(*, endpoint_name: str) -> str:
    return jsonify(
        endpoints_data[endpoint_name]
        if endpoint_name in endpoints_data
        else {}
    )


@app.route("/endpoint1", methods=["PATCH"])
def patch_endpoint1() -> str:
    return patch_endpoint(
        endpoint_name="/endpoint1", request_data=request.get_json()
    )


@app.route("/endpoint1", methods=["GET"])
def get_endpoint1() -> str:
    return get_endpoint(endpoint_name="/endpoint1")


@app.route("/endpoint2", methods=["PATCH"])
def patch_endpoint2() -> str:
    return patch_endpoint(
        endpoint_name="/endpoint2", request_data=request.get_json()
    )


@app.route("/endpoint2", methods=["GET"])
def get_endpoint2() -> str:
    return get_endpoint(endpoint_name="/endpoint2")


@app.route("/endpoint3", methods=["PATCH"])
def patch_endpoint3() -> str:
    return patch_endpoint(
        endpoint_name="/endpoint3", request_data=request.get_json()
    )


@app.route("/endpoint3", methods=["GET"])
def get_endpoint3() -> str:
    return get_endpoint(endpoint_name="/endpoint3")


if __name__ == "__main__":
    # app.run(debug=True, port=8080, host='0.0.0.0')
    app.run(debug=True, port=5000)
