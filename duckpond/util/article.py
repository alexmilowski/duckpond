import CommonMark,re,argparse

import sys,io,os,shutil

from html import escape

META_RE = re.compile(r'^[ ]{0,3}(?P<key>[A-Za-z0-9_-]+):\s*(?P<value>.*)')
META_MORE_RE = re.compile(r'^[ ]{4,}(?P<value>.*)')

class ArticleConverter:
   def __init__(self,weburi,entryuri):
      self.weburi = weburi
      self.entryuri = [ entryuri ]
      self.vocab = 'http://schema.org'
      self.typeof = 'BlogPosting'

   def enter(self,suffix):
      self.entryuri.append(self.entryuri[-1] + suffix)

   def leave(self):
      return self.entryuri.pop()
      
   def toArticle(self,base,md,html,triples):
      glob = io.StringIO()
      metadata = {}
      hasMetadata = True
      hasTitle = False
      line = md.readline()
      while hasMetadata:
         m = META_RE.match(line)
         if (not(m)):
            glob.write(line)
            if not hasTitle and line[0:2]=='# ':
               hasTitle = True
            glob.write('\n')
            hasMetadata = False
         else:
            key = m.group('key').lower().strip()
            value = m.group('value').strip()
            try:
               metadata[key].append(value)
            except KeyError:
               metadata[key] = [value]
            continued = True
            while continued:
               line = md.readline()
               more = META_MORE_RE.match(line)
               if (not(more)):
                  continued = False
               else:
                  metadata[key].append(more.group('value').strip())

      for line in md:
         if not hasTitle and line[0:2]=='# ':
            hasTitle = True
         glob.write(line)

      self.toHTML(glob.getvalue(),metadata,html,generateTitle=not hasTitle)
      self.toTurtle(base,metadata,triples)

   def toHTML(self,md,metadata,html,generateTitle=False):

      uri = self.weburi + metadata['published'][0]

      print('<article xmlns="http://www.w3.org/1999/xhtml" vocab="{}" typeof="{}" resource="{}">'.format(self.vocab,self.typeof,uri),file=html)
   
      print('<script type="application/json+ld">',file=html)
      print('{\n"@context" : "http://schema.org/",',file=html)
      print('"@id" : "{}",'.format(uri),file=html)
      print('"headline" : "{}",'.format(metadata['title'][0]),file=html)
      print('"datePublished" : "{}",'.format(metadata['published'][0]),file=html)
      print('"dateModified" : "{}",'.format(metadata['updated'][0]),file=html)
      if ("keywords" in metadata):
         print('"keywords" : [{}],'.format(','.join(['"' + m + '"' for m in metadata['keywords']])),file=html)
      html.write('"author" : [ ')
      for index,author in enumerate(metadata['author']):
         if (index>0):
            html.write(', ')
         html.write('{{ "@type" : "Person", "name" : "{}" }}'.format(author))
      html.write(']\n')
      print('}',file=html)
      print('</script>',file=html)

      if generateTitle:
         print("<h1>{}</h1>".format(escape(metadata['title'][0],quote=False)),file=html)

      print(CommonMark.commonmark(md),file=html)

      print('</article>',file=html)

   def toTurtle(self,base,metadata,triples):
      
      uri = self.weburi + metadata['published'][0]
      basedOn = self.entryuri[-1] + base + '.html'
      
      print('@base <{}> .'.format(uri),file=triples)
      print('@prefix schema: <http://schema.org/> .',file=triples)
      print('<>',file=triples)
      print('   a schema:BlogPosting ;',file=triples)
      print('   schema:headline "{}" ;'.format(metadata['title'][0]),file=triples)
      print('   schema:datePublished "{}" ;'.format(metadata['published'][0]),file=triples)
      print('   schema:dateModified "{}" ;'.format(metadata['updated'][0]),file=triples)
      print('   schema:isBasedOnUrl <{}> ;'.format(basedOn),file=triples)
      if ("keywords" in metadata):
         print('   schema:keywords {} ;'.format(','.join(['"' + m + '"' for m in metadata['keywords']])),file=triples)
      triples.write('   schema:author ')
      for index,author in enumerate(metadata['author']):
         if (index>0):
            triples.write(', ')
         triples.write('[ a schema:Person; schema:name "{}" ]'.format(author))
      triples.write(' .\n')

