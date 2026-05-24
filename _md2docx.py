# -*- coding: utf-8 -*-
"""Markdown -> DOCX converter using stdlib only"""
import zipfile, os, re, io, shutil, xml.etree.ElementTree as ET
from pathlib import Path

PROJECT = r"D:\project\VisDrone_Project"
MD_PATH = os.path.join(PROJECT, "毕业论文_完整版.md")
FIG_DIR = os.path.join(PROJECT, "thesis_figures")
OUT_PATH = os.path.join(PROJECT, "毕业论文_完整版.docx")

def escape_xml(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")

# Read markdown
with open(MD_PATH, "r", encoding="utf-8") as f:
    md = f.read()

# Parse into sections
lines = md.split("\n")

# Build document.xml body
body_parts = []
image_idx = 0
image_rels = []  # (rId, filename)

i = 0
while i < len(lines):
    line = lines[i]

    # Image
    m = re.match(r"!\[(.*?)\]\((.*?)\)", line)
    if m:
        alt = m.group(1)
        img_path = m.group(2)
        # Resolve path
        if not os.path.isabs(img_path):
            img_path = os.path.join(PROJECT, img_path)
        if os.path.exists(img_path):
            image_idx += 1
            rid = f"rIdImg{image_idx}"
            ext = os.path.splitext(img_path)[1].lstrip(".")
            if ext == "jpg": ext = "jpeg"
            fname = f"image{image_idx}.{ext}"
            image_rels.append((rid, fname, img_path))
            # Image paragraph
            body_parts.append(f'''    <w:p>
      <w:pPr><w:jc w:val="center"/></w:pPr>
      <w:r>
        <w:drawing>
          <wp:inline distT="0" distB="0" distL="0" distR="0">
            <wp:extent cx="5400000" cy="3600000"/>
            <wp:docPr id="{image_idx}" name="Picture {image_idx}"/>
            <a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
              <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
                <pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
                  <pic:nvPicPr>
                    <pic:cNvPr id="0" name="img{image_idx}"/>
                    <pic:cNvPicPr/>
                  </pic:nvPicPr>
                  <pic:blipFill>
                    <a:blip r:embed="{rid}"/>
                    <a:stretch><a:fillRect/></a:stretch>
                  </pic:blipFill>
                  <pic:spPr>
                    <a:xfrm><a:off x="0" y="0"/><a:ext cx="5400000" cy="3600000"/></a:xfrm>
                    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
                  </pic:spPr>
                </pic:pic>
              </a:graphicData>
            </a:graphic>
          </wp:inline>
        </w:drawing>
      </w:r>
    </w:p>''')
        i += 1
        continue

    # Table: |---|---|
    m = re.match(r"^\|(.+)\|$", line)
    if m and i+2 < len(lines) and re.match(r"^\|[-:\s|]+\|$", lines[i+1]):
        # Start table
        header_cells = [c.strip() for c in line.split("|")[1:-1]]
        i += 2
        rows_data = []
        rows_data.append(header_cells)
        while i < len(lines) and re.match(r"^\|(.+)\|$", lines[i]):
            cells = [c.strip() for c in lines[i].split("|")[1:-1]]
            rows_data.append(cells)
            i += 1

        # Build table XML
        tbl_xml = ['    <w:tbl>']
        tbl_xml.append('      <w:tblPr><w:tblW w:w="9000" w:type="dxa"/><w:tblBorders><w:top w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:left w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:right w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:insideV w:val="single" w:sz="4" w:space="0" w:color="auto"/></w:tblBorders></w:tblPr>')
        tbl_xml.append('      <w:tblGrid>')
        for c in header_cells:
            tbl_xml.append(f'        <w:gridCol w:w="{9000//len(header_cells)}"/>')
        tbl_xml.append('      </w:tblGrid>')

        for ri, row in enumerate(rows_data):
            tbl_xml.append('        <w:tr>')
            for ci, cell in enumerate(row):
                is_header = ri == 0
                tbl_xml.append(f'          <w:tc><w:tcPr>')
                if is_header:
                    tbl_xml.append(f'            <w:shd w:val="clear" w:color="auto" w:fill="2F5496"/>')
                tbl_xml.append(f'          </w:tcPr>')
                tbl_xml.append(f'            <w:p><w:pPr><w:jc w:val="center"/></w:pPr>')
                if is_header:
                    tbl_xml.append(f'              <w:r><w:rPr><w:b/><w:color w:val="FFFFFF"/></w:rPr><w:t xml:space="preserve">{escape_xml(cell)}</w:t></w:r>')
                else:
                    tbl_xml.append(f'              <w:r><w:t xml:space="preserve">{escape_xml(cell)}</w:t></w:r>')
                tbl_xml.append(f'            </w:p></w:tc>')
            tbl_xml.append('        </w:tr>')
        tbl_xml.append('    </w:tbl>')
        body_parts.append("\n".join(tbl_xml))
        continue

    # Headings
    if line.startswith("# ") and not line.startswith("## "):
        body_parts.append(f'    <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t xml:space="preserve">{escape_xml(line[2:])}</w:t></w:r></w:p>')
    elif line.startswith("## "):
        body_parts.append(f'    <w:p><w:pPr><w:pStyle w:val="Heading2"/></w:pPr><w:r><w:t xml:space="preserve">{escape_xml(line[3:])}</w:t></w:r></w:p>')
    elif line.startswith("### "):
        body_parts.append(f'    <w:p><w:pPr><w:pStyle w:val="Heading3"/></w:pPr><w:r><w:t xml:space="preserve">{escape_xml(line[4:])}</w:t></w:r></w:p>')
    # Separator
    elif line.strip() == "---":
        body_parts.append(f'    <w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="auto"/></w:pBdr></w:pPr></w:p>')
    # Bold line
    elif line.startswith("**") and line.endswith("**"):
        body_parts.append(f'    <w:p><w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">{escape_xml(line[2:-2])}</w:t></w:r></w:p>')
    # List item
    elif re.match(r"^\d+\.\s", line):
        text = re.sub(r"^\d+\.\s", "", line)
        body_parts.append(f'    <w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr></w:pPr><w:r><w:t xml:space="preserve">{escape_xml(text)}</w:t></w:r></w:p>')
    elif line.startswith("- "):
        text = line[2:]
        # Check for inline bold
        body_parts.append(f'    <w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="2"/></w:numPr></w:pPr><w:r><w:t xml:space="preserve">{escape_xml(text)}</w:t></w:r></w:p>')
    # Empty line
    elif line.strip() == "":
        body_parts.append('    <w:p/>')
    # Regular paragraph
    else:
        text = line
        # Handle inline bold: **text**
        parts = re.split(r"(\*\*.*?\*\*)", text)
        runs = []
        for p in parts:
            if p.startswith("**") and p.endswith("**"):
                runs.append(f'<w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">{escape_xml(p[2:-2])}</w:t></w:r>')
            else:
                runs.append(f'<w:r><w:t xml:space="preserve">{escape_xml(p)}</w:t></w:r>')
        body_parts.append(f'    <w:p>{"".join(runs)}</w:p>')

    i += 1

body_xml = "\n".join(body_parts)

# ===== Build DOCX =====
# [Content_Types].xml
content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="jpeg" ContentType="image/jpeg"/>
  <Default Extension="png" ContentType="image/png"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>'''

# _rels/.rels
rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

# word/_rels/document.xml.rels
img_rel_lines = []
for rid, fname, _ in image_rels:
    img_rel_lines.append(f'  <Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{fname}"/>')

doc_rels = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
{chr(10).join(img_rel_lines)}
</Relationships>'''

# word/styles.xml
styles = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:rPr><w:rFonts w:eastAsia="SimSun"/><w:sz w:val="24"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="Heading 1"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr><w:jc w:val="center"/><w:spacing w:before="240" w:after="120"/></w:pPr>
    <w:rPr><w:rFonts w:eastAsia="SimHei"/><w:b/><w:sz w:val="36"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="Heading 2"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr><w:spacing w:before="200" w:after="100"/></w:pPr>
    <w:rPr><w:rFonts w:eastAsia="SimHei"/><w:b/><w:sz w:val="28"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading3">
    <w:name w:val="Heading 3"/>
    <w:basedOn w:val="Normal"/>
    <w:rPr><w:rFonts w:eastAsia="SimHei"/><w:b/><w:sz w:val="24"/></w:rPr>
  </w:style>
</w:styles>'''

# word/document.xml
doc_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"
            xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
            xmlns:o="urn:schemas-microsoft-com:office:office"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
            xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"
            xmlns:v="urn:schemas-microsoft-com:vml"
            xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
            xmlns:w10="urn:schemas-microsoft-com:office:word"
            xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml">
  <w:body>
{body_xml}
    <w:sectPr>
      <w:pgSz w:w="11900" w:h="16840"/>
      <w:pgMar w:top="1440" w:right="1800" w:bottom="1440" w:left="1800"/>
    </w:sectPr>
  </w:body>
</w:document>'''

# Create ZIP (docx)
with zipfile.ZipFile(OUT_PATH, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", content_types)
    z.writestr("_rels/.rels", rels)
    z.writestr("word/document.xml", doc_xml)
    z.writestr("word/styles.xml", styles)
    z.writestr("word/_rels/document.xml.rels", doc_rels)
    for rid, fname, img_path in image_rels:
        z.write(img_path, f"word/media/{fname}")

print(f"OK: {OUT_PATH}")
print(f"Images embedded: {len(image_rels)}")
