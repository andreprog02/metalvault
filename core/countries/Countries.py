"""Country-to-continent mapping for coin origins."""

CONTINENTS = {
    "AF": "África",
    "AS": "Ásia",
    "EU": "Europa",
    "NA": "América do Norte",
    "SA": "América do Sul",
    "OC": "Oceania",
    "AN": "Antártida",
}

# (country_code, country_name, continent_code)
COUNTRIES = [
    ("AF", "Afeganistão", "AS"), ("ZA", "África do Sul", "AF"), ("AL", "Albânia", "EU"),
    ("DE", "Alemanha", "EU"), ("AD", "Andorra", "EU"), ("AO", "Angola", "AF"),
    ("AG", "Antígua e Barbuda", "NA"), ("SA", "Arábia Saudita", "AS"), ("DZ", "Argélia", "AF"),
    ("AR", "Argentina", "SA"), ("AM", "Armênia", "AS"), ("AU", "Austrália", "OC"),
    ("AT", "Áustria", "EU"), ("AZ", "Azerbaijão", "AS"), ("BS", "Bahamas", "NA"),
    ("BD", "Bangladesh", "AS"), ("BE", "Bélgica", "EU"), ("BZ", "Belize", "NA"),
    ("BO", "Bolívia", "SA"), ("BA", "Bósnia e Herzegovina", "EU"), ("BR", "Brasil", "SA"),
    ("BG", "Bulgária", "EU"), ("CA", "Canadá", "NA"), ("CL", "Chile", "SA"),
    ("CN", "China", "AS"), ("CO", "Colômbia", "SA"), ("KR", "Coreia do Sul", "AS"),
    ("KP", "Coreia do Norte", "AS"), ("CR", "Costa Rica", "NA"), ("HR", "Croácia", "EU"),
    ("CU", "Cuba", "NA"), ("DK", "Dinamarca", "EU"), ("EC", "Equador", "SA"),
    ("EG", "Egito", "AF"), ("SV", "El Salvador", "NA"), ("AE", "Emirados Árabes", "AS"),
    ("ES", "Espanha", "EU"), ("US", "Estados Unidos", "NA"), ("EE", "Estônia", "EU"),
    ("ET", "Etiópia", "AF"), ("FI", "Finlândia", "EU"), ("FR", "França", "EU"),
    ("GH", "Gana", "AF"), ("GE", "Geórgia", "AS"), ("GR", "Grécia", "EU"),
    ("GT", "Guatemala", "NA"), ("GY", "Guiana", "SA"), ("HT", "Haiti", "NA"),
    ("NL", "Holanda", "EU"), ("HN", "Honduras", "NA"), ("HU", "Hungria", "EU"),
    ("IN", "Índia", "AS"), ("ID", "Indonésia", "AS"), ("IR", "Irã", "AS"),
    ("IQ", "Iraque", "AS"), ("IE", "Irlanda", "EU"), ("IS", "Islândia", "EU"),
    ("IL", "Israel", "AS"), ("IT", "Itália", "EU"), ("JM", "Jamaica", "NA"),
    ("JP", "Japão", "AS"), ("JO", "Jordânia", "AS"), ("KZ", "Cazaquistão", "AS"),
    ("KE", "Quênia", "AF"), ("KW", "Kuwait", "AS"), ("LV", "Letônia", "EU"),
    ("LB", "Líbano", "AS"), ("LY", "Líbia", "AF"), ("LT", "Lituânia", "EU"),
    ("LU", "Luxemburgo", "EU"), ("MK", "Macedônia do Norte", "EU"), ("MY", "Malásia", "AS"),
    ("MA", "Marrocos", "AF"), ("MX", "México", "NA"), ("MZ", "Moçambique", "AF"),
    ("MC", "Mônaco", "EU"), ("MN", "Mongólia", "AS"), ("ME", "Montenegro", "EU"),
    ("MM", "Mianmar", "AS"), ("NI", "Nicarágua", "NA"), ("NG", "Nigéria", "AF"),
    ("NO", "Noruega", "EU"), ("NZ", "Nova Zelândia", "OC"), ("OM", "Omã", "AS"),
    ("PA", "Panamá", "NA"), ("PY", "Paraguai", "SA"), ("PE", "Peru", "SA"),
    ("PL", "Polônia", "EU"), ("PT", "Portugal", "EU"), ("GB", "Reino Unido", "EU"),
    ("DO", "República Dominicana", "NA"), ("CZ", "República Tcheca", "EU"),
    ("RO", "Romênia", "EU"), ("RU", "Rússia", "EU"), ("SE", "Suécia", "EU"),
    ("CH", "Suíça", "EU"), ("RS", "Sérvia", "EU"), ("SG", "Singapura", "AS"),
    ("SY", "Síria", "AS"), ("TH", "Tailândia", "AS"), ("TW", "Taiwan", "AS"),
    ("TN", "Tunísia", "AF"), ("TR", "Turquia", "AS"), ("UA", "Ucrânia", "EU"),
    ("UY", "Uruguai", "SA"), ("UZ", "Uzbequistão", "AS"), ("VE", "Venezuela", "SA"),
    ("VN", "Vietnã", "AS"), ("ZW", "Zimbábue", "AF"),
    ("XX", "Outro / Desconhecido", ""),
]

COUNTRY_CHOICES = [(code, name) for code, name, _ in COUNTRIES]

COUNTRY_TO_CONTINENT = {code: cont for code, _, cont in COUNTRIES}

def get_continent_name(country_code):
    cont_code = COUNTRY_TO_CONTINENT.get(country_code, "")
    return CONTINENTS.get(cont_code, "Desconhecido")

def get_continent_code(country_code):
    return COUNTRY_TO_CONTINENT.get(country_code, "")

def get_country_name(country_code):
    for code, name, _ in COUNTRIES:
        if code == country_code:
            return name
    return "Desconhecido"