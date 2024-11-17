import requests
import sys
import getopt
import json
import os

from fasp.loc import GA4GHRegistryClient
from fasp.search.MappingLibrary import MappingLibraryClient
import pandas as pd

class DataConnectClient:

	def __init__(self, hostURL, return_type=None, row_limit=10000, debug=False, passport=None ):
		self.hostURL = self._url_format(hostURL)
		self.debug = debug
		self.return_type = return_type
		self.row_limit = row_limit
		self.headers = {
			'content-type': 'application/json'
		}
		self.passport = passport

	def set_row_limit(self, row_limit):
		self.row_limit = row_limit
		
	def set_return_type(self, return_type):
		self.return_type = return_type
		
		# Look for registered search services
	@classmethod
	def getRegisteredSearchServices(cls):
		reg = GA4GHRegistryClient()
		services = reg.getRegisteredServices('org.ga4gh:search')
		for service in services:
			#serviceType=service['type']
			print(json.dumps(service, indent=3))
			#serviceURL = service['url']
			#hostname = serviceURL.split("/")[2]

		return None

	def _url_format(self, url):
		url = str(url)
		if url.endswith('/'):
			url = url[:-1]
		return url

	def list_tables(self, requestedCatalog=None, verbose=True):

		tables = []

		if requestedCatalog == None:
			next_url = self.hostURL + "/tables"
		else:
			next_url = "{}{}{}".format(self.hostURL,'/tables/catalog/',requestedCatalog)

		self.__add_passport({})

		pageCount = 0
		if verbose:
			print("Retrieving the table list")
		while next_url != None :
			pageCount += 1
			if verbose:
				print ("____Page{}_______________".format(pageCount))
			if self.debug:
				print(f'Retrieving {next_url}')
			response = requests.get(next_url, headers=self.headers)
			result = (response.json())
			if self.debug:
				print(json.dumps(result, indent=3))
			if requestedCatalog == None and 'pagination' in result and 'next_page_url' in result['pagination']:
				next_url = result['pagination']['next_page_url']
			else:
				next_url = None
			for t in result['tables']:
				if verbose:
					print(t['name'])
				tables.append(t['name'])

		return tables

	def list_catalogs(self):
		url = self.hostURL + "/tables"

		print ("Retrieving the catalog list")
		response = requests.get(url, headers=self.headers)
		result = (response.json())
		for t in result['index']:
			print(t['description'])
		return


	def list_catalog(self, catalog):
		return self.list_tables(catalog)

	def list_table_info(self, table, verbose=False):
		url = "{}/table/{}/info".format(self.hostURL,table)
		response = requests.get(url, headers=self.headers)
		info = json.loads(response.text)
		if verbose:
			print ("_Schema for table{}_".format(table))
			print(json.dumps(info, indent=3))
		#return info
		return SearchSchema(info)
				
	def list_table_columns(self, table, descriptions=False, enums=False):
		''' List the columns in a table. More compact and practical for many purposes compared with list_table_info '''
		schema = self.list_table_info(table).schema
		if self.debug: print(json.dumps(schema, indent=3))
		for c, v in schema['data_model']['properties'].items():
			print (c)
			if descriptions:
				if 'description' in v: print (v['description'])
				if '$comment' in v: print (v['$comment'])
			if enums:
				if 'oneOf' in v:
					for c in v['oneOf']:
						print ('\t\t{}'.format(c['const']))
				if '$comment' in v: print (v['$comment'])
			print('_______________________________________')
			
	def list_column_info(self, table, verbose=False):
		url = "{}/table/{}/info".format(self.hostURL,table)
		response = requests.get(url, headers=self.headers)
		info = json.loads(response.text)
		if verbose:
			print ("_Schema for table{}_".format(table))
			print(json.dumps(info, indent=3))
		return info

	def get_mapping_template(self, table, propList=None):
		''' Get an empty template in which to create  mappings for property values 
		:param table: table for which to generate a mapping template
		:param propList: optional list of properties to include in the map
		'''
		schema = self.list_table_info(table).schema
		template = {}
		for prop, details in schema['data_model']['properties'].items():
			if propList == None or prop in propList:
				if 'oneOf' in details:
					vList = {}
					for v in details['oneOf']:
						vList[v['const']] = 'replaceThis'
						#if titles:
						#	vList[v['const']]['title'] = v['title']
					template[prop] = vList
		return template
			

	def get_decode_template(self, table, propList=None, numericCodes=True):
		''' Get a template which maps enumerated codes to their decoded values 
		:param table: table for which to generate a mapping template
		:param propList: optional list of properties to include in the map
		:param numericCodes: return codes as integers - will fail if the codes are not
		'''
		schema = self.list_table_info(table).schema
		template = {}
		for prop, details in schema['data_model']['properties'].items():
			if propList == None or prop in propList:
				if 'oneOf' in details:
					vList = {}
					for v in details['oneOf']:
						if numericCodes:
							vList[int(v['const'])] = v['title']
						else:
							vList[v['const']] = v['title']
						#if titles:
						#	vList[v['const']]['title'] = v['title']
					template[prop] = vList
		return template

		
	def get_mappings_for_table(self, table, mapset='combined_mappings'):
		modl = self.list_table_info(table)
		#varlist = []
		props = modl.schema['data_model']['properties']
		vLookUp = {}
		for p, v in props.items():
			vLookUp[v['$id']] = p
		if self.debug:
			print(vLookUp)
		#Find the mappings
		mcl = MappingLibraryClient()
		varList = mcl.getMappingsForVars(list(vLookUp.keys()), mapset=mapset)
		if self.debug:
			print(varList)
		# Add column names to the mappings
		vi = 0
		for var in varList:
			varList[vi]['fromCol'] = vLookUp[var['from']]
			vi += 1
		return varList
	
	def runOneTableQuery(self, column_list, table, limit, passport=None):
		col_string = ", ".join(column_list)

		query = "select {columns} from {table} limit {results}".format(columns=col_string,
																table=table, results=limit)
		res = self.run_query(query, return_type='dataframe', passport=passport)
		return res

	def getDataFrameFromTable(self, table, column_list=[], limit=1000, passport=None):
		if isinstance(column_list, list):
			if len(column_list) == 0:
				column_list = '*'
			else:
				column_list.join(',')
		query = f"select {column_list} from {table} limit {limit}"
		print (query)
		res = self.run_query(query, return_type='dataframe', passport=passport)
		if res.shape[0] >= limit:
			print(f'The number of rows was limited to {limit}. Try setting limit=your_value if you need more data')
		return res
				
	def __add_passport(self, body, passport=None):
		'''Adds Passport/TST to body/header respectively.
		This is an interim implementation that determines if we have been given a tst or a passport 
		based on the specifics of the NCBI implementation'''
		if passport == None:
			passport = self.passport
		
		req_headers = self.headers
		if passport != None:
			full_key_path = os.path.expanduser(passport)
			file_content = ""
			if self.debug: print(f"passport path {full_key_path}")
			try:
				with open(full_key_path) as f:
					file_content = f.read()
				if self.debug: print(f"content of passport file {file_content}")
			except:
				print("Could not find passport file")
			if file_content.startswith("ncbi_tstv1"):
				req_headers["GA4GH-Search-Authorization"] = f"ga4gh-passport={file_content}"				
			elif file_content.startswith("ncbi_ppv1"):
				body['passport'] = file_content
			else:
				print("Unrecognized passport/visa content")
				
		return req_headers, body
				
	def run_query(self, query, return_type=None, progessIndicator=None, passport=None):

		if return_type == None:
			return_type = self.return_type	
			
		url = self.hostURL + "/search"
		query = query.replace("\n", " ").replace("\t", " ")
		query = query.strip()
		#query2 = "{\"query\":\"%s\", \"parameters\":[]}" % query
		body = {"query":query, "parameters":[]}
		if self.debug:
			print("Query: {}".format(body))
			

		req_headers , body = self.__add_passport(body, passport=passport)
		if self.debug:
			print(f"Headers: {req_headers}")
		response = requests.request("POST", url,
			headers=self.headers, json = body)
		return self.__handle_response(response, return_type, progessIndicator)
	
		
	def get_data(self, table, return_type=None, progessIndicator=None, passport=None, show_urls=True):

		if return_type == None:
			return_type = self.return_type

		url = self.hostURL + f"/table/{table}/data"
		if show_urls:
			print(url)
		req_headers , body = self.__add_passport({}, passport=passport)
		response = requests.request("GET", url, headers=req_headers)
		return self.__handle_response(response, return_type, progessIndicator)
		
			
	def __handle_response(self, response, return_type, progessIndicator):
		if self.debug: print("In handle response")
		pageCount = 0
		resultRows = []
		column_list = []
		if not progessIndicator:
			print ("Retrieving the query")
		done = False
		while not done :
			pageCount += 1
			if progessIndicator:
				progessIndicator.value += 1
			else:
				print ("____Page{}_______________".format(pageCount))

			if self.debug: print(response.content)
			result = (response.json())
			if self.debug:
				print(json.dumps(result, indent=3))
			if 'pagination' in result and 'next_page_url' in result['pagination']:
				next_url = result['pagination']['next_page_url']
			else:
				next_url = None
				done = True
			if "errors" in result:
				for e in result['errors']:
					print(f"Error status:{e['title']}")
					print(f"{e['title']}")
					print(f"Details: {e['details']}")
			if return_type == 'json':
				resultRows += result['data']
			else:
				for r in result['data']:
					resultRows.append([*r.values()])
				
			if 'data_model' in result:
				if self.debug: print('found data model')
				column_list = result['data_model']['properties'].keys()
			
			if len(resultRows) >= self.row_limit:
				print(f"Client row limit of {self.row_limit} was reached. Reset limit with care!")
				done = True	
				
			# Get the next page
			if not done :
				response = requests.request("GET", next_url)

		if progessIndicator:
			progessIndicator.value = progessIndicator.max
		
		if return_type == 'dataframe':
			df = pd.DataFrame(resultRows, columns=column_list, index=None)
			return df
		else:
			return resultRows

	def run_param_query(self, query, return_type=None, progessIndicator=None, passport=None):

		if return_type == None:
			return_type = self.return_type
			
		url = self.hostURL + "/search"
		query_text = query['query'].replace("\n", " ").replace("\t", " ")
		query_text = query_text.strip()
		#query2 = "{\"query\":\"%s\"}" % query
		query2 = {"query":query_text, "parameters":query['parameters']}
		if self.debug:
			print("Query: {}".format(query2))
		#query2 = query

		#response = requests.request("POST", url,
		#	headers=self.headers, data = query2)
		req_headers , body = self.__add_passport(query2, passport=passport)
		response = requests.post(url, json = body, headers=req_headers)
		return self.__handle_response(response, return_type, progessIndicator)



	def query2Frame(self, query, passport=None):
		return self.run_query(query, return_type='dataframe', passport=passport)
	
