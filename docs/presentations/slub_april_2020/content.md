layout: true
  
<div class="my-header"></div>

<div class="my-footer">
  <table>
    <tr>
      <td style="text-align:right">Sächsische Landesbibliothek – Staats- und Universitätsbibliothek</td>
      <td>29. April 2019</td>
      <td style="text-align:right"><a href="https://www.slub-dresden.de/">www.slub-dresden.de</a></td>
    </tr>
    <tr>
      <td style="text-align:right">Referat 2.5</td>
      <td />
    </tr>
  </table>
</div>

<div class="my-title-footer">
  <table>
    <tr>
      <td style="text-align:left"><b>Kay-Michael Würzner</b></td>
    </tr>
    <tr>
      <td style="text-align:left">Referat 2.5</td>
    </tr>
    <tr>
      <td style="font-size:8pt"><b>29. April 2019</b></td>
    </tr>
    <tr>
      <td style="font-size:8pt">XML/TEI-Fortbildung</td>
    </tr>
  </table>
</div>

---

class: title-slide
count: false

# Automatische Erzeugung von TEI-XML
## aus SLUB-Bestandsdaten 

---

# Überblick

- Motivation
- Datengrundlage
  + MODS
  + METS
  + ALTO
- Methode
- Anwendungsperspektive

---

class: part-slide
count: false

# Motivation

---

# Motivation

- **TEI**: weitverbreiteter Standard in den Text ver- und bearbeitenden Wissenschaften
  + Anschluss an bestehende Forschungsinfrastrukturen
  + DFG: *Best Practice* für Editionsprojekte
- Standardformate in Bibliotheken:
  + MODS: bibliothekarische Metadaten
  + METS: Strukturdaten
  + ALTO: Volltexte
- Transformationsszenario zur Erhöhung der **Reichweite**
- **Herausforderung**: nicht-triviale Abbildung zwischen **Stand-Off-** (METS/ALTO) und **Inline-**Kodierung struktureller Information

---

class: part-slide
count: false

# Datengrundlage

---

# Datengrundlage: MODS

- MODS: *Metadata Object Description Schema*
  + XML-Format zur Kodierung bibliographischer Metadaten
  + hoher Freiheitsgrad
  + ausspezifiziert im [MODS-Anwendungsprofil](https://dfg-viewer.de/fileabmin/groups/dfgviewer/MODS-Anwendungsprofil_2.3.1.pdf)
- Beispiel:
```xml
<mods>
  <titleInfo>
    <title>Dresden seine Umgebungen und die Sächsische Schweiz</title>
  </titleInfo>
  <name type="personal">
    <role>
      <roleTerm type="text">creator</roleTerm>
    </role>
    <namePart>Gottschalck, Friedrich</namePart>
  </name>
</mods>
```

---

# Datengrundlage: METS

- METS: *Metadata Encoding & Transmission Standard*
  + XML-Format zur Kodierung digitaler Objekte
  + hoher Freiheitsgrad
  + ausspezifiziert im [METS-Anwendungsprofil](https://dfg-viewer.de/fileabmin/groups/dfgviewer/METS-Anwendungsprofil_2.3.1.pdf)
  + **Kontainerformat**: enthält bspw. MODS
- Grundstruktur:
```xml
<mets>
  <metsHdr/>
  <dmdSec/>
  <amdSec/>
  <fileSec/>
  <structMap/>
  <structLink/>
</mets>
```
---

# Datengrundlage: ALTO

- ALTO: *Analyzed Layout and Text Object*

---

class: part-slide

# Vielen Dank für Ihre Aufmerksamkeit!

<center>
<a href="https://wrznr.github.io/mets-mods2tei/presentations/slub_april_2020/slub_aplril_2020.html">wrznr.github.io/mets-mods2tei</a>
</center>
