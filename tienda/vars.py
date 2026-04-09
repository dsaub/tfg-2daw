PAGE_SIZE = 20
VAT_RATE = 0.21  # IVA 21%
STOCK_RESERVATION_MINUTES = 5

TRANSACTION_CODE_PREFIX = "comal-"
TRANSACTION_CODE_LENGTH = 32
TRANSACTION_CODE_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

# Restricciones de envío
SHIPPING_COUNTRY = "España"
ALMERIA_POSTAL_CODE_PREFIX = "04"
ALMERIA_MUNICIPALITIES_DISPLAY = (
	"Abla", "Abrucena", "Adra", "Albánchez", "Alboloduy", "Albox", "Alcolea", "Alcóntar",
	"Alcudia de Monteagud", "Alhabia", "Alhama de Almería", "Alicún", "Almería", "Almócita",
	"Alsodux", "Antas", "Arboleas", "Armuña de Almanzora", "Bacares", "Bayárcal", "Bayarque",
	"Bédar", "Beires", "Benahadux", "Benitagla", "Benizalón", "Bentarique", "Berja", "Canjáyar",
	"Cantoria", "Carboneras", "Castro de Filabres", "Chercos", "Chirivel", "Cóbdar",
	"Cuevas del Almanzora", "Dalías", "Enix", "Félix", "Fines", "Fiñana", "Fondón", "Gádor",
	"Gallardos", "Los Gallardos", "Garrucha", "Gérgal", "Huécija", "Huércal de Almería",
	"Huércal-Overa", "Íllar", "Instinción", "Laroya", "Laujar de Andarax", "Líjar", "Lubrín",
	"Lucainena de las Torres", "Lúcar", "Macael", "María", "Mojácar", "Mojonera", "La Mojonera",
	"Nacimiento", "Níjar", "Ohanes", "Olula de Castro", "Olula del Río", "Oria", "Padules",
	"Partaloa", "Paterna del Río", "Pechina", "Pulpí", "Purchena", "Rágol", "Rioja",
	"Roquetas de Mar", "Santa Cruz de Marchena", "Santa Fe de Mondújar", "Senés", "Serón", "Sierro",
	"Somontín", "Sorbas", "Suflí", "Tabernas", "Taberno", "Tahal", "Terque", "Tíjola", "Turre",
	"Turrillas", "Uleila del Campo", "Urrácal", "Velefique", "Vélez-Blanco", "Vélez-Rubio", "Vera",
	"Viator", "Vícar", "Zurgena"
)

verify_message = """
¡Buenas {name}!

Muchas gracias por registrarte en Comercialmeria, para verificar que el correo que ha empleado es el suyo, por favor, haga click en el siguiente enlace.

Si por alguna razón no es su correo, eliminelo inmediatamente y no le de click al enlace.

{protocol}://{domain}/tienda/verify/{code}

Este email ha sido automatizado
"""

login_message = """
¡Buenas {name}!

Le enviamos este correo para indicarle que se acaba de iniciar sesión en un nuevo dispositivo.
En caso de que no sea usted, para proteger compras indebidas, ¡cambie la contraseña inmediatamente! 
"""