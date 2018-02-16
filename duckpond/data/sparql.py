import io

def write_var(out,name):
   if type(name)==str:
      out.write('?')
      out.write(name)
   else:
      out.write(str(name))

class var:
   def __init__(self,value):
      self.name = value
   def __str__(self):
      return '?'+str(self.name)

class inline_expr:
   def __init__(self,value):
      self.expr = value
   def __str__(self):
      return '(' + str(self.expr) + ')'

class uri:
   def __init__(self,value):
      self.expr = value
   def __str__(self):
      return '<' + str(self.expr) + '>'


class in_expr:
   def __init__(self,ref_expr,*values):
      self.ref_expr = ref_expr
      self.values = values
   def __str__(self):
      return str(self.ref_expr) + ' IN(' + ','.join(map(lambda v:str(uri(v)),self.values)) + ')'

class tuple_expr:
   def __init__(self,*spo):
      self.statements = []
      if len(spo)==3:
         self.statements.append((spo[0],spo[1],spo[2]))

   def triple(self,s,p,o):
      self.statements.append((s,p,o))
      return self

   def predicate(self,p,o):
      self.statements.append((p,o))
      return self

   def optional(self,*expressions):
      self.statements.append(('optional',expressions))
      return self

   def filter(self,*expressions,conjunction='and'):
      self.statements.append(('filter',(expressions,conjunction)))
      return self

   def __str__(self):
      statement = io.StringIO()
      for index,item in enumerate(self.statements):
         if index>0:
            statement.write(' ')
         if (len(item)==3):
            write_var(statement,item[0])
            statement.write(' ')
            write_var(statement,item[1])
            statement.write(' ')
            write_var(statement,item[2])
         elif type(item[1])==list and item[0]=='optional':
            statement.write(' optional {')
            for index,expression in enumerate(item[1]):
               if index>0:
                  statement.write(' ')
               statement.write(str(expression))
            statement.write('}')
         elif type(item[1])==tuple and item[0]=='filter':
            statement.write(' filter (')
            for index,expression in enumerate(item[1][0]):
               if index>0:
                  statement.write(' ')
                  statement.write(item[1][1])
                  statement.write(' ')
               statement.write(str(expression))
            statement.write(')')
      return statement.getvalue()

class graph_expr:
   def __init__(self,graph,*expressions):
      self.expr = (graph,expressions)

   def __str__(self):
      statement = io.StringIO()

      statement.write('graph ')
      statement.write(str(uri(self.expr[0]) if type(self.expr[0])==str else self.expr[0]))
      statement.write(' {')
      for index,expr in enumerate(self.expr[1]):
         statement.write(str(expr))
         statement.write('\n')
      statement.write('}')
      return statement.getvalue()

class SPARQL:

   def __init__(self):
      self.statement = io.StringIO()

   def start(self,prefixes):
      for key in prefixes:
         self.statement.write('prefix {}: {}\n'.format(key,uri(prefixes[key])))
      return self

   def construct(self,names):
      self.statement.write('construct {')
      for name in names:
         write_var(self.statement,name)
         self.statement.write(' ')
      self.statement.write('}\n')
      return self

   def select(self,names):
      self.statement.write('select ')
      for name in names:
         write_var(self.statement,name)
         self.statement.write(' ')
      self.statement.write('\n')
      return self

   def fromGraphs(self,graphs):
      for graph in graphs:
         self.statement.write('from {0}\n'.format(uri(graph)))
      return self

   def fromNameGraphs(self,graphs):
      for graph in graphs:
         self.statement.write('from named {0}\n'.format(uri(graph)))
      return self

   def withGraph(self,graph):
      self.statement.write("with {0}\n".format(uri(graph)))
      return self

   def where(self,*expressions):
      self.statement.write('where {')
      for expression in expressions:
         self.statement.write(str(expression))
         self.statement.write('\n')
      self.statement.write('}\n')
      return self

   def group(self,*expressions):
      self.statement.write('{')
      for expression in expressions:
         self.statement.write(str(expression))
         self.statement.write('\n')
      self.statement.write('}\n')
      return self

   def insert(self,*expressions):
      self.statement.write('insert data {')
      for expression in expressions:
         self.statement.write(str(expression))
         self.statement.write('\n')
      self.statement.write('}\n')
      return self

   def delete(self,*expressions):
      self.statement.write('delete data {')
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
      self.statement.write('graph {0} {'.format(uri(graph)))
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
