from flask import Flask, request, make_response, abort, jsonify
import gluster

app = Flask(__name__)


@app.route("/")
def index():
    return "Good morning sir\n"


@app.route("/files", methods=['GET'])
def list_file():
    files = gluster.file_list()
    return jsonify(files=files)


@app.route("/files/<filename>", methods=['POST'])
def upload_file(filename):
    if request.content_length is not None:
        oid = gluster.save_file(request.stream, filename)
        return jsonify(oid=oid)
    abort(400, 'request is empty')


@app.route('/files/<oid>', methods=['GET'])
def get_file(oid):
    f = gluster.get_file(oid)
    if f is not None:
        response = make_response(f.read())
        return response
    abort(404, 'file not found')


@app.route('/files/<oid>', methods=['REMOVE'])
def remove_file(oid):
    f = gluster.remove_file(oid)
    if f is not None:
        return jsonify(message="done")
    abort(404, 'file not found')


@app.errorhandler(404)
def custom404(error):
    response = jsonify({'message': error.description})
    return response


@app.errorhandler(400)
def custom400(error):
    response = jsonify({'message': error.description})
    return response


@app.errorhandler(500)
def custom500(error):
    response = jsonify({'message': "Server error"})
    return response


if __name__ == "__main__":
    app.run()