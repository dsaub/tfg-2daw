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
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(0, 10, f"Cliente: {cliente}", ln=True)
    pdf.cell(0, 10, f"")

    DATA = []
    DATA.append(
        ("Cant.", "Nombre", "Precio Unit.", "Subtotal")
    )

    pdf.cell(0, 10, "DETALLE DEL COBRO", ln=True, align='C')
    pdf.ln(5)

    with pdf.table() as table:
        for data_row in DATA:
            row = table.row()
            for datum in data_row:
                row.cell(datum)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f'TOTAL A PAGAR: {total} €', align="R")
    return pdf.output(dest="S")
    