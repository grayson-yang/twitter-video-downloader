from flask import Flask, jsonify, abort, make_response, request

app = Flask(__name__)


@app.after_request
def af_request(resp):
    resp = make_response(resp)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET,POST'
    resp.headers['Access-Control-Allow-Headers'] = 'x-requested-with,content-type'
    return resp


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.route('/1.1/videos/tweet/config/<string:twitter_id>.json', methods=['GET'])
def get_twitter_m3u8(twitter_id):
    if len(twitter_id) <= 0:
        abort(400)
    track = {
        "contentType": "media_entity",
        "durationMs": 140000,
        "playbackUrl": "http://127.0.0.1:8081/ext_tw_video/1033356336052850688/pu/pl/wQcHxx2l-D3fB9h7.m3u8?tag=5",
        "playbackType": "application/x-mpegURL"
    }
    return jsonify({'track': track}), 200


if __name__ == '__main__':
    app.run(debug=True)