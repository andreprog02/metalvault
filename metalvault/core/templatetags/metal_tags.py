from django import template
from decimal import Decimal

register = template.Library()

GRAMS_PER_TROY_OUNCE = Decimal("31.1034768")

@register.filter
def brl(value):
    try:
        n = Decimal(str(value))
        formatted = f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatted}"
    except:
        return "R$ 0,00"

@register.filter
def grams(value):
    try:
        n = Decimal(str(value))
        formatted = f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{formatted} g"
    except:
        return "0 g"

@register.filter
def troy_oz(value):
    try:
        n = Decimal(str(value)) / GRAMS_PER_TROY_OUNCE
        formatted = f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{formatted} oz t"
    except:
        return "0 oz t"

@register.filter
def purity(value):
    try:
        n = Decimal(str(value))
        formatted = f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{formatted}%"
    except:
        return "0%"

@register.filter
def date_br(value):
    if not value:
        return "—"
    try:
        return value.strftime("%d/%m/%Y")
    except:
        return str(value)

@register.filter
def subtract(value, arg):
    try:
        return Decimal(str(value)) - Decimal(str(arg))
    except:
        return 0

@register.filter
def percentage_change(current, original):
    try:
        c = Decimal(str(current))
        o = Decimal(str(original))
        if o == 0:
            return "0,00"
        pct = ((c - o) / o) * 100
        formatted = f"{pct:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return formatted
    except:
        return "0,00"
