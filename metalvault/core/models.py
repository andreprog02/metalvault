import uuid
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

GRAMS_PER_TROY_OUNCE = 31.1034768


class MetalType(models.TextChoices):
    BAR = "bar", "Barra"
    COIN = "coin", "Moeda"
    MEDAL = "medal", "Medalha"
    OTHER = "other", "Outro"


class MetalMaterial(models.TextChoices):
    GOLD = "gold", "Ouro"
    SILVER = "silver", "Prata"
    PLATINUM = "platinum", "Platina"
    OTHER = "other", "Outro"


class BanknoteCurrency(models.TextChoices):
    USD = "usd", "Dólar (US$)"
    EUR = "eur", "Euro (€)"
    GBP = "gbp", "Libra (£)"
    BRL = "brl", "Real (R$)"
    OTHER = "other", "Outra"


class Location(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="locations")
    name = models.CharField("Nome", max_length=200)
    description = models.TextField("Descrição", blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def metal_count(self):
        return self.metals.count()

    def banknote_count(self):
        return self.banknotes.count()


class Metal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="metals")
    serial_number = models.CharField("Número de série", max_length=200, blank=True, default="")
    invoice_number = models.CharField("Número da NF", max_length=200, blank=True, default="")
    type = models.CharField("Tipo", max_length=10, choices=MetalType.choices, default=MetalType.BAR)
    type_custom_label = models.CharField("Tipo personalizado", max_length=200, blank=True, default="")
    material = models.CharField("Material", max_length=10, choices=MetalMaterial.choices, default=MetalMaterial.GOLD)
    material_custom_label = models.CharField("Material personalizado", max_length=200, blank=True, default="")
    purity_percentage = models.DecimalField("Pureza (%)", max_digits=6, decimal_places=3, default=99.9)
    weight_grams = models.DecimalField("Peso (g)", max_digits=14, decimal_places=4, default=0)
    acquisition_date = models.DateField("Data de aquisição")
    acquisition_value = models.DecimalField("Valor de aquisição (R$)", max_digits=14, decimal_places=2, default=0)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name="metals")
    photo = models.ImageField("Foto", upload_to="metals/photos/", blank=True)
    certificate = models.FileField("Certificado", upload_to="metals/certificates/", blank=True)
    invoice_file = models.FileField("Nota Fiscal", upload_to="metals/invoices/", blank=True)
    # IRPF fields
    description = models.TextField("Descrição IRPF", blank=True, default="")
    vendor_name = models.CharField("Nome do vendedor", max_length=300, blank=True, default="")
    vendor_document = models.CharField("CPF/CNPJ do vendedor", max_length=20, blank=True, default="")
    sold_date = models.DateField("Data de venda", null=True, blank=True)
    sold_value = models.DecimalField("Valor de venda", max_digits=14, decimal_places=2, null=True, blank=True)
    irpf_group = models.CharField("Grupo IRPF", max_length=10, blank=True, default="")
    irpf_code = models.CharField("Código IRPF", max_length=10, blank=True, default="")
    irpf_include_override = models.BooleanField("Incluir no IRPF", null=True, blank=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_type_display()} - {self.get_material_display()}"

    def type_label(self):
        if self.type == "other" and self.type_custom_label:
            return self.type_custom_label
        return self.get_type_display()

    def material_label(self):
        if self.material == "other" and self.material_custom_label:
            return self.material_custom_label
        return self.get_material_display()

    def weight_troy_oz(self):
        return float(self.weight_grams) / GRAMS_PER_TROY_OUNCE

    def default_irpf_group(self):
        if self.type == "bar" and self.material == "gold":
            return "04"
        return "05"

    def default_irpf_code(self):
        if self.type == "bar" and self.material == "gold":
            return "01"
        return "01"

    def effective_irpf_group(self):
        return self.irpf_group or self.default_irpf_group()

    def effective_irpf_code(self):
        return self.irpf_code or self.default_irpf_code()

    def default_description_irpf(self):
        parts = [f"{self.type_label()} de {self.material_label()}"]
        if self.purity_percentage:
            parts.append(f"pureza {self.purity_percentage}%")
        if self.weight_grams:
            parts.append(f"peso {self.weight_grams} g")
        if self.serial_number:
            parts.append(f"série {self.serial_number}")
        if self.invoice_number:
            parts.append(f"NF {self.invoice_number}")
        return ", ".join(parts)


class MetalPhoto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metal = models.ForeignKey(Metal, on_delete=models.CASCADE, related_name="extra_photos")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField("Foto", upload_to="metals/extra_photos/")
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "created_at"]


class Banknote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="banknotes")
    currency = models.CharField("Moeda", max_length=10, choices=BanknoteCurrency.choices, default=BanknoteCurrency.USD)
    currency_custom_label = models.CharField("Moeda personalizada", max_length=100, blank=True, default="")
    denomination = models.DecimalField("Valor de face", max_digits=14, decimal_places=2)
    quantity = models.PositiveIntegerField("Quantidade", default=1)
    acquisition_value = models.DecimalField("Valor de aquisição (R$)", max_digits=14, decimal_places=2)
    acquisition_date = models.DateField("Data de aquisição")
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name="banknotes")
    serial_number = models.CharField("Número de série", max_length=200, blank=True, default="")
    notes = models.TextField("Observações", blank=True, default="")
    # IRPF fields
    description = models.TextField("Descrição IRPF", blank=True, default="")
    vendor_name = models.CharField("Nome do vendedor", max_length=300, blank=True, default="")
    vendor_document = models.CharField("CPF/CNPJ do vendedor", max_length=20, blank=True, default="")
    sold_date = models.DateField("Data de venda", null=True, blank=True)
    sold_value = models.DecimalField("Valor de venda", max_digits=14, decimal_places=2, null=True, blank=True)
    irpf_group = models.CharField("Grupo IRPF", max_length=10, blank=True, default="")
    irpf_code = models.CharField("Código IRPF", max_length=10, blank=True, default="")
    irpf_include_override = models.BooleanField("Incluir no IRPF", null=True, blank=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_currency_display()} - {self.denomination}"

    def currency_label(self):
        if self.currency == "other" and self.currency_custom_label:
            return self.currency_custom_label
        return self.get_currency_display()

    def default_irpf_group(self):
        if self.currency != "brl":
            return "06"
        return "05"

    def default_irpf_code(self):
        if self.currency != "brl":
            return "02"
        return "01"

    def effective_irpf_group(self):
        return self.irpf_group or self.default_irpf_group()

    def effective_irpf_code(self):
        return self.irpf_code or self.default_irpf_code()

    def default_description_irpf(self):
        parts = [f"Cédula de {self.currency_label()}, valor de face {self.denomination}", f"quantidade {self.quantity}"]
        if self.serial_number:
            parts.append(f"série {self.serial_number}")
        return ", ".join(parts)
