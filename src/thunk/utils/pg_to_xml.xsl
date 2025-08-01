<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:xs="http://www.w3.org/2001/XMLSchema"
 xmlns:html="http://www.w3.org/1999/xhtml"
 xmlns:METS="http://www.loc.gov/METS/" 
 xmlns:xlink="http://www.w3.org/1999/xlink"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
 xmlns:marc="http://www.loc.gov/MARC21/slim"
 exclude-result-prefixes="xs html"
 version="3.1">
 <xsl:output method="xml" indent="yes"/>
 
 <xsl:template match="METS:mets">
  <xsl:apply-templates select="METS:structMap" />
 </xsl:template>
 
 <xsl:template match="METS:structMap">
  <xsl:apply-templates select="METS:div[@TYPE='volume']" />
 </xsl:template>
 
 <xsl:template match="METS:div[@TYPE='volume']">
  <div type='volume'>
   <xsl:apply-templates />
  </div>
 </xsl:template>
 
 <xsl:template match="METS:div[@TYPE='page']">
  <pb>
   <xsl:if test="@ORDER">
    <xsl:attribute name="n"><xsl:value-of select="@ORDER"/></xsl:attribute>
   </xsl:if>
  </pb>
 <xsl:if test="@ORDERLABEL">
  <cb>
   <xsl:attribute name="n"><xsl:value-of select="@ORDERLABEL"/></xsl:attribute>
  </cb>
 </xsl:if>
 </xsl:template>
 
</xsl:stylesheet>