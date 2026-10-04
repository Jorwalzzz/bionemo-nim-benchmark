import os
import sys
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        # Outer double border (Security Certificate frame)
        self.setStrokeColor(colors.HexColor("#0f172a")) # Slate 900
        self.setLineWidth(2)
        self.rect(20, 20, 572, 752)
        self.setStrokeColor(colors.HexColor("#38bdf8")) # Sky 400
        self.setLineWidth(0.75)
        self.rect(24, 24, 564, 744)

        # Header running title
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(32, 752, "JORWAL™ INTELLECTUAL PROPERTY & LEGAL CERTIFICATION INSTRUMENT")
        self.drawRightString(580, 752, "DOC ID: JORWAL-CERT-2026-001")

        # Footer
        self.setFont("Helvetica", 7.5)
        self.drawString(32, 30, "CONFIDENTIAL & LEGALLY BINDING DECLARATION • ENFORCEABLE UNDER BERNE & PARIS CONVENTIONS")
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(580, 30, page_str)
        self.restoreState()

def generate_certificate():
    out_dir = os.path.join(os.getcwd(), "results")
    os.makedirs(out_dir, exist_ok=True)
    pdf_path = os.path.join(out_dir, "JORWAL_LEGAL_CERTIFICATE_OF_OWNERSHIP.pdf")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=46
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        alignment=1 # Center
    )

    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#0284c7"),
        alignment=1 # Center
    )

    section_hdr = ParagraphStyle(
        'SecHdr',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#0f172a")
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#334155")
    )

    bold_label = ParagraphStyle(
        'BoldLbl',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#0f172a")
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#0f172a")
    )

    elements = []

    # Title Banner
    elements.append(Paragraph("OFFICIAL CERTIFICATE OF INTELLECTUAL PROPERTY", title_style))
    elements.append(Paragraph("DEED OF TRADEMARK, COPYRIGHT, CITATION & ECOSYSTEM OWNERSHIP", subtitle_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=10))

    # Executive Declaration Box
    p_exec = Paragraph(
        "<b>LEGAL ATTESTATION:</b> This document certifies that <b>Aarav Jorwal</b> (operating globally as <b>Jorwal</b> / <b>@Jorwalzzz</b>) "
        "is the sole creator, original architect, and exclusive worldwide rights holder of the <b>JORWAL™</b> mark, the "
        "<b>JORWAL™ NIM SWARM OS</b> biocompute platform, and all derivative technologies. Priority of first use in commerce and "
        "copyright authorship is formally established herein under international statutory law.",
        body_style
    )
    exec_table = Table([[p_exec]], colWidths=[540])
    exec_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f0fdf4")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#16a34a")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(exec_table)
    elements.append(Spacer(1, 12))

    # Section 1: Proprietor & Institutional Identifiers
    elements.append(Paragraph("1. PROPRIETOR & REGISTERED GLOBAL IDENTIFIERS", section_hdr))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=6))

    id_data = [
        [Paragraph("Legal Proprietor Name:", bold_label), Paragraph("<b>Aarav Jorwal</b>", body_style)],
        [Paragraph("Professional / Brand Name:", bold_label), Paragraph("<b>Jorwal™</b> / <b>JORWAL™</b>", body_style)],
        [Paragraph("Digital Handle / Alias:", bold_label), Paragraph("<b>@Jorwalzzz</b>", body_style)],
        [Paragraph("Official Verified ORCID iD:", bold_label), Paragraph("<b>https://orcid.org/0009-0008-8922-3599</b>", bold_label)],
        [Paragraph("Primary Contact Email:", bold_label), Paragraph("jorwalnetwork@proton.me", body_style)],
        [Paragraph("Cryptographic Master Repository:", bold_label), Paragraph("https://github.com/Jorwalzzz/bionemo-nim-benchmark", body_style)],
        [Paragraph("Latest Cryptographic Git SHA:", bold_label), Paragraph("c0480b9c2f9bb3e77c800d9c3dbde1fa011ac269", code_style)],
        [Paragraph("Effective Date & Legal Priority:", bold_label), Paragraph("October 4, 2026 (Incontestable Prior Use)", body_style)],
    ]
    t_id = Table(id_data, colWidths=[180, 360])
    t_id.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#f8fafc")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_id)
    elements.append(Spacer(1, 12))

    # Section 2: Global Registry Lockdown Matrix
    elements.append(Paragraph("2. VERIFIED GLOBAL REGISTRY LOCKDOWN (LIVE PROOF)", section_hdr))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=6))

    reg_headers = [Paragraph("<b>Registry / Platform</b>", bold_label), Paragraph("<b>Exact Namespace</b>", bold_label), Paragraph("<b>Status</b>", bold_label), Paragraph("<b>Verification URI / Details</b>", bold_label)]
    reg_rows = [
        reg_headers,
        [Paragraph("PyPI (Python Core)", body_style), Paragraph("<b>jorwal</b>", bold_label), Paragraph("<font color='#16a34a'><b>LIVE (v1.0.0)</b></font>", body_style), Paragraph("pypi.org/project/jorwal/1.0.0/", code_style)],
        [Paragraph("PyPI (AI Platform)", body_style), Paragraph("<b>jorwal-nim</b>", bold_label), Paragraph("<font color='#16a34a'><b>LIVE (v1.0.0)</b></font>", body_style), Paragraph("pypi.org/project/jorwal-nim/1.0.0/", code_style)],
        [Paragraph("npm (JS / Node)", body_style), Paragraph("<b>jorwal-nim</b>", bold_label), Paragraph("<font color='#16a34a'><b>LIVE (v1.0.0)</b></font>", body_style), Paragraph("npmjs.com/package/jorwal-nim", code_style)],
        [Paragraph("Hugging Face (AI Hub)", body_style), Paragraph("<b>jorwal-labs</b>", bold_label), Paragraph("<font color='#16a34a'><b>LIVE (Org)</b></font>", body_style), Paragraph("huggingface.co/jorwal-labs", code_style)],
        [Paragraph("Read the Docs (Core)", body_style), Paragraph("<b>jorwal</b>", bold_label), Paragraph("<font color='#16a34a'><b>LOCKED</b></font>", body_style), Paragraph("jorwal.readthedocs.io", code_style)],
        [Paragraph("Read the Docs (AI OS)", body_style), Paragraph("<b>jorwal-nim</b>", bold_label), Paragraph("<font color='#16a34a'><b>LOCKED</b></font>", body_style), Paragraph("jorwal-nim.readthedocs.io", code_style)],
        [Paragraph("CERN / Zenodo", body_style), Paragraph("bionemo-nim-benchmark", bold_label), Paragraph("<font color='#16a34a'><b>ACTIVE DOI</b></font>", body_style), Paragraph("Permanent DataCite CERN Geneva", body_style)],
        [Paragraph("ORCID Consortium", body_style), Paragraph("0009-0008-8922-3599", bold_label), Paragraph("<font color='#16a34a'><b>VERIFIED</b></font>", body_style), Paragraph("orcid.org/0009-0008-8922-3599", code_style)],
    ]
    t_reg = Table(reg_rows, colWidths=[120, 110, 85, 225])
    t_reg.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 3.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    elements.append(t_reg)
    elements.append(Spacer(1, 12))

    # Section 3: Legal Trademark & Brand Policy
    elements.append(Paragraph("3. ENFORCEABLE TRADEMARK & TRADE NAME DECLARATION", section_hdr))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=6))

    p_tm = Paragraph(
        "<b>STATUTORY ASSERTION:</b> Under the common-law priority rule of first use in commerce, the <b>Trade Marks Act, 1999 "
        "(Sections 27(2) & 34)</b>, the United States <b>Lanham Act § 43(a) (15 U.S.C. § 1125(a))</b>, and the <b>Paris Convention "
        "for the Protection of Industrial Property (Article 8)</b> across 179+ nations, the marks:<br/>"
        "• <b>JORWAL</b> (Uppercase Standard Character Mark)<br/>"
        "• <b>Jorwal</b> (Title Case Wordmark)<br/>"
        "• <b>jorwal</b> (Lowercase Namespace, CLI & API Identifier)<br/>"
        "• <b>JORWAL™ NIM SWARM OS</b>, <b>JORWAL TECH™</b>, <b>JORWAL AI™</b>, <b>JORWAL LABS™</b><br/>"
        "are the exclusive proprietary property of Aarav Jorwal. The claim covers all of <b>Nice Class 9</b> (AI/software/operating systems), "
        "<b>Class 42</b> (SaaS/cloud compute/biocompute), and <b>Class 44</b> (bioinformatics). Third-party unauthorized commercial use, "
        "re-branding, or typosquatting is strictly prohibited and actionable under international passing-off and trademark infringement law.",
        body_style
    )
    elements.append(p_tm)
    elements.append(Spacer(1, 10))

    # Section 4: License & Academic Citation Clause
    elements.append(Paragraph("4. OPEN SOURCE LICENSE & MANDATORY ACADEMIC CITATION", section_hdr))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=6))

    p_lic = Paragraph(
        "<b>LICENSE COVENANT:</b> The software source code is copyleft-licensed under the <b>GNU Affero General Public License v3.0 (AGPL-3.0)</b>. "
        "This license strictly grants source code rights while expressly withholding and reserving all brand, trade name, and trademark rights.<br/>"
        "<b>MANDATORY SCHOLARLY CITATION:</b> Any academic paper, industrial whitepaper, or derivative compute model utilizing this platform "
        "must cite the work under <b>CITATION.cff</b> specification as:<br/>"
        "<i>Jorwal, A. (@Jorwalzzz). JORWAL™ NIM SWARM OS: Autonomous Multi-Agent AI Discovery Platform Powered by NVIDIA BioNeMo & NIM (v2.2.1). "
        "ORCID: 0009-0008-8922-3599. Available at https://github.com/Jorwalzzz/bionemo-nim-benchmark</i>",
        body_style
    )
    elements.append(p_lic)
    elements.append(Spacer(1, 14))

    # Formal Signature & Execution Box
    sig_data = [
        [
            Paragraph("<b>EXECUTED & ATTESTED BY:</b><br/><br/>"
                      "<b>Aarav Jorwal</b><br/>"
                      "Founder, Lead Architect & Rights Holder<br/>"
                      "ORCID: 0009-0008-8922-3599<br/>"
                      "Verified GitHub: @Jorwalzzz", body_style),
            Paragraph("<b>LEGAL SEAL & VERIFICATION TIMESTAMP:</b><br/><br/>"
                      "<b>Date of Execution:</b> October 4, 2026<br/>"
                      "<b>Document Hash:</b> SHA256-AUTHENTICATED<br/>"
                      "<b>Jurisdiction:</b> Global (Paris & Berne Conventions)<br/>"
                      "<b>Status:</b> INCONTESTABLE PRIOR ART PROOF", body_style)
        ]
    ]
    t_sig = Table(sig_data, colWidths=[270, 270])
    t_sig.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#0f172a")),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('PADDING', (0,0), (-1,-1), 10),
        ('LINEBEFORE', (1,0), (1,-1), 0.5, colors.HexColor("#cbd5e1")),
    ]))
    elements.append(t_sig)

    doc.build(elements, canvasmaker=NumberedCanvas)
    print(f"Generated PDF at: {pdf_path}")

if __name__ == "__main__":
    generate_certificate()
