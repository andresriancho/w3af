<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:xi="http://www.w3.org/2003/XInclude"
                exclude-result-prefixes="xi"
                version="1.0">
  
  <xsl:template match="/|@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
  </xsl:template>
  
  <xsl:template match="contributors">
    <informaltable>
      <tgroup cols='2'>
<thead>
<row>
  <entry>Name</entry>
  <entry>Affiliation</entry>
  <entry>Homepage</entry>
</row>
</thead>        <tbody>
          <xsl:apply-templates select="developer"/>
          <xsl:apply-templates select="contributor">
            <xsl:sort select="substring-after(normalize-space(name), ' ')"/>
          </xsl:apply-templates>
        </tbody>
      </tgroup>
    </informaltable>
  </xsl:template>
  
  <xsl:template match="contributor|developer">
    <xsl:variable name="name" select="normalize-space(name)"/>
    <row>
      <entry>
        <author>
          <firstname><xsl:value-of select="substring-before($name, ' ')"/></firstname>
          <surname><xsl:value-of select="substring-after($name, ' ')"/></surname>
          <email><xsl:value-of select="email"/></email>
        </author>
      </entry>
      <entry>
        <xsl:if test="organization">
        <para>
          <xsl:value-of select="organization"/>
        </para>
        </xsl:if>
      </entry>
      <xsl:if test="webpage">
        <entry>
          <ulink url="{webpage}"/>
        </entry>
      </xsl:if>
    </row>
  </xsl:template>
</xsl:stylesheet>