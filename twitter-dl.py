#!/usr/bin/env python


import argparse

import requests
import json
import urllib.parse
import m3u8
from pathlib import Path
import re
import ffmpeg
import shutil

class M3E8Downloader:
	def __init__(self, m3u8_url, video_id):
		self.requests = requests.Session()
		self.video_id = video_id
		self.video_host, self.m3u8_parse = self.getM3U8(m3u8_url)

	"""
	Get the M3u8 file - this is where rate limiting has been happening
	"""
	def getM3U8(self, m3u8_url):
		# Get m3u8
		m3u8_response = requests.Session().get(m3u8_url)

		m3u8_url_parse = urllib.parse.urlparse(m3u8_url)
		video_host = m3u8_url_parse.scheme + '://' + m3u8_url_parse.hostname

		m3u8_parse = m3u8.loads(m3u8_response.text)
		return video_host, m3u8_parse

	def download(self, resolution=0, output_dir='./output'):
		playlist = self.m3u8_parse
		video_host = self.video_host
		video_id = self.video_id

		if playlist.is_variant:
			print('[+] Multiple resolutions found. Slurping all resolutions.')

			# find out the required resolution
			resolution_playlists = []
			if resolution == 0:
				for plist in playlist.playlists:
					resolution_playlists.append(plist)
			else:
				if resolution <= len(playlist.playlists):
					resolution_playlists.append(playlist.playlists[resolution - 1])
				else:
					resolution_playlists.append(playlist.playlists[len(playlist.playlists) - 1])

			for plist in resolution_playlists:
				self.downloadM3u8(video_host=video_host, m3u8_plist=plist, video_id=video_id, output_dir=output_dir)

		else:
			print('[-] Sorry, single resolution video download is not yet implemented. Please submit a bug report with the link to the tweet.')


	def downloadM3u8(self, video_host, m3u8_plist, video_id, output_dir='./output'):
		resolution = str(m3u8_plist.stream_info.resolution[0]) + 'x' + str(m3u8_plist.stream_info.resolution[1])
		video_file_name = video_id + '_' + resolution + '.mp4'
		video_file = str(Path(output_dir) / video_file_name)

		# Avoid duplicate
		if Path.exists(Path(video_file)):
			print('[+] Exists ' + video_file_name)
			return video_file

		cache_dir = str(Path(output_dir) / video_id)
		Path.mkdir(Path(cache_dir), parents=True, exist_ok=True)

		print('[+] Downloading ' + video_file_name)

		playlist_url = video_host + m3u8_plist.uri
		ts_m3u8_response = requests.Session().get(playlist_url, headers={'Authorization': None})
		ts_m3u8_parse = m3u8.loads(ts_m3u8_response.text)

		ts_list = []
		for ts_uri in ts_m3u8_parse.segments.uri:
			ts_file = requests.get(video_host + ts_uri)
			fname = ts_uri.split('/')[-1]
			ts_path = Path(cache_dir) / Path(fname)
			ts_list.append(ts_path)

			ts_path.write_bytes(ts_file.content)

		ts_full_file = Path(cache_dir) / Path(resolution + '.ts')
		ts_full_file = str(ts_full_file)

		with open(str(ts_full_file), 'wb') as wfd:
			for f in ts_list:
				with open(f, 'rb') as fd:
					shutil.copyfileobj(fd, wfd, 1024 * 1024 * 10)

		print('\t[*] Doing the magic ...')
		ffmpeg \
			.input(ts_full_file) \
			.output(video_file, acodec='copy', vcodec='libx264', format='mp4', loglevel='error') \
			.overwrite_output() \
			.run()

		print('\t[+] Doing cleanup')

		for ts in ts_list:
			p = Path(ts)
			p.unlink()

		p = Path(ts_full_file)
		p.unlink()

		Path.rmdir(Path(cache_dir))

		return video_file


	def __debug(self, msg_prefix, msg_body, msg_body_full = ''):
		if self.debug == 0:
			return

		if self.debug == 1:
			print('[Debug] ' + '[' + msg_prefix + ']' + ' ' + msg_body)

		if self.debug == 2:
			print('[Debug+] ' + '[' + msg_prefix + ']' + ' ' + msg_body + ' - ' + msg_body_full)


