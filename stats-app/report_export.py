"""HTML에 확장자를 붙이지 않고 실제 OOXML Word 파일을 생성합니다."""
from io import BytesIO
import math
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.section import WD_ORIENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def build_report_docx(sections, credit):
    doc = Document()
    normal = doc.styles['Normal']
    normal.font.name = '맑은 고딕'
    normal.font.size = Pt(10)
    normal.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), '맑은 고딕')
    for name in ['Title', 'Heading 1', 'Heading 2']:
        doc.styles[name].font.color.rgb = RGBColor(0, 0, 0)
    sec = doc.sections[0]
    widest = max((len(p[2].columns) + int(p[3]) for s in sections for p in s['parts'] if p[0] == 'table'), default=0)
    if widest > 7:
        sec.orientation = WD_ORIENT.LANDSCAPE
        sec.page_width, sec.page_height = Inches(11.69), Inches(8.27)
    sec.top_margin = sec.bottom_margin = Inches(.65)
    sec.left_margin = sec.right_margin = Inches(.65)
    doc.add_heading('통계분석 결과 보고서', 0)
    doc.add_paragraph(credit)
    doc.add_paragraph(f'분석 {len(sections)}건의 결과표와 해석입니다. 그래프는 앱에서 확인하세요.')
    for i, section in enumerate(sections, 1):
        doc.add_heading(f'{i} {section["title"]}', 1)
        doc.add_paragraph(f'자료: {section["data"]} · 분석 시각: {section["time"]} · 결측 처리: {section.get("missing", "기록 없음")}')
        for part in section['parts']:
            if part[0] == 'table':
                _, caption, frame, show_index = part
                frame = frame.reset_index() if show_index else frame
                doc.add_heading(caption, 2)
                table = doc.add_table(rows=1, cols=len(frame.columns))
                table.style = 'Table Grid'
                for c, name in zip(table.rows[0].cells, frame.columns):
                    c.text = str(name)
                props = table.rows[0]._tr.get_or_add_trPr()
                props.append(OxmlElement('w:tblHeader'))
                for values in frame.itertuples(index=False, name=None):
                    cells = table.add_row().cells
                    for cell, value in zip(cells, values):
                        cell.text = '' if value is None or (isinstance(value, float) and math.isnan(value)) else str(value)
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            paragraph.paragraph_format.space_after = Pt(3)
                            for run in paragraph.runs:
                                run.font.size = Pt(8 if widest > 7 else 9)
                doc.add_paragraph()
            else:
                doc.add_paragraph(('APA: ' if part[0] == 'apa' else '') + str(part[1]))
    doc.add_paragraph('결과는 통계적 관계를 보여 줄 뿐 인과관계를 증명하지 않습니다. 분석 가정과 자료 수집 방법을 함께 검토하세요.')
    output = BytesIO()
    doc.save(output)
    return output.getvalue()
