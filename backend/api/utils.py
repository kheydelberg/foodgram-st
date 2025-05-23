import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate
from django.http import HttpResponse


def generate_text_shopping_list(components, user):
    """Generate a plain text shopping list for download.

    Args:
        components: List of ingredients with their amounts
        user: User object for whom the list is generated

    Returns:
        HttpResponse with text file attachment
    """
    lines = []
    header = (
        f"Shopping list for user: {user.get_full_name() or user.username}\n"
    )
    lines.append(header)
    lines.append("=" * len(header.strip()) + "\n")

    for item in components:
        lines.append(f"{item['name']} ({item['unit']}) — {item['total']}")

    response = HttpResponse('\n'.join(lines), content_type='text/plain')
    response['Content-Disposition'] = (
        'attachment; filename="shopping_list.txt"'
    )
    return response


def generate_pdf_shopping_list(components, user):
    """Generate a PDF shopping list for download.

    Args:
        components: List of ingredients with their amounts
        user: User object for whom the list is generated

    Returns:
        HttpResponse with PDF file attachment
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        alignment=1,
        spaceAfter=20
    )

    title = f"Shopping list: {user.get_full_name() or user.username}"
    elements.append(Paragraph(title, title_style))

    for item in components:
        item_text = (
            f"<b>{item['name']}</b> ({item['unit']}) — {item['total']}"
        )
        elements.append(Paragraph(item_text, styles['Normal']))
        elements.append(Paragraph("<br/>", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = (
        'attachment; filename="shopping_list.pdf"'
    )
    return response