if __name__ == "__main__":
   argparser = argparse.ArgumentParser(prog=sys.modules[__name__].__spec__.name,description='Article HTML and Turtle Generator')
   argparser.add_argument('-f',action='store_true',help='Forces all the files to be regenerated.',dest='force')
   argparser.add_argument('-o',nargs='?',help='The output directory',dest='outdir')
   argparser.add_argument('-w',nargs='?',help='The web uri',dest='weburi',default='http://www.milowski.com/journal/entry/')
   argparser.add_argument('-e',nargs='?',help='The entry uri directory',dest='entryuri',default='http://alexmilowski.github.io/milowski-journal/')
   argparser.add_argument('--immediate',action='store_true',help='Only process the immediate director (no subdirectories)',dest='immediate')
   argparser.add_argument('dir',nargs=1,help='The directory to process.')
   args = argparser.parse_args()
   inDir = args.dir[0]
   outDir = args.outdir if (args.outdir!=None) else inDir
   dirs = [inDir] if args.immediate else [d for d in os.listdir(inDir) if not(d[0]=='.') and os.path.isdir(inDir + '/' + d)]

   converter = ArticleConverter(args.weburi,args.entryuri)

   for dir in dirs:
   
      sourceDir = inDir + '/' + dir if inDir!='.' else dir
      targetDir = outDir + '/' + dir if outDir!='.' else dir
   
      if (not(os.path.exists(targetDir))):
         os.makedirs(targetDir)

      converter.enter(dir+'/')
   
      files = [f for f in os.listdir(sourceDir) if f.endswith('.md') and os.path.isfile(sourceDir + '/' + f)]
   
      for file in files:
      
         targetFile = sourceDir + '/' + file
         base = file.rsplit('.md',1)[0]
         htmlFile = targetDir + '/' + base + ".html"
         turtleFile = targetDir + '/' + base + ".ttl"
      
         updatedNeeded = args.force or not(os.path.exists(htmlFile)) or not(os.path.exists(turtleFile))
         if (not(updatedNeeded)):
            btime = os.path.getmtime(targetFile)
            updatedNeeded = btime > os.path.getmtime(htmlFile) or btime > os.path.getmtime(turtleFile)
         
         if (not(updatedNeeded)):
            continue
      
         print(file + " → " + htmlFile + ", " + turtleFile)
      
         md = open(targetFile,"r")
         html = open(htmlFile,"w")
         turtle = open(turtleFile,"w")
      
         converter.toArticle(base,md,html,turtle)
      
         md.close()
         html.close()
         turtle.close()

      work = [f for f in os.listdir(sourceDir) if (not f.endswith('.md'))]
      for file in work:
         sourceFile = sourceDir + '/' + file
         targetFile = targetDir + '/' + file
         if os.path.isfile(sourceFile):
            copyNeeded = args.force or not(os.path.exists(targetFile)) or os.path.getmtime(sourceFile) > os.path.getmtime(targetFile)
         
            if copyNeeded:
               print(file + " → " + targetFile)
               shutil.copyfile(sourceFile,targetFile)
         elif os.path.isdir(sourceFile):
            if os.path.exists(targetFile):
               print('sync tree ' + sourceFile)
               work += [sourceFile + '/' + f for f in os.listdir(sourceFile)]
            else:
               print("copy tree " + sourceFile + " → " + targetFile)
               shutil.copytree(sourceFile,targetFile)
   
      converter.leave()

