from flask import Flask, jsonify, abort, make_response, request
from twitter_dl import TwitterDownloader
import urllib.parse
import _thread

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

def startDownload(twitter_url):
    output_dir = 'D:/output'
    resolution = 0
    debug = 0
    twitter_dl = TwitterDownloader(twitter_url, output_dir, resolution, debug)
    twitter_dl.download()


@app.route('/1.1/videos/tweet/get_m3u8', methods=['GET'])
def get_twitter_m3u8():
    twitter_link = request.args.get("twitter_link") if "twitter_link" in request.args else ""
    if len(twitter_link) <= 0:
        abort(400)
    # client transfer the full link
    twitter_url = twitter_link
    output_dir = 'D:/output'
    resolution = 0
    debug = 0
    twitter_dl = TwitterDownloader(twitter_url, output_dir, resolution, debug)
    playbackUrl = twitter_dl.get_playlist()
    print('playbackUrl = ' + playbackUrl)

    m3u8_url_parse = urllib.parse.urlparse(playbackUrl)
    video_host = 'http' + '://' + '10.154.10.111:8081' + m3u8_url_parse.path

    track = {
        "contentType": "media_entity",
        "durationMs": 140000,
        "playbackUrl": video_host,
        "playbackType": "application/x-mpegURL"
    }
    startDownload(twitter_url)
    return jsonify({'track': track}), 200


if __name__ == '__main__':
    app.run(host='10.154.10.111', port=5000, debug=True)
