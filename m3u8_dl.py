#!/usr/bin/env python

import requests
import urllib.parse
import m3u8
from pathlib import Path
import ffmpeg
import shutil

"""
Usage:
	m3u8_url="https://video.twimg.com/ext_tw_video/1033356336052850688/pu/pl/wQcHxx2l-D3fB9h7.m3u8?tag=5"
	video_id="20202020"
	resolution=0
	output_dir="./output
	m3e8Loader = M3E8Downloader(m3u8_url=m3u8_url, video_id=video_id)
	m3e8Loader.download(resolution=resolution, output_dir=output_dir)
"""
class M3U8Downloader:
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

	"""
	@param resolution, 0 all resolution, 1 the first resolution, ...
	"""
	def download(self, resolution=0, output_dir='./output'):
		playlist = self.m3u8_parse
		video_host = self.video_host
		video_id = self.video_id
		if resolution < 0:
			resolution = 0

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