
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