from elasticsearch import Elasticsearch
import json, requests

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
# es.index(index='sw', doc_type='people', id=1, body={
# 	"name": "Luke Skywalker",
# 	"height": "172",
# 	"mass": "77",
# 	"hair_color": "blond",
# 	"birth_year": "19BBY",
# 	"gender": "male",
# })

r = requests.get('http://localhost:9200')
i = 18

# while r.status_code == 200:
#      r = requests.get('http://swapi.co/api/people/'+ str(i))
#      es.index(index='sw', doc_type='people', id=i, body=json.loads(r.content.decode('utf8')))
#      i=i+1

# print(i)

#out = es.index(index='test-index', doc_type='test', id=1, body={'test': 'test'})
#print(out)

get = es.get(index='sw', doc_type='people', id=65)
print(get)