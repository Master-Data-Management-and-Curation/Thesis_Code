# -*- coding: utf-8 -*-
"""
Created on Tue Apr 19 17:22:49 2022

@author: Michele Devetta <michele.devetta@cnr.it>
"""

import io
import os.path as osp

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib.styles import StyleSheet1, ParagraphStyle
from reportlab.lib.colors import Color
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
# Typography
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Frame, Table, TableStyle
# Fonts
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.rl_config import TTFSearchPath
TTFSearchPath.append(osp.join(osp.dirname(osp.abspath(__file__)), 'fonts'))

from Tags.templatetags.tr_month import month_num2en


def loadTTFonts():
    if 'Roboto' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('Roboto', 'Roboto-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('RobotoItalic', 'Roboto-Italic.ttf'))
        pdfmetrics.registerFont(TTFont('RobotoBold', 'Roboto-Bold.ttf'))
        pdfmetrics.registerFont(TTFont('RobotoBoldItalic', 'Roboto-BoldItalic.ttf'))
        pdfmetrics.registerFontFamily('Roboto', normal='Roboto', bold='RobotoBold', italic='RobotoItalic', boldItalic='RobotoBoldItalic')

    if 'RobotoCondesed' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('RobotoCondensed', 'RobotoCondensed-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('RobotoCondensed-Italic', 'RobotoCondensed-Italic.ttf'))
        pdfmetrics.registerFont(TTFont('RobotoCondensed-Bold', 'RobotoCondensed-Bold.ttf'))
        pdfmetrics.registerFont(TTFont('RobotoCondensed-BoldItalic', 'RobotoCondensed-BoldItalic.ttf'))
        pdfmetrics.registerFontFamily('RobotoCondensed', normal='RobotoCondensed', bold='RobotoCondensed-Bold', italic='RobotoCondensed-Italic', boldItalic='RobotoCondensed-BoldItalic')


def loadStyles():
    # Create stylesheet
    stylesheet = StyleSheet1()

    # Create normal style
    stylesheet.add(ParagraphStyle(
        'Normal',
        fontName="Roboto",
        fontSize=10,
        bulletFontName="Roboto",
        bulletFontSize=10,
        alignment=TA_LEFT,
    ))

    # Create heading style
    stylesheet.add(ParagraphStyle(
        'Heading',
        parent=stylesheet['Normal'],
        fontName="Roboto",
        fontSize=20,
        alignment=TA_LEFT,
        # textColor = Color(90/255.0, 92/255.0, 105/255.0, 1),
    ))

    stylesheet.add(ParagraphStyle(
        'SubtitleHeading',
        parent=stylesheet['Normal'],
        fontName="Roboto",
        fontSize=11,
        alignment=TA_LEFT,
        textColor=Color(90/255.0, 92/255.0, 105/255.0, 1),
        spaceAfter=6,
    ))

    stylesheet.add(ParagraphStyle(
        'Subtitle',
        parent=stylesheet['Normal'],
        fontName="RobotoBold",
        fontSize=16,
        alignment=TA_LEFT,
        spaceAfter=6,
        # textColor=Color(90/255.0, 92/255.0, 105/255.0, 1),
    ))

    stylesheet.add(ParagraphStyle(
        'TSProject',
        parent=stylesheet['Normal'],
        fontName="RobotoCondensed",
        fontSize=10,
        alignment=TA_LEFT,
        # textColor=Color(90/255.0, 92/255.0, 105/255.0, 1),
    ))

    stylesheet.add(ParagraphStyle(
        'TSWP',
        parent=stylesheet['Normal'],
        fontName="RobotoCondensed",
        fontSize=9,
        alignment=TA_LEFT,
        textColor=Color(90/255.0, 92/255.0, 105/255.0, 1),
    ))

    stylesheet.add(ParagraphStyle(
        'SignatureHeading',
        parent=stylesheet['Normal'],
        fontName="RobotoBold",
        fontSize=9,
        alignment=TA_CENTER,
        textColor=Color(90/255.0, 92/255.0, 105/255.0, 1),
    ))

    stylesheet.add(ParagraphStyle(
        'SignatureLabel',
        parent=stylesheet['Normal'],
        fontName="RobotoBold",
        fontSize=9,
        alignment=TA_LEFT,
    ))

    stylesheet.add(ParagraphStyle(
        'Signature',
        parent=stylesheet['Normal'],
        fontName="RobotoBold",
        fontSize=10,
        alignment=TA_LEFT,
    ))

    stylesheet.add(ParagraphStyle(
        'SignatureProjects',
        parent=stylesheet['Normal'],
        fontName="Roboto",
        fontSize=9,
        alignment=TA_LEFT,
    ))
    return stylesheet


def PrintPFDTimesheet(contextes):
    print("PDF:", len(contextes))

    # Create buffer
    buffer = io.BytesIO()

    # Load fonts
    loadTTFonts()

    # Load stylesheets
    stylesheet = loadStyles()

    # Canvas
    doc = canvas.Canvas(buffer, pagesize=landscape(A4))
    doc.setTitle(f"H2020 TimeSheets for {contextes[0]['researcher']}")

    # Page size
    page_w, page_h = landscape(A4)

    # Cycle over contextes and create a TS for each
    for context in contextes:

        # Reset page count
        page_count = 0

        # Set available width and height
        aw = page_w - 2*cm
        ah = page_h - 2*cm

        # Header
        header = Paragraph(f"Time Recording for HORIZON 2020 Actions - <b>{month_num2en(context['month'])}, {context['year']:d}</b>", stylesheet['Heading'])
        Frame(1*cm, 1*cm + ah - 0.5*cm, aw, 1*cm).addFromList([header, ], doc)

        beneficiary_title = Paragraph("Beneficiary's / Third party's name", style=stylesheet['SubtitleHeading'])
        beneficiary = Paragraph("Consiglio Nazionale delle Ricerche", style=stylesheet['Subtitle'])
        Frame(1*cm, 1*cm + ah - 2.5*cm, 2*aw/5, 1.6*cm).addFromList([beneficiary_title, beneficiary], doc),

        person_title = Paragraph("Person working on the action", style=stylesheet['SubtitleHeading'])
        person = Paragraph(f"{context['researcher']}", style=stylesheet['Subtitle'])
        Frame(1*cm + 2*aw/5, 1*cm + ah - 2.5*cm, 1.5*aw/5, 1.6*cm).addFromList([person_title, person], doc),

        personnel_title = Paragraph("Type of personnel (see GA art. 6.2.A)", style=stylesheet['SubtitleHeading'])
        personnel = Paragraph(f"{context['employment']}", style=stylesheet['Subtitle'])
        Frame(1*cm + 3.5*aw/5, 1*cm + ah - 2.5*cm, 1.5*aw/5, 1.6*cm).addFromList([personnel_title, personnel], doc),

        # Update ah
        ah -= 3.5*cm

        # ========================0
        # Timesheet table

        # Number of days
        ndays = context['ts']['numdays']

        # Column widths
        colwidths = [0.75*cm for i in range(ndays)] + [1*cm, ]
        colwidths = [aw - sum(colwidths), ] + colwidths

        # Table style
        table_style = TableStyle()
        table_style.add('FONTNAME', (0, 1), (-1, -1), 'RobotoCondensed')         # Font for full table
        table_style.add('FONTNAME', (0, 0), (-1, 0), 'RobotoCondensed-Bold')     # Bold for header line
        table_style.add('FONTNAME', (-1, -1), (-1, -1), 'RobotoCondensed-Bold')  # Bold for total hours
        table_style.add('ALIGN', (1, 0), (-1, -1), 'CENTER')                     # Center for all cell except first column

        # Create data array
        data = []
        data.append(['Days', ] + [f"{d['n']:d}" for d in context['ts']['days']] + ['Σ', ])
        table_style.add('LINEBELOW', (0, 0), (-1, 0), 1.5, (0, 0, 0))

        # Add holiday shading to styles
        for i, d in enumerate(context['ts']['days']):
            if d['holiday']:
                #table_style.add('BACKGROUND', (i+1, 1), (i+1, -1), (254/255.0, 239/255.0, 218/255.0))
                table_style.add('BACKGROUND', (i+1, 1), (i+1, -1), (189/255.0, 242/255.0, 218/255.0))

        linenum = 1
        for prj in context['ts']['projects']:
            pname = f"{prj['name']}: {prj['ref']}" if prj['ref'] != '' else prj['name']
            pname = Paragraph(pname, style=stylesheet['TSProject'])
            if prj['has_wps']:
                # Project with WPs
                data.append([pname, ] + [f"{d:.1f}" for d in prj['days']] + [f"{prj['total']:.1f}", ])
                table_style.add('LINEBELOW', (0, linenum), (-1, linenum), 0.75, (224/255.0, 224/255.0, 224/255.0))
                linenum += 1
                for wp in prj['wps']:
                    data.append([Paragraph(f"{wp['name']}: {wp['desc']}", style=stylesheet['TSWP']), ] + [f"{d:.1f}" for d in wp['days']] + [f"{wp['total']:.1f}", ])
                    table_style.add('FONTSIZE', (0, linenum), (-1, linenum), 9)
                    table_style.add('TEXTCOLOR', (0, linenum), (-1, linenum), (90/255.0, 92/255.0, 105/255.0))
                    if wp['last']:
                        table_style.add('LINEBELOW', (0, linenum), (-1, linenum), 0.75, Color(0, 0, 0))
                    linenum += 1

            else:
                # Project without WPs
                data.append([pname, ] + [f"{d:.1f}" for d in prj['days']] + [f"{prj['total']:.1f}", ])
                if prj['name'] != "Internal activities":
                    table_style.add('LINEBELOW', (0, linenum), (-1, linenum), 0.75, (0, 0, 0))
                linenum += 1

        # Add absences line
        data.append([Paragraph('Absences', style=stylesheet['TSProject']), ] + [d['code'] for d in context['ts']['days']] + ['', ])
        table_style.add('LINEBELOW', (0, linenum), (-1, linenum), 1.5, (0, 0, 0))

        # Add totals line
        data.append([Paragraph('Total', style=stylesheet['TSProject']), ] + [f"{d['total']:.1f}" for d in context['ts']['days']] + [f"{context['ts']['grand_total']:.1f}", ])

        # Render table
        t = Table(data, colWidths=colwidths, style=table_style)

        # Evaluate size of the table
        w, h = t.wrapOn(doc, aw, ah)

        if h > ah:
            # Need to split table
            t_parts = t.split(aw, ah)
        else:
            # Single table
            t_parts = [t, ]

        # Draw table
        for i, t in enumerate(t_parts):
            w, h = t.wrapOn(doc, aw, ah)
            t.drawOn(doc, 1*cm, 1*cm + ah - h)

            if i < len(t_parts) - 1:
                doc.showPage()
                page_count += 1
                ah = page_h - 2*cm
            else:
                ah -= h

        # Spacing
        ah -= 0.5*cm

        #==================
        # LEGEND

        legend_data = [
            ['SL', 'Sick leave'],
            ['PH', 'Public holidays'],
            ['AH', 'Annual holidays'],
            ['BT', 'Business travel'],
        ]

        legend_style = TableStyle()
        legend_style.add('FONTFACE', (0, 0), (-1, -1), 'RobotoCondensed')
        legend_style.add('FONTSIZE', (0, 0), (-1, -1), 9)
        legend_style.add('LINEBELOW', (0, 0), (-1, -1), 0.5, (90/255.0, 92/255.0, 105/255.0))

        legend = Table(legend_data, colWidths=(2*cm, 4*cm), style=legend_style)

        w, h = legend.wrapOn(doc, ah, aw)
        if h > ah:
            doc.showPage()
            page_count += 1
            ah = page_h - 2*cm

        legend.drawOn(doc, 1*cm, 1*cm + ah - h)
        ah -= 0.5*cm

        #==================
        # SIGNATURES

        # Researcher signature style
        researcher_signature_style = TableStyle([
            ('SPAN', (0,0), (1,0)),
            ('BACKGROUND', (0,0), (1,0), (230/255.0, 230/255.0, 240/255.0)),
            # NOTE: added line for date because we disabled the automatic signature date
            ('LINEBELOW', (-1, -2), (-1, -2), 0.5, (135/255.0, 138/255.0, 158/255.0)),
            ('LINEBELOW', (-1, -1), (-1, -1), 0.5, (135/255.0, 138/255.0, 158/255.0)),
            ('VALIGN',(0,0),(1,0),'MIDDLE'),
            ('VALIGN',(0,1),(0,-1),'BOTTOM'),
        ])

        # Director signature style
        director_signature_style = TableStyle([
            ('SPAN', (0,0), (1,0)),
            ('BACKGROUND', (0,0), (1,0), (230/255.0, 230/255.0, 240/255.0)),
            ('LINEBELOW', (-1, -2), (-1, -2), 0.5, (135/255.0, 138/255.0, 158/255.0)),
            ('LINEBELOW', (-1, -1), (-1, -1), 0.5, (135/255.0, 138/255.0, 158/255.0)),
            ('VALIGN',(0,0),(1,0),'MIDDLE'),
            ('VALIGN',(0,1),(0,-1),'BOTTOM'),
        ])

        # PI signature style
        pi_signature_style = TableStyle([
            ('SPAN', (0,0), (1,0)),
            ('BACKGROUND', (0,0), (1,0), (230/255.0, 230/255.0, 240/255.0)),
            ('LINEBELOW', (-1, -1), (-1, -1), 0.5, (135/255.0, 138/255.0, 158/255.0)),
            ('VALIGN',(0,0),(1,0),'MIDDLE'),
            ('VALIGN',(0,1),(0,-1),'BOTTOM'),
        ])

        #signature_style = TableStyle([
        #    ('LINEBELOW', (-1, -1), (-1, -1), 0.5, (90/255.0, 92/255.0, 105/255.0)),
        #])

        # Format date
        if context['sign_day'] is not None:
            import locale
            locale.setlocale(locale.LC_TIME, ("en_US", 'UTF-8'))
            sign_day = context['sign_day'].strftime("%B %-d, %Y")
        else:
            sign_day = ""

        person_signature_data = [
            [Paragraph('Researcher', style=stylesheet['SignatureHeading']), ''],
            [Paragraph('Name:', style=stylesheet['SignatureLabel']),
             Paragraph(context['researcher'], style=stylesheet['Signature'])],
            [Paragraph('Date:', style=stylesheet['SignatureLabel']),
             # NOTE: removed automatic sign day because does not work well when producing timesheets month by month
             #Paragraph(sign_day, style=stylesheet['Signature'])],
             ''],
            [Paragraph('Signature:', style=stylesheet['SignatureLabel']),
             ''],
        ]

        director_signature_data = [
            [Paragraph(context['director'][1], style=stylesheet['SignatureHeading']), ''],
            [Paragraph('Name:', style=stylesheet['SignatureLabel']),
             Paragraph(context['director'][0], style=stylesheet['Signature'])],
            [Paragraph('Date:', style=stylesheet['SignatureLabel']),
             ''],
            [Paragraph('Signature:', style=stylesheet['SignatureLabel']),
             ''],
        ]

        person_signature = Table(person_signature_data, colWidths=(2*cm, 6.5*cm), rowHeights=0.8*cm, style=researcher_signature_style)
        wp, hp = person_signature.wrapOn(doc, aw/3 - 1*cm, ah)

        director_signature = Table(director_signature_data, colWidths=(2*cm, 6.5*cm), rowHeights=0.8*cm, style=director_signature_style)
        wd, hd = director_signature.wrapOn(doc, aw/3 - 1*cm, ah)

        signatures = []
        tot_h = 0
        for name, projects in context['signatures'].items():
            data = [
                [Paragraph(f"PI for projects: {projects}", style=stylesheet['SignatureHeading']), ''],
                [Paragraph('Name:', style=stylesheet['SignatureLabel']),
                 Paragraph(name, style=stylesheet['Signature'])],
                [Paragraph('Signature:', style=stylesheet['SignatureLabel']),
                 ''],
            ]
            t = Table(data, colWidths=(2*cm, 6.5*cm), rowHeights=0.8*cm, style=pi_signature_style)
            w, h = t.wrapOn(doc, aw/3 - 1*cm, page_h)
            signatures.append((t, w, h))
            tot_h += h

        # Add spacing to tot_h
        tot_h += 0.5*cm*(len(signatures)-1)

        if max((tot_h, hp + hd)) > ah:
            doc.showPage()
            page_count += 1
            ah = page_h - 2*cm

        # Person signature
        person_signature.drawOn(doc, aw/3, 1*cm + ah - hp)

        # Director signature
        director_signature.drawOn(doc, aw/3, 1*cm + ah - hp - 0.5*cm - hd)

        # PIs signatures
        for t, w, h in signatures:
            t.drawOn(doc, 1*cm + 2*aw/3, 1*cm + ah - h)
            ah -= h + 0.5*cm

        # Close page and check that the number of pages is even (to be able to print double sided)
        doc.showPage()
        page_count += 1
        if page_count % 2 != 0:
            doc.showPage()

    # Save document
    doc.save()

    # Rewind buffer and return
    buffer.seek(0)
    return buffer
