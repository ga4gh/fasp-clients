import requests
import json
import re
#from builtins import None

class DRSClient:
	'''Basic DRS functions, no bundle handling'''    

	def __init__(self, api_url_base, access_id=None, public=False, debug=False):
		'''Initialize a DRS Client for the service at the specified url base
		api_url_base
		access_id  the default access id to use when obtaining a URL for a  given object id
		public an indicator that the data to be accessed through this client is public, adn that suthentication is not required
	 -boolean
	 debug - whether debug level informstion should be printed
		'''
		self.api_url_base = api_url_base
		self.access_id = access_id
		self.id = None
		self.name = None
		self.version = None
		self.debug = debug
		self.public = public
		self.authorized = False
		

	@classmethod
	def fromRegistryEntry(cls, registryEntry):
		''' Instantiate a DRS Client from information in a GA4GH Registry 
		'''
		instance = cls(registryEntry['url'])
		instance.id = registryEntry['id']
		instance.name = registryEntry['name']
		instance.version = registryEntry['version']
		return instance
			

	# Get info about a DrsObject
	# See https://ga4gh.github.io/data-repository-service-schemas/preview/develop/docs/#_get_object
	def get_object(self, object_id, expand=False):
		''' Implementation of the DRS getObject method
		object_id
		expand - whether or not bundles should be expanded - boolean 
		'''
		api_url = '{0}/ga4gh/drs/v1/objects/{1}'.format(self.api_url_base, object_id)
		if expand:
			api_url += '?expand=true'
		if self.debug:
			print(api_url)
		# headers generated error on SRA, doesn't seem to be required by the others
		#headers = {'Content-Type': 'application/json'}
		#response = requests.get(api_url, headers=headers)
		response = requests.get(api_url)
		response.raise_for_status()
		resp = response.content.decode('utf-8')

		return json.loads(resp)
		#=======================================================================
		# if response.status_code == 200:
		# 	resp = response.content.decode('utf-8')
		# 	return json.loads(resp)
		# else:
		# 	print(response.content.decode('utf-8'))
		# 	return response.status_code
		#=======================================================================

	# Get info about a DrsObject
	# See https://ga4gh.github.io/data-repository-service-schemas/preview/develop/docs/#_get_object
	def get_objects(self, object_list):
		''' Implementation of the DRS 1,2 getObject method to retieve a selection of DRS objects
		object_list
		'''
		api_url = '{0}/ga4gh/drs/v1/objects'.format(self.api_url_base)
		if self.debug:
			print(api_url)
		# headers generated error on SRA, doesn't seem to be required by the others
		#headers = {'Content-Type': 'application/json'}
		#response = requests.get(api_url, headers=headers)
		body = {'selection':object_list}
		response = requests.post(api_url, json=body)
		response.raise_for_status()
		resp = response.content.decode('utf-8')
		return json.loads(resp)
		#=======================================================================
		# if response.status_code == 200:
		# 	resp = response.content.decode('utf-8')
		# 	return json.loads(resp)
		# else:
		# 	print(response.content.decode('utf-8'))
		# 	return response.status_code
		#=======================================================================

	# Get a URL for fetching bytes. 
	# See https://ga4gh.github.io/data-repository-service-schemas/preview/develop/docs/#_get_access_url
	def get_access_url(self, object_id, access_id=None):
		''' Implementation of the DRS get URL to access bytes method
		object_id
		access_id a valid  access id for this object_id on the specified DRS server
		by default the access id supplied for the client will be used
		'''
		if access_id == None:
			access_id = self.access_id
		
		if not self.public:
			headers = self.getHeaders()
		else:
			headers ={}
		#headers['Content-Type'] = 'application/json'
		api_url = '{0}/ga4gh/drs/v1/objects/{1}/access/{2}'.format(self.api_url_base, object_id, access_id)
		if self.debug:
			print(api_url)
		response = requests.get(api_url, headers=headers)
		if self.debug: print(response)
		if response.status_code == 200:
			resp = response.content.decode('utf-8')
			return json.loads(resp)['url']
		if response.status_code == 401:
			print('Unauthorized for that DRS id')
			return None
		else:
			print (response)
			print (response.content)
			return None
	

	def get_url_for_region(self, object_id, region):
		''' get an access url for the object in the specified region
		object_id
		region al valid region for this object_id on the specified DRS server

		'''
		access_methods = self.get_object(object_id)['access_methods']
		am = next((sub for sub in access_methods if 'region' in sub and sub['region'] == region), None)
		if am == None:
			print ('object not in region {}'.format(region))
			return None
		return self.get_access_url(object_id, am['access_id'])
		
	def get_host(self):
		''' get the host for DRS Server'''
		p = re.compile("http[s]?://(.*)")
		m = p.match(self.api_url_base)
		return m.group(1)
		
	
	def getHeaders(self): 
		return {'Authorization' : 'Bearer {0}'.format(self.access_token) }