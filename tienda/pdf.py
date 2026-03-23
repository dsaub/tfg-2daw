import os
from django.conf import settings

from fpdf import FPDF
import string, random
class Recibo(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'RECIBO DE PAGO', ln=True, align='C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', align='C')

def generar_recibo(cliente: str, total: float, objetos: list, metodo_pago: str):
    pdf = Recibo()
    font_path = "/fonts/Roboto-Regular.ttf"
    pdf.add_font('Roboto', '', '/fonts/Roboto-Regular.ttf')
    pdf.add_font('Roboto', 'B', '/fonts/Roboto-Bold.ttf')
    pdf.add_page()
    pdf.set_font('Roboto', size=12)

    pdf.cell(0, 10, f"Cliente: {cliente}", ln=True)
    pdf.cell(0, 10, f"")

    DATA = []
    DATA.append(
        ("Cant.", "Nombre", "Precio Unit.", "Subtotal")
    )
    for i in objetos:
        DATA.append(
            (str(i["amount"]), str(i["product_name"]), str(i["price"]), str(float(i["price"])*int(i["amount"])))
        )
    pdf.cell(0, 10, "DETALLE DEL COBRO", ln=True, align='C')
    pdf.ln(5)

    with pdf.table() as table:
        for data_row in DATA:
            row = table.row()
            for datum in data_row:
                row.cell(datum)
    pdf.ln(5)
    pdf.set_font('Roboto', size=12)
    pdf.cell(0, 10, f'TOTAL A PAGAR: {total} €', align="R")
    return pdf.output(dest="S")
    