<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">
  
  <xsl:import href="file:///c:/laszlo/tools/docbook-xsl-1.65.1/html/chunk.xsl"/>
  <!-- ToC/LoT/Index Generation -->
  <xsl:param name="generate.section.toc.level" select="'0'"/>
  <xsl:param name="toc.section.depth" select="2"/>
  <xsl:param name="toc.max.depth" select="2"/>
  <!-- Extensions -->
  <xsl:param name="graphicsize.extension" select="0"/>
  <!-- HTML -->
  <xsl:param name="use.id.as.filename" select="1"/>
  <xsl:param name="html.stylesheet" select="'styles.css'"/>

  <!--xsl:param name="chunker.output.method" select="'xml'"/>
  <xsl:param name="chunker.output.standalone" select="'yes'"/>
  <xsl:param name="chunker.output.omit-xml-declaration" select="'yes'"/-->
  <!-- Meta/*.info -->
  <xsl:param name="make.year.ranges" select="1"/>
  <!-- Chunking -->
  <xsl:param name="chunk.fast" select="1"/>
  <xsl:param name="chunk.section.depth" select="1"/>
  <xsl:param name="chunk.first.sections" select="1"/>
  <xsl:param name="chunker.output.indent" select="'yes'"/>
  <xsl:param name="html.extra.head.links" select="0"/>
  <!-- Miscellaneous -->
  <xsl:param name="shade.verbatim" select="1"/>  
  
  <!-- XSLT Processing -->
  <xsl:param name="suppress.navigation" select="1"/>
  
  <xsl:param name="generate.toc">
    appendix  toc,title
    article/appendix  nop
    article   nop
    book      toc,title,figure,table,example,equation
    chapter   toc,title,figure,table,example,equation
    part      toc,title
    preface   toc,title
    qandadiv  toc
    qandaset  toc
    reference toc,title
    sect1     toc
    sect2     toc
    sect3     toc
    sect4     toc
    sect5     toc
    section   toc
    set       toc,title
  </xsl:param>
  
  <xsl:template name="body.attributes">
    <xsl:attribute name="id">
      <xsl:value-of select="@id"/>
      <xsl:if test="not(@id)">
        <xsl:text>index</xsl:text>
      </xsl:if>
    </xsl:attribute>
  </xsl:template>
  
  <xsl:template name="user.header.navigation">
    <div class="banner">
      <span class="projectname"><a href="http://osteele.com/projects/pywordnet/">PyWordNet</a></span>
    </div>
    
    <div id="navigation">
      <ul>&#10;
        <li><a id="nav-index" href="index.html">About</a></li>&#10;
        <xsl:for-each select="/*/section">
          <li>
            <a id="nav-{@id}" href="{@id}.html"><xsl:value-of select="title"/></a>
          </li>
        </xsl:for-each>
      </ul>&#10;
    </div>
  </xsl:template>
</xsl:stylesheet>
