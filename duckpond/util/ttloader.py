
import sys,io,os,argparse

import json,requests,urllib

argparser = argparse.ArgumentParser(description='Triple loader')
argparser.add_argument('dir',nargs=1,help='The directory to process.')
argparser.add_argument('uri',nargs=1,help='The repository URI.')
argparser.add_argument('graph',nargs='?',help='The graph name')
argparser.add_argument('-u',help='The user',dest='user')
argparser.add_argument('-p',help='The password',dest='password')
args = argparser.parse_args()
inDir = args.dir[0]
repository = args.uri[0]

auth = requests.auth.HTTPBasicAuth(args.user, args.password)

def loadTriples(targetFile):

   print(targetFile)
   f = open(targetFile,"r",encoding='utf-8')
   data = f.read()
   f.close()

   uri = repository
   if args.graph is not None and len(args.graph)>0:
      uri = uri + "?context=" + urllib.parse.quote('<'+args.graph+'>')
   req = requests.post(uri,data=data.encode('utf-8'),headers={'content-type':'text/turtle; charset=utf-8'},auth=auth)
   if (req.status_code<200 or req.status_code>=300):
      raise IOError('Cannot post data to uri <{}>, status={}'.format(uri,req.status_code))

for file in [f for f in os.listdir(inDir) if f.endswith('.ttl') and os.path.isfile(inDir + '/' + f)]:
   targetFile = inDir + '/' + file

   loadTriples(targetFile)

dirs = [d for d in os.listdir(inDir) if not(d[0]=='.') and os.path.isdir(inDir + '/' + d)]

for dir in dirs:
   sourceDir = inDir + '/' + dir

   files = [f for f in os.listdir(sourceDir) if f.endswith('.ttl') and os.path.isfile(sourceDir + '/' + f)]
   for file in files:
      targetFile = sourceDir + '/' + file

      loadTriples(targetFile)
