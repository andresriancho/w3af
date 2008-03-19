<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:xi="http://www.w3.org/2003/XInclude"
                xmlns:xalanredirect="org.apache.xalan.xslt.extensions.Redirect"
                exclude-result-prefixes="xi xalanredirect"
                version="1.0">
  
  <xsl:output method="html"
              omit-xml-declaration="yes"
              indent="yes"/>
  
  <xsl:template match="/">
    <div id="navigation">
      <ul>&#10;
        <li><a id="nav-index" href="index.html">About</a></li>&#10;
        <xsl:for-each select="//xi:include">
          <li><xsl:apply-templates select="document(@href)/section"/></li>&#10;
        </xsl:for-each>
      </ul>&#10;
    </div>
  </xsl:template>
  
  <xsl:template match="section">
    <a id="nav-{@id}" href="{@id}.html"><xsl:value-of select="title"/></a>
  </xsl:template>
</xsl:stylesheet>