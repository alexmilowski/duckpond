import io

class SPARQL:

   def __init__(self):
      self.statement = io.StringIO()

   def start(self,prefixes):
      for key in prefixes:
         self.statement.write('prefix {}: <{}>\n'.format(key,prefixes[key]))
      return self

   def select(self,names):
      self.statement.write('select ')
      for name in names:
         if name[0]=='(':
            self.statement.write(name)
         else:
            self.statement.write('?')
            self.statement.write(name)
         self.statement.write(' ')
      self.statement.write('\n')
      return self

   def fromGraphs(self,graphs):
      for graph in graphs:
         self.statement.write('from <{0}>\n'.format(graph))
      return self

   def fromNameGraphs(self,graphs):
      for graph in graphs:
         self.statement.write('from named <{0}>\n'.format(graph))
      return self

   def withGraph(self,graph):
      self.statement.write("with <{0}>\n".format(graph))
      return self

   def where(self,*expressions):
      self.statement.write('where {')
      for expression in expressions:
         self.statement.write(str(expression))
         self.statement.write('\n')
      self.statement.write('}\n')
      return self

   def insert(self,*expressions):
      self.statement.write('insert {')
      for expression in expressions:
         self.statement.write(str(expression))
         self.statement.write('\n')
      self.statement.write('}\n')
      return self

   def delete(self,*expressions):
      self.statement.write('delete {')
      for expression in expressions:
         self.statement.write(str(expression))
         self.statement.write('\n')
      self.statement.write('}\n')
      return self

   def anyGraph(self,*expressions):
      self.statement.write('graph ?g {')
      for expression in expressions:
         self.statement.write(str(expression))
         self.statement.write('\n')
      self.statement.write('}\n')
      return self

   def forGraph(self,graph,*expressions):
      self.statement.write('graph <{0}> {'.format(graph))
      for expression in expressions:
         self.statement.write(str(expression))
         self.statement.write('\n')
      self.statement.write('}\n')
      return self

   def newline(self):
      self.statement.write('\n')
      return self;

   def orderBy(self,*expressions):
      self.statement.write('order by ')
      first = True
      for expression in expressions:
         if not first:
            self.statement.write(',')
         self.statement.write(str(expression))
      self.statement.write('\n')
      return self

   def groupBy(self,expression):
      self.statement.write('group by ')
      self.statement.write(expression)
      self.statement.write('\n')
      return self

   def __str__(self):
      return self.statement.getvalue()
