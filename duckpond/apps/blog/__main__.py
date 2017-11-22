from flask import Flask
import logging, logging.config, os, sys
import importlib.util

app = Flask(__name__)

from duckpond.apps.blog.views import blog,assets,docs
app.register_blueprint(blog)
app.register_blueprint(assets)
app.register_blueprint(docs)

if len(sys.argv)>1:
   path = sys.argv[1].split('.')
   package = '.'.join(path[0:len(path)-1])
   spec = importlib.util.find_spec(package)
   if spec is None:
      pyfile = os.getcwd()+'/'+package+'.py'
      spec = importlib.util.spec_from_file_location(package,pyfile)
      if spec is None:
         raise ValueError('Cannot find module '+package)
   module = importlib.util.module_from_spec(spec)
   spec.loader.exec_module(module)
   obj = getattr(module,path[-1])()
   app.config.from_object(obj)
elif os.environ.get('WEB_CONF') is not None:
   app.config.from_envvar('WEB_CONF')

logLevel = app.config.get('LOGLEVEL')
if logLevel is not None:
   logging.basicConfig(level=logLevel)

logConfig = app.config.get("LOGCONFIG")
if logConfig is not None:
   logging.config.dictConfig(logConfig)

if __name__ == '__main__':
    app.run()
