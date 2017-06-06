from flask import Flask
import logging, logging.config, os

# TODO: total hack to get the configuration of the templates folder
f = os.environ.get('WEB_CONF')
template_folder = 'templates'
if f is not None:
   d = {}
   with open(f) as config_file:
       exec(compile(config_file.read(), f, 'exec'), d)

   template_folder = d.get('TEMPLATE_FOLDER')
   if template_folder is None:
      template_folder = 'templates'
# END

app = Flask(__name__,template_folder=template_folder)
app.config.from_envvar('WEB_CONF')
logLevel = app.config.get('LOGLEVEL')
if logLevel is not None:
   logging.basicConfig(level=logLevel)

logConfig = app.config.get("LOGCONFIG")
if logConfig is not None:
   logging.config.dictConfig(logConfig)