class SearchSchema():
	''' A table schema '''	
	def __init__(self, table_info ):
		self.schema = table_info
	
	def getCol(self, colName):
		if colName not in self.schema['data_model']['properties']:
			print('No column named {}'.format(colName))
		print(json.dumps(self.schema['data_model']['properties'][colName], indent=3))
		
	def getcaDSRDefinition(self, ref):
		
		from urllib.request import urlopen
		from xml.etree.ElementTree import parse
		metaresolverURL = 'http://identifiers.org/{}'.format(ref)
		var_url = urlopen(metaresolverURL)
		xmldoc = parse(var_url)

		root = xmldoc.getroot()
		requiredFields=['publicID','version','dateCreated','dateModified','longName',
                'preferredDefinition','preferredName', 'registrationStatus']

		requiredLinks=['valueDomain','dataElementConcept']
		caDSRrep = {}
		for item in root.findall('./queryResponse/class/field'):
			fName = item.get('name')
			if fName in requiredFields:
				caDSRrep[fName]=item.text
			if fName in requiredLinks:
				caDSRrep[fName]=item.get('{http://www.w3.org/1999/xlink}href')

		return caDSRrep


def usage():
	print (sys.argv[0] +' -s service -l listTables -c listCatalog -t tableInfo -r registeredServices')

def main(argv):

	try:
		opts, args = getopt.getopt(argv, "hls:c:t:ra", ["help", "listTables", "service", "tableInfo", "registeredServices","catalogs"])
	except getopt.GetoptError as err:
		print(err)
		usage()
		sys.exit(2)
	searchClient = None
	for opt, arg in opts:
	    if opt == '-s':
	    	searchClient = DataConnectClient(arg, debug=True)
	if searchClient == None:
		print("-s service must be provided")
		usage()
		sys.exit()
	for opt, arg in opts:
	    if opt in ("-h", "--help"):
	        usage()
	        sys.exit()
	    elif opt in ("-l", "--listTables"):
	        searchClient.list_tables(verbose=True)
	    elif opt in ("-c", "--listCatalog"):
	        searchClient.list_catalog(arg)
	    elif opt in ("-t", "--table"):
	        ti = searchClient.list_table_info(arg, verbose=True)
	    elif opt in ("-a", "--catalogs"):
	        searchClient.list_catalogs()
	    elif opt in ("-r", "--registeredServices"):
	        DataConnectClient.getRegisteredSearchServices()


if __name__ == "__main__":
    main(sys.argv[1:])

