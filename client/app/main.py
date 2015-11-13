from flask import Flask, request, make_response, abort, jsonify
import os
import gluster

app = Flask(__name__)


@app.route("/")
def index():
    return "Good morning sir"


@app.route("/files", methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST' and request.content_length is not None:
        dir = os.path.dirname(os.path.realpath(__file__))
        oid = gluster.save_file(request.stream)
        return jsonify(oid=1)
    return jsonify(message="send file")


@app.route('/files/<oid>', methods=['GET'])
def get_file(oid):
    f = gluster.get_file(oid)
    if file is not None:
        response = make_response(f.read())
        return response
    abort(404)


if __name__ == "__main__":
    app.run(debug=True)