#!/usr/bin/env python

import requests
import urllib.parse
import m3u8
from pathlib import Path
import ffmpeg
import shutil

"""
Usage:
	m3u8_url = "https://video.twimg.com/ext_tw_video/1033356336052850688/pu/pl/wQcHxx2l-D3fB9h7.m3u8?tag=5"
	video_id = "wQcHxx2l-D3fB9h7"
	resolution = 1
	output_dir = "./output"
	m3e8Loader = M3U8Downloader(m3u8_url=m3u8_url, video_id=video_id)
	m3e8Loader.download(resolution=resolution, output_dir=output_dir)
"""
class M3U8Downloader:

	def __init__(self, m3u8_url, video_id, output_dir='./output'):
		self.requests = requests.Session()
		self.video_id = video_id
		self.output_dir = output_dir
		cache_dir = str(Path(self.output_dir) / video_id)
		self.cache_dir = cache_dir
		Path.mkdir(Path(cache_dir), parents=True, exist_ok=True)

		self.video_host, self.m3u8_parse = self.getM3U8Summary(m3u8_url)


	"""
	Get the M3u8 file - this is where rate limiting has been happening
	"""
	def getM3U8Summary(self, m3u8_url):
		# Get m3u8
		m3u8_response = self.requests.get(m3u8_url)

		m3u8_url_parse = urllib.parse.urlparse(m3u8_url)
		video_host = m3u8_url_parse.scheme + '://' + m3u8_url_parse.hostname

		m3u8_parse = m3u8.loads(m3u8_response.text)

		# save m3u8 summary file
		self.saveM3U8SummaryFile(m3u8_url, m3u8_response)

		return video_host, m3u8_parse


	"""
	@param m3u8_url, such as https://video.twimg.com/ext_tw_video/1033356336052850688/pu/pl/wQcHxx2l-D3fB9h7.m3u8?tag=5
	"""
	def saveM3U8SummaryFile(self, m3u8_url, m3u8_response):
		# save m3u8 summary
		m3u8_url_parse = urllib.parse.urlparse(m3u8_url)
		# note: remove the '/' at the beginning
		m3u8_summary_dir = m3u8_url_parse.path[:m3u8_url_parse.path.rindex('/')][1:]
		m3u8_summary_name = m3u8_url_parse.path.split('/')[-1]
		Path.mkdir(Path(self.output_dir) / m3u8_summary_dir, parents=True, exist_ok=True)
		with open(Path(self.output_dir) / m3u8_summary_dir / m3u8_summary_name, 'w') as f:
			f.writelines(m3u8_response.text)

		# create folder for playlist
		m3u8_parse = m3u8.loads(m3u8_response.text)
		for play in m3u8_parse.playlists:
			Path.mkdir(Path(self.output_dir) / play.base_path[1:], parents=True, exist_ok=True)


	"""
	@param resolution, 0 all resolution, 1 the first resolution, ...
	"""
	def download(self, resolution=0):
		playlist = self.m3u8_parse
		video_host = self.video_host
		video_id = self.video_id
		if resolution < 0:
			resolution = 0

		if playlist.is_variant:
			print('[+] Multiple resolutions found. Slurping all resolutions.')

			# find out the required resolution
			filtered_playlists = []
			if resolution == 0:
				for plist in playlist.playlists:
					filtered_playlists.append(plist)
			else:
				if resolution <= len(playlist.playlists):
					filtered_playlists.append(playlist.playlists[resolution - 1])
				else:
					filtered_playlists.append(playlist.playlists[len(playlist.playlists) - 1])

			for plist in filtered_playlists:
				self.downloadM3u8(video_host=video_host, m3u8_plist=plist, video_id=video_id)

		else:
			print('[-] Sorry, single resolution video download is not yet implemented. Please submit a bug report with the link to the tweet.')


	"""
	@param m3u8_url, such as https://video.twimg.com/ext_tw_video/1033356336052850688/pu/pl/640x360/0ClFYlDWV-Fr3ZXx.m3u8
	"""
	def saveM3U8PlayFile(self, m3u8_url, m3u8_response):
		m3u8_url_parse = urllib.parse.urlparse(m3u8_url)
		with open(Path(self.output_dir) / m3u8_url_parse.path[1:], 'w') as f:
			f.writelines(m3u8_response.text)


	def downloadM3u8(self, video_host, m3u8_plist, video_id):
		resolution = str(m3u8_plist.stream_info.resolution[0]) + 'x' + str(m3u8_plist.stream_info.resolution[1])
		video_file_name = video_id + '_' + resolution + '.mp4'
		video_file = str(Path(self.output_dir) / video_file_name)

		# Avoid duplicate
		if Path.exists(Path(video_file)):
			print('[+] Exists ' + video_file_name)
			return video_file

		print('[+] Downloading ' + video_file_name)

		playlist_url = video_host + m3u8_plist.uri
		ts_m3u8_response = self.requests.get(playlist_url, headers={'Authorization': None})
		ts_m3u8_parse = m3u8.loads(ts_m3u8_response.text)
		# save m3u8 play file
		self.saveM3U8PlayFile(playlist_url, ts_m3u8_response)

		ts_list = []
		for ts_uri in ts_m3u8_parse.segments.uri:
			ts_file = requests.get(video_host + ts_uri)
			ts_dir = ts_uri[1:ts_uri.rindex('/')]
			Path.mkdir(Path(self.output_dir) / ts_dir, parents=True, exist_ok=True)
			ts_path = Path(self.output_dir) / ts_uri[1:]
			ts_list.append(ts_path)

			ts_path.write_bytes(ts_file.content)

		Path.mkdir(Path(self.cache_dir), parents=True, exist_ok=True)
		ts_full_file = Path(self.cache_dir) / Path(resolution + '.ts')
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

		# do not remove the ts file. can add judgement for this later.
		# for ts in ts_list:
		# 	p = Path(ts)
		# 	p.unlink()

		try:
			p = Path(ts_full_file)
			p.unlink()

			Path.rmdir(Path(self.cache_dir))
		except:
			print("\t[+] file remove errors!")

		return video_file


if __name__ == '__main__':
	m3u8_url = "https://video.twimg.com/ext_tw_video/1033356336052850688/pu/pl/wQcHxx2l-D3fB9h7.m3u8?tag=5"
	video_id = "1033356336052850688"
	resolution = 0
	output_dir = "D:/output"
	m3e8Loader = M3U8Downloader(m3u8_url=m3u8_url, video_id=video_id, output_dir=output_dir)
	m3e8Loader.download(resolution=resolution)