class TwitterDownloader:
	"""
	tw-dl offers the ability to download videos from Twitter feeds.

	**Disclaimer** I wrote this to recover a video for which the original was lost. Consider copyright before downloading
	content you do not own.
	"""
	video_player_prefix = 'https://twitter.com/i/videos/tweet/'
	video_api = 'https://api.twitter.com/1.1/videos/tweet/config/'
	tweet_data = {}

	def __init__(self, tweet_url, output_dir = './output', resolution = 0, debug = 0):
		self.tweet_url = tweet_url
		self.output_dir = output_dir
		self.debug = debug
		if resolution < 0:
			resolution = 0
		self.resolution = resolution

		if debug > 2:
			self.debug = 2

		"""
		We split on ? to clean up the URL. Sharing tweets, for example, 
		will add ? with data about which device shared it.
		The rest is just getting the user and ID to work with.
		"""
		self.tweet_data['tweet_url'] = tweet_url.split('?', 1)[0]
		self.tweet_data['user'] = self.tweet_data['tweet_url'].split('/')[3]
		self.tweet_data['id'] = self.tweet_data['tweet_url'].split('/')[5]

		self.output_dir = output_dir

		self.requests = requests.Session()

	def download(self):
		self.__debug('Tweet URL', self.tweet_data['tweet_url'])

		# Get the bearer token
		token = self.__get_bearer_token()

		# Get the M3u8 file - this is where rate limiting has been happening
		m3u8_url = self.__get_playlist(token)
		downloader = M3E8Downloader(m3u8_url, self.tweet_data['id'])
		downloader.download(resolution=1, output_dir=self.output_dir)


	def __get_bearer_token(self):
		video_player_url = self.video_player_prefix + self.tweet_data['id']
		video_player_response = self.requests.get(video_player_url).text
		self.__debug('Video Player Body', '', video_player_response)

		js_file_url  = re.findall('src="(.*js)', video_player_response)[0]
		js_file_response = self.requests.get(js_file_url).text
		self.__debug('JS File Body', '', js_file_response)

		bearer_token_pattern = re.compile('Bearer ([a-zA-Z0-9%-])+')
		bearer_token = bearer_token_pattern.search(js_file_response)
		bearer_token = bearer_token.group(0)
		self.requests.headers.update({'Authorization': bearer_token})
		self.__debug('Bearer Token', bearer_token)
		self.__get_guest_token()

		return bearer_token


	def __get_playlist(self, token):
		player_config_req = self.requests.get(self.video_api + self.tweet_data['id'] + '.json')

		player_config = json.loads(player_config_req.text)

		if 'errors' not in player_config:
			self.__debug('Player Config JSON', '', json.dumps(player_config))
			m3u8_url = player_config['track']['playbackUrl']

		else:
			self.__debug('Player Config JSON - Error', json.dumps(player_config['errors']))
			print('[-] Rate limit exceeded. Could not recover. Try again later.')
			sys.exit(1)

		return m3u8_url

	"""
	Thanks to @devkarim for this fix: https://github.com/h4ckninja/twitter-video-downloader/issues/2#issuecomment-538773026
	"""
	def __get_guest_token(self):
		res = self.requests.post("https://api.twitter.com/1.1/guest/activate.json")
		res_json = json.loads(res.text)
		self.requests.headers.update({'x-guest-token': res_json.get('guest_token')})


	def __debug(self, msg_prefix, msg_body, msg_body_full = ''):
		if self.debug == 0:
			return

		if self.debug == 1:
			print('[Debug] ' + '[' + msg_prefix + ']' + ' ' + msg_body)

		if self.debug == 2:
			print('[Debug+] ' + '[' + msg_prefix + ']' + ' ' + msg_body + ' - ' + msg_body_full)



if __name__ == '__main__':
	import sys

	if sys.version_info[0] == 2:
		print('Python3 is required.')
		sys.exit(1)

	parser = argparse.ArgumentParser()
	parser.add_argument('tweet_url', help = 'The video URL on Twitter (https://twitter.com/<user>/status/<id>).')
	parser.add_argument('-o', '--output', dest='output', default = './output', help = 'The directory to output to. The structure will be: <output>/video/.')
	parser.add_argument('-d', '--debug', default=0, action='count', dest='debug', help = 'Debug. Add more to print out response bodies (maximum 2).')
	parser.add_argument('-r', '--resolution', dest='resolution', default=0, help='The resolution of video. 0 = All, 1 = Low (320*180), 2 Medium (640*360), 3 High (1280*720).')
	args = parser.parse_args()

	twitter_dl = TwitterDownloader(args.tweet_url, args.output, int(args.resolution), args.debug)
	twitter_dl.download()
