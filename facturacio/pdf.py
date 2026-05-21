from io import BytesIO
from django.http import HttpResponse
from django.template.loader import render_to_string


def generar_pdf_factura(factura):
    try:
        import weasyprint
    except ImportError:
        return HttpResponse(
            'WeasyPrint no està instal·lat. Afegiu-lo amb: pip install weasyprint',
            status=501,
            content_type='text/plain',
        )
    html = render_to_string('facturacio/factura_pdf.html', {'factura': factura})
    pdf_file = BytesIO()
    weasyprint.HTML(string=html).write_pdf(pdf_file)
    pdf_file.seek(0)
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="factura_{factura.numero}.pdf"'
    return response
