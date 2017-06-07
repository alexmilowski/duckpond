from flask import Blueprint, request, render_template, abort, send_file, redirect, current_app, send_from_directory, Response, stream_with_context
import logging,collections

from duckpond.data import Pond,uripath
from duckpond.data.pond import Facet

blog = Blueprint('duckpond_blog',__name__,template_folder='templates')

logger = logging.getLogger('webapp')

def getPond(config):
   user = config.get('USER')
   password = config.get('PASSWORD')

   data = Pond(config['SPARQL_SERVICE'],cache=config['CACHE'],facets=[ Facet('resource','schema:isBasedOnUrl','xsd:anyURI')])
   data.authenticate(user if user is not None else 'anonymous', password if password is not None else '')
   return data

def getJournalCriteria(config):
   journalGenre = config.get('JOURNAL_GENRE')
   if journalGenre is None:
      journalGenre = 'blog'
   return {'schema:genre' : journalGenre}


def getTemplateOptions(config):
   options = config.get('TEMPLATE_OPTIONS')
   return options if options is not None else {
      'title' : 'My Journal'
   }

def entry(e):
   if e is None:
      return None
   else:
      return {'uri':uripath(e[0]),'subject':e[0],'title':e[1],'summary':e[2],'date':e[3],'time':e[4],'basedOnUrl':e[5]}

def siteURL(config,request):
   u = current_app.config.get('SITE_URL')
   return u if u is not None else request.url_root[0:-1]

def renderEntry(data,basedOnUrl,entry=None,preceding=None,following=None,base=None,path=None):
   try:
      logger.debug(basedOnUrl)
      content = data.getResourceText(basedOnUrl)
      topics = [(key,value) for key,value in data.getCategoryCount().items()]
      sortedTopics = sorted(topics,key=lambda x : str.lower(x[0]))
      return render_template('base.html', siteURL=siteURL(current_app.config,request), path=path, options=getTemplateOptions(current_app.config), entry=entry,entryContent=content,preceding=preceding,following=following,keywords=sorted(data.getEntityCategories(entry['subject']),key=str.lower),topics=sortedTopics,base=base)
   except FileNotFoundError:
      abort(404)

def renderKeyword(data,keyword,related,entries):
   try:
      topics = [(key,value) for key,value in data.getCategoryCount().items()]
      sortedTopics = sorted(topics,key=lambda x : str.lower(x[0]))
      return render_template('keyword.html', entry=None, siteURL=siteURL(current_app.config,request), path=request.path, options=getTemplateOptions(current_app.config), keyword=keyword,related=sorted(related,key=str.lower),entries=entries,topics=sortedTopics)
   except FileNotFoundError:
      abort(404)

@blog.route('/')
def index():

   data = getPond(current_app.config)

   entryInfo = data.currentEntity(criteria=getJournalCriteria(current_app.config))
   if entryInfo is None:
      abort(404)

   subject,_,_,date,time,*_ = entryInfo
   dateTime = date + "T" + time
   resource = data.getEntityResource(subject)
   following = data.relatedEntityByOrder(dateTime,previous=True)
   path = "/journal/entry/{}T{}/".format(date,time)
   return renderEntry(data,resource[0],entry=entry(entryInfo),following=entry(following) if following is not None and len(following)>0 else None,base=path,path=path)

@blog.route('/journal/entry/<date>T<time>/')
def entryByTime(date,time):

   data = getPond(current_app.config)

   dateTime = date + "T" + time
   entryInfo = data.entityByOrder(dateTime)
   if entryInfo is None:
      abort(404)

   following = data.relatedEntityByOrder(dateTime,previous=True)
   preceding = data.relatedEntityByOrder(dateTime,previous=False)
   resource = data.getEntityResource(entryInfo[0])

   return renderEntry(data,resource[0],entry=entry(entryInfo),following=entry(following),preceding=entry(preceding),path=request.path)

@blog.route('/journal/entry/<date>T<time>/<path:path>')
def entryMedia(date,time,path):

   data = getPond(current_app.config)

   uri = app.config['CACHE']['base'] + date + '/' + path
   resource = data.getResource(uri)
   if resource[0] == Pond.ResourceType.uri:
      return redirect(resource[1], code=resource[2])
   elif resource[0] == Pond.ResourceType.stream:
      return Response(stream_with_context(resource[1]), content_type = resource[2])
   else:
      return send_file(resource[1])

@blog.route('/rel/keyword/<keyword>')
def relKeyword(keyword):

   data = getPond(current_app.config)

   entries = data.getEntitiesByCategory(keyword)
   allKeywords = []
   entries = list(map(lambda e:entry(e),entries))
   for relatedEntry in entries:
      relatedEntry['keywords'] = sorted(data.getEntityCategories(relatedEntry['subject']))
      allKeywords.extend(relatedEntry['keywords'])
   return renderKeyword(data,keyword,set(allKeywords),entries)

@blog.errorhandler(404)
def page_not_found(error):
   return render_template('error.html', siteURL=siteURL if siteURL is not None else request.url_root[0:-1], path=request.path, options=templateOptions, entry=None, error="I'm sorry.  I can't find that page.")


docs = Blueprint('duckpond_blog_docs',__name__)

@docs.route('/docs/<path:path>')
def send_doc(path):
   siteURL = current_app.config.get('SITE_URL')

   templateOptions = current_app.config.get('TEMPLATE_OPTIONS')
   if templateOptions is None:
      templateOptions = {
         'title' : 'My Journal'
      }

   location = current_app.config.get('DOCS')
   if location is None:
      abort(404)

   if location[0:4]=='http':
      url = location + path
      req = requests.get(url, stream = True,headers={'Connection' : 'close'})
      if req.headers['Content-Type'][0:9]=='text/html':
         return render_template('content.html', siteURL=siteURL if siteURL is not None else request.url_root[0:-1], options=templateOptions, html=req.text, entry=None)
      else:
         return Response(stream_with_context(req.iter_content()), headers = dict(req.headers))

   else:

      dir = os.path.abspath(location)
      if path.endswith('.html'):

         glob = io.StringIO()
         try:
            with open(os.path.join(dir,path), mode='r', encoding='utf-8') as doc:
               peeked = doc.readline()
               if peeked.startswith('<!DOCTYPE'):
                  return send_from_directory(dir, path)
               glob.write(peeked)
               for line in doc:
                  glob.write(line)

               return render_template('content.html', siteURL=siteURL if siteURL is not None else request.url_root[0:-1], options=templateOptions, html=glob.getvalue(), entry=None)
         except FileNotFoundError:
            abort(404)

      return send_from_directory(dir, path)

assets = Blueprint('duckpond_blog_assets',__name__)
@assets.route('/assets/<path:path>')
def send_asset(path):
   dir = current_app.config.get('ASSETS')
   if dir is None:
      dir = __file__[:__file__.rfind('/')] + '/assets/'
   return send_from_directory(dir, path)
