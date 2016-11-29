import shutil, os

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
