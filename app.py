from flask import Flask, jsonify, abort, make_response, request
from library.twitter_dl import TwitterDownloader
import urllib.parse

from library.twitter_list_dl import TwitterMediaViewer

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
    resolution = 1
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
    resolution = 1
    debug = 0
    twitter_dl = TwitterDownloader(twitter_url, output_dir, resolution, debug)
    player_config = twitter_dl.get_playlist()

    playbackUrl = player_config.get("track").get("playbackUrl")
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


@app.route('/2/timeline/media/<string:screen_name>.json', methods=['GET'])
def get_media_tweets(screen_name):
    print('get_media_tweets for ' + screen_name)
    twitter_home_url = 'https://twitter.com/'
    screen_name_url = twitter_home_url + screen_name

    media_viewer = TwitterMediaViewer(screen_name_url, 'D:/output')
    tweets = media_viewer.get_tweets_from_disk()
    if tweets is None:
        return jsonify({'tweets': []})
    video_list = media_viewer.filter_tweets_video(tweets)
    return jsonify({'tweets': video_list})


if __name__ == '__main__':
    app.run(host='10.154.10.111', port=5000, debug=True)
