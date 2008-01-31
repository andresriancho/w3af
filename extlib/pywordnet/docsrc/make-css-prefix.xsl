<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:xi="http://www.w3.org/2003/XInclude"
                exclude-result-prefixes="xi"
                version="1.0">
  
  <xsl:output method="text"/>
  
  <xsl:template match="/">
    <xsl:for-each select="//xi:include">
      <xsl:variable name="id" select="document(@href)/*/@id"/>
      <xsl:text>#</xsl:text>
      <xsl:value-of select="$id"/>
      <xsl:text> </xsl:text>
      <xsl:text>#nav-</xsl:text>
      <xsl:value-of select="$id"/>
      <xsl:text>,&#10;</xsl:text>
    </xsl:for-each>
  </xsl:template>
</xsl:stylesheet>