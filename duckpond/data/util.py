def relative(uri):
   afterScheme = uri[uri.index('//') + 2:]
   return afterScheme[afterScheme.index('/'):]
