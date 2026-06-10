import os
from django.conf import settings

from fpdf import FPDF
import string, random
class Recibo(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, "Comercialmeria S.L")
        self.cell(0, 10, 'RECIBO DE PAGO', ln=True, align='R')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', align='C')

def generar_recibo(cliente: str, total: float, objetos: list, metodo_pago: str, transaction_code: str):
    pdf = Recibo()
    pdf.add_font('Roboto', '', str(settings.BASE_DIR / 'fonts' / 'Roboto-Regular.ttf'))
    pdf.add_font('Roboto', 'B', str(settings.BASE_DIR / 'fonts' / 'Roboto-Bold.ttf'))
    pdf.add_page()
    pdf.set_font('Roboto', size=12)

    METODOS_MAP = {"stripe": "Stripe", "paypal": "PayPal", "manual": "Manual"}
    metodo_mostrar = METODOS_MAP.get(metodo_pago, metodo_pago)

    pdf.cell(0, 10, f"Cliente: {cliente}", ln=True)
    pdf.cell(0, 10, f"ID de transaccion: {transaction_code}", ln=True)
    pdf.cell(0, 10, f"Metodo de pago: {metodo_mostrar}", ln=True)
    pdf.cell(0, 10, "")

    DATA = []
    DATA.append(
        ("Cant.", "Nombre", "Precio Unit.", "Subtotal")
    )
    for i in objetos:
        DATA.append(
            (str(i["amount"]), str(i["product_name"]), str(i["price"]), str(float(i["price"])*int(i["amount"])))
        )
    pdf.cell(0, 10, "DETALLE DEL COBRO", ln=True, align='R')
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
    