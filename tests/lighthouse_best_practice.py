#-*- coding: utf-8 -*-
import sys
import socket
import ssl
import json
import requests
import urllib # https://docs.python.org/3/library/urllib.parse.html
import uuid
import re
from bs4 import BeautifulSoup
import config
from tests.utils import *

### DEFAULTS
request_timeout = config.http_request_timeout
googlePageSpeedApiKey = config.googlePageSpeedApiKey

def run_test(url, strategy='mobile', category='best-practices'):
	check_url = url.strip()
	
	pagespeed_api_request = 'https://www.googleapis.com/pagespeedonline/v5/runPagespeed?category={0}&url={1}&strategy={2}&key={3}'.format(category, check_url, strategy, googlePageSpeedApiKey)
	
	get_content = ''
	
	try:
		get_content = httpRequestGetContent(pagespeed_api_request)
	except:  # breaking and hoping for more luck with the next URL
		print(
			'Error! Unfortunately the request for URL "{0}" failed, message:\n{1}'.format(
				check_url, sys.exc_info()[0]))
		pass
		
	json_content = ''
	
	try:
		json_content = json.loads(get_content)
	except:  # might crash if checked resource is not a webpage
		print('Error! JSON failed parsing for the URL "{0}"\nMessage:\n{1}'.format(
			check_url, sys.exc_info()[0]))
		pass
	
	return_dict = {}

	score = 0
	fails = 0
	fail_dict = {}
	
	for item in json_content['lighthouseResult']['audits'].keys():
		try:
			return_dict[item] = json_content['lighthouseResult']['audits'][item]['score']

			score = score + int(json_content['lighthouseResult']['audits'][item]['score'])
			
			if int(json_content['lighthouseResult']['audits'][item]['score']) == 0:
				fails += 1
				fail_dict[item] = json_content['lighthouseResult']['audits'][item]['title']
		except:
			# has no 'numericValue'
			#print(item, 'har inget värde')
			pass
	
	review = ''
	points = 0
	
	if fails == 0:
		points = 5
		review = '* Webbplatsen följer god praxis fullt ut!\n'
	elif fails <= 2:
		points = 4
		review = '* Webbplatsen har ändå förbättrings&shy;potential.\n'
	elif fails <= 3:
		points = 3
		review = '* Genomsnittlig efterlevnad till praxis.\n'
	elif fails <= 4:
		points = 2
		review = '* Webbplatsen är ganska dålig på att följa god praxis.\n'
	elif fails > 4:
		points = 1
		review = '* Webbplatsen är inte alls bra på att följa praxis!\n'
	
	review += '* Antal problem med god praxis: {} st\n'.format(fails)
	

	if fails != 0:
		review += '\nProblem:\n'

		for key, value in return_dict.items():
			if value == 0:
				review += '* {}\n'.format(fail_dict[key])
				#print(key)
	
	return (points, review, return_dict)
