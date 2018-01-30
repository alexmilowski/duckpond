from flask import Flask, g
import logging, logging.config, os
import argparse
import json


from duckpond.apps.jsonld.service import data

app = Flask(__name__)

app.register_blueprint(data,url_prefix='/data')


if __name__ == '__main__':
   parser = argparse.ArgumentParser(prog='duckpond.apps.jsonld',description='JSONLD/SPARQL connection service')
   parser.add_argument(
      '--service',
      nargs='?',
      default='http://localhost:10035/repositories/test',
      help="The endpoint service")
   parser.add_argument(
      '--auth',
      nargs='?',
      help="The authentication (colon separated)")
   parser.add_argument(
      '--context',
      nargs='?',
      help="The JSON-LD context to use")
   parser.add_argument(
        '--debug',
        action='store_true',
        default=False,
        help="Enable debugging")
   args = parser.parse_args()

   f = os.environ.get('WEB_CONF')
   if f is not None:
      app.config.from_envvar('WEB_CONF')

   if args.service is not None:
      app.config['SPARQL_ENDPOINT'] = {
         'url' : args.service
      }

   if args.context is not None:
      with open(args.context,'r') as data:
         app.config['LD_CONTEXT'] = json.load(data)
   else:
      if app.config.get('LD_CONTEXT') is None:
         app.config['LD_CONTEXT'] = {}

   if args.auth is not None:
      auth = args.auth.split(':')
      app.config['SPARQL_ENDPOINT']['username'] = auth[0]
      if len(auth)>1:
         app.config['SPARQL_ENDPOINT']['password'] = auth[1]

   app.config['DEBUG'] = args.debug

   logLevel = app.config.get('LOGLEVEL')
   if logLevel is not None:
      logging.basicConfig(level=logLevel)

   logConfig = app.config.get("LOGCONFIG")
   if logConfig is not None:
      logging.config.dictConfig(logConfig)

   app.run()
