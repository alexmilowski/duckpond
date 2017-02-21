import shutil, os
from io import BufferedReader
from tempfile import TemporaryFile
from urllib.parse import urlparse
import boto3, botocore

class FileResourceService:
   def __init__(self,base=None,directory='.',cleanup=True):
      self.base = base
      self.directory = directory
      self.separator = '/' if self.directory[-1]!='/' else ''
      self.cleanup = True

   def resolveLocation(self,url):
      path = None
      if url.find(self.base)==0:
         path = url[len(self.base):]
      else:
         colon = url.find(':')
         if url[colon:colon+3]=='://':
            slash = url.find('/',colon+3)
            path = url[slash+1:]
         else:
            raise ValueError('The URL is not generic: '+url)
      return self.directory + self.separator + path

   def getResource(self,url):
      location = self.resolveLocation(url)
      if os.path.isfile(location):
         return (200,open(location,'rb'),os.path.getsize(location))
      else:
         return (404,None,None)

   def putResource(self,url,stream,content_type=None):
      location = self.resolveLocation(url)
      print(location)
      last = location.rfind('/')
      dirpath = location[0:last]
      os.makedirs(dirpath,exist_ok=True)
      exists = os.path.isfile(location)
      with open(location,'wb') as fdest:
         shutil.copyfileobj(stream,fdest)
      return 204 if exists else 201

   def deleteResource(self,url):
      location = self.resolveLocation(url)
      if not os.path.isfile(location):
         return 404
      os.remove(location)

      if self.cleanup:
         # Try to remove empty content directories
         try:
            last = location.rfind('/')
            dirpath = location[0:last]
            os.rmdir(dirpath)
         except OSError:
            # An exception means the directory is not empty and that's okay!
            pass
      return 200

class S3ResourceService:
   def __init__(self,access_key_id,secret_access_key,bucket,bucket_domains={},tmpdir=None):
      self.s3 = boto3.client('s3',aws_access_key_id=access_key_id,aws_secret_access_key=secret_access_key)
      self.bucket_name = bucket
      self.bucket_domains = bucket_domains
      self.tmpdir = tmpdir
      self.readSize = 32*1024

   def parseLocation(self,url):
      spec = urlparse(url)
      colon = spec.netloc.find(':')
      return (spec.netloc[0:colon] if colon>0 else spec.netloc,spec.path[1:])

   def getBucket(self,domain):
      bucket = self.bucket_domains.get(domain)
      return bucket if bucket is not None else self.bucket_name

   def getResource(self,url):
      domain,path = self.parseLocation(url)
      try:
         response = self.s3.get_object(Bucket=self.getBucket(domain),Key=path)
         def readBody():
            while True:
               data = response['Body'].read(self.readSize)
               if len(data)>0:
                  yield data
               else:
                  response['Body'].close()
                  break
         return (200,readBody(),response['ContentLength'])
      except botocore.exceptions.ClientError as e:
         if e.response['Error']['Code'] == "404":
            return (404,None,None)
         else:
            raise e

   def putResource(self,url,stream,content_type=None):
      domain,path = self.parseLocation(url)
      creating = False
      try:
         self.s3.head_object(Bucket=self.getBucket(domain),Key=path)
      except botocore.exceptions.ClientError as e:
         if e.response['Error']['Code'] == "404":
            creating = True
         else:
            raise e
      with TemporaryFile(dir=self.tmpdir) as cached:
         shutil.copyfileobj(stream,cached)
         cached.seek(0)
         self.s3.put_object(Bucket=self.getBucket(domain),Body=cached,Key=path,ContentType=content_type)
      return 201 if creating else 204

   def deleteResource(self,url):
      domain,path = self.parseLocation(url)
      try:
         self.s3.delete_object(Bucket=self.getBucket(domain),Key=path)
      except botocore.exceptions.ClientError as e:
         if e.response['Error']['Code'] != "404":
            raise e
      return 204
