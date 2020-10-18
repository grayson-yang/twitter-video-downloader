import json

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


@app.route('/1.1/videos/tweet/get_m3u8', methods=['GET'])
def get_twitter_m3u8():
    twitter_link = request.args.get("twitter_link") if "twitter_link" in request.args else ""
    if len(twitter_link) <= 0:
        abort(400)
    # client transfer the full link
    twitter_url = twitter_link
    output_dir = "D:/output"
    twitter_dl = TwitterDownloader(twitter_url, output_dir=output_dir)
    player_config = twitter_dl.get_playlist_buffer()

    return jsonify(player_config), 200


""" cache for get_media_tweets API """
__cache_media_tweets = {}


def parseToInt(value, default, positive=True):
    value = default if value is None else value;
    try:
        value = int(value)
    except:
        value = default
    value = abs(value) if positive is True else value
    return value


@app.route('/2/timeline/media/<string:screen_name>.json', methods=['GET'])
def get_media_tweets(screen_name):
    print('get_media_tweets for ' + screen_name)

    cursor = parseToInt(request.args.get("cursor"), 0)
    count = parseToInt(request.args.get("count"), 10)

    if screen_name.lower() in __cache_media_tweets:
        print('find cache for ' + screen_name)
        video_list = __cache_media_tweets[screen_name.lower()]
    else:
        twitter_home_url = 'https://twitter.com/'
        screen_name_url = twitter_home_url + screen_name
        output_dir = 'D:/output'
        media_viewer = TwitterMediaViewer(screen_name_url, output_dir=output_dir)
        tweets = media_viewer.get_tweets_from_disk()
        if tweets is None:
            return jsonify({'tweets': []})
        video_list = media_viewer.filter_tweets_video(tweets)
        __cache_media_tweets[screen_name.lower()] = video_list
    if cursor >= len(video_list):
        return jsonify({'tweets': {}, 'cursor': -1})
    capacity = len(video_list) - cursor
    count = capacity if count > capacity else count
    video_list = video_list[cursor:cursor + count]
    result_dict = {}
    for video in video_list:
        result_dict[video.get('tweet_id')] = video
    next_cursor = cursor + count
    response = make_response(jsonify({'tweets': result_dict, 'cursor': next_cursor}))
    return response


@app.route('/1/twitter/white_list.json', methods=['GET'])
def get_twitter_white_list():
    with open('document/white_list.json', 'r') as f:
        f.seek(0, 0)
        lines = f.readlines()
    content = ''
    for line in lines:
        content += line

    white_list = json.loads(content)
    return jsonify({'white_list': white_list})


if __name__ == '__main__':
    app.run(host='10.154.10.111', port=5000, debug=True)
