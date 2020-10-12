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

		self.video_host, self.m3u8_parse = self.getM3U8Summary(m3u8_url)


	"""
	Get the M3u8 file - this is where rate limiting has been happening, such as
		https://video.twimg.com/ext_tw_video/1033356336052850688/pu/pl/wQcHxx2l-D3fB9h7.m3u8?tag=5
	"""
	def getM3U8Summary(self, m3u8_url):

		m3u8_url_parse = urllib.parse.urlparse(m3u8_url)
		video_host = m3u8_url_parse.scheme + '://' + m3u8_url_parse.hostname

		m3u8_response = self.get_playfile_m3u8(m3u8_url_parse.path)
		if m3u8_response is not None:
			m3u8_parse = m3u8.loads(m3u8_response)
		else:
			# Get m3u8
			m3u8_response = self.requests.get(m3u8_url)
			m3u8_parse = m3u8.loads(m3u8_response.text)

			# save m3u8 summary file
			self.save_playfile_m3u8(m3u8_url_parse.path, m3u8_response.text)

		return video_host, m3u8_parse


	"""
	@param resolution, 0 all resolution, 1 the first resolution, ...
	"""
	def download(self, resolution=0, save_as_mp4=False):
		playlist = self.m3u8_parse
		video_host = self.video_host
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
				resolution_str, ts_list = self.downloadM3u8(video_host=video_host, m3u8_plist=plist)
				if save_as_mp4 is True:
					self.merge_ts_files(resolution_str, ts_list)

		else:
			print('[-] Sorry, single resolution video download is not yet implemented. Please submit a bug report with the link to the tweet.')


	"""
	@param m3u8_uri, such as 
		/ext_tw_video/1033356336052850688/pu/pl/wQcHxx2l-D3fB9h7.m3u8
		or
		/ext_tw_video/1033356336052850688/pu/pl/640x360/0ClFYlDWV-Fr3ZXx.m3u8
	"""
	def save_playfile_m3u8(self, m3u8_uri, m3u8_text):

		Path.mkdir(Path(self.output_dir) / m3u8_uri[1:m3u8_uri.rindex('/')], parents=True, exist_ok=True)
		with open(Path(self.output_dir) / m3u8_uri[1:], 'w') as f:
			f.writelines(m3u8_text)

	"""
	@param m3u8_uri, such as 
		/ext_tw_video/1033356336052850688/pu/pl/wQcHxx2l-D3fB9h7.m3u8
		or
		/ext_tw_video/1033356336052850688/pu/pl/640x360/0ClFYlDWV-Fr3ZXx.m3u8
	"""
	def get_playfile_m3u8(self, m3u8_uri):
		if Path.exists(Path(self.output_dir) / m3u8_uri[1:]) is False:
			return None
		with open(Path(self.output_dir) / m3u8_uri[1:], 'r') as f:
			f.seek(0, 0)
			lines = f.readlines()
		content = ''
		for line in lines:
			content += line
		return content if len(content) > 0 else None;


	def downloadM3u8(self, video_host, m3u8_plist):

		resolution_str = str(m3u8_plist.stream_info.resolution[0]) + 'x' + str(m3u8_plist.stream_info.resolution[1])
		print('\t[+] Checking ' + m3u8_plist.uri)

		# get the buffer fistly
		ts_m3u8_response = self.get_playfile_m3u8(m3u8_plist.uri)
		if ts_m3u8_response is not None:
			ts_m3u8_parse = m3u8.loads(ts_m3u8_response)
			print('\t\t[+] Exists ' + m3u8_plist.uri)
		else:
			print('\t\t[+] Downloading ' + m3u8_plist.uri)
			playlist_url = video_host + m3u8_plist.uri
			ts_m3u8_response = self.requests.get(playlist_url, headers={'Authorization': None})
			ts_m3u8_parse = m3u8.loads(ts_m3u8_response.text)
			# save m3u8 play file
			self.save_playfile_m3u8(m3u8_plist.uri, ts_m3u8_response.text)

		ts_list = []
		print('\t\t[+] Checking segments')
		for ts_uri in ts_m3u8_parse.segments.uri:
			ts_dir = ts_uri[1:ts_uri.rindex('/')]
			Path.mkdir(Path(self.output_dir) / ts_dir, parents=True, exist_ok=True)
			ts_path = Path(self.output_dir) / ts_uri[1:]
			if Path.exists(ts_path) is False:
				ts_file = requests.get(video_host + ts_uri)
				ts_path.write_bytes(ts_file.content)
			ts_list.append(ts_path)

		return resolution_str, ts_list


	def merge_ts_files(self, resolution_str, ts_list):
		video_file_name = self.video_id + '_' + resolution_str + '.mp4'
		video_file = str(Path(self.output_dir) / video_file_name)
		print('\t\t[+] Checking ' + video_file)

		# Avoid duplicate
		if Path.exists(Path(video_file)):
			print('\t\t\t[+] Exists ' + video_file_name)
			return video_file

		print('\t\t\t[+] Generating ' + video_file)
		cache_dir = str(Path(self.output_dir) / self.video_id)
		Path.mkdir(Path(cache_dir), parents=True, exist_ok=True)
		ts_full_file = Path(cache_dir) / Path(resolution_str + '.ts')
		ts_full_file = str(ts_full_file)

		with open(str(ts_full_file), 'wb') as wfd:
			for f in ts_list:
				with open(f, 'rb') as fd:
					shutil.copyfileobj(fd, wfd, 1024 * 1024 * 10)

		print('\t\t\t[*] Doing the magic ...')
		ffmpeg \
			.input(ts_full_file) \
			.output(video_file, acodec='copy', vcodec='libx264', format='mp4', loglevel='error') \
			.overwrite_output() \
			.run()

		print('\t\t\t[+] Doing cleanup')

		# do not remove the ts file. can add judgement for this later.
		# for ts in ts_list:
		# 	p = Path(ts)
		# 	p.unlink()

		try:
			p = Path(ts_full_file)
			p.unlink()

			Path.rmdir(Path(cache_dir))
		except:
			print("\t[+] file remove errors!")

		return video_file


if __name__ == '__main__':
	m3u8_url = "https://video.twimg.com/ext_tw_video/1033356336052850688/pu/pl/wQcHxx2l-D3fB9h7.m3u8?tag=5"
	video_id = "1033356336052850688"
	resolution = 0
	output_dir = "D:/output"
	m3e8Loader = M3U8Downloader(m3u8_url=m3u8_url, video_id=video_id, output_dir=output_dir)
	m3e8Loader.download(resolution=resolution, save_as_mp4=True)
