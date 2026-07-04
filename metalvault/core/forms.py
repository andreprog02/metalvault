import re
from decimal import Decimal, InvalidOperation
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Metal, Banknote, Location


def parse_brl(value):
    """Parse BRL formatted string like '12.999,99' or '12999.99' to Decimal."""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    # Remove R$ prefix if present
    s = re.sub(r'^R\$\s*', '', s)
    # If has both . and , -> BRL format: 12.999,99
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    # If only comma -> treat as decimal separator: 999,99
    elif ',' in s:
        s = s.replace(',', '.')
    # else: already in 12999.99 format
    try:
        return Decimal(s)
    except InvalidOperation:
        raise forms.ValidationError("Informe um valor numérico válido. Ex: 12.999,99")


class BRLField(forms.CharField):
    """Text field that accepts BRL-formatted input and returns Decimal."""
    def __init__(self, *args, max_digits=14, decimal_places=2, min_value=None, **kwargs):
        self.max_digits = max_digits
        self.decimal_places = decimal_places
        self.min_value = min_value
        kwargs.setdefault('widget', forms.TextInput(attrs={
            "class": "form-control brl-input",
            "placeholder": "0,00",
            "inputmode": "decimal",
        }))
        super().__init__(*args, **kwargs)

    def clean(self, value):
        value = super().clean(value)
        if not value and not self.required:
            return None
        result = parse_brl(value)
        if result is None:
            if self.required:
                raise forms.ValidationError("Este campo é obrigatório.")
            return None
        if self.min_value is not None and result < self.min_value:
            raise forms.ValidationError(f"O valor deve ser maior ou igual a {self.min_value}.")
        return result


def format_brl_initial(value):
    """Format a Decimal value for display in BRL format."""
    if value is None:
        return ""
    try:
        n = Decimal(str(value))
        formatted = f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return formatted
    except:
        return str(value)


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "seu@email.com"}))

    class Meta:
        model = User
        fields = ("email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.setdefault("class", "form-control")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "E-mail"
        self.fields["username"].widget = forms.EmailInput(attrs={"class": "form-control", "placeholder": "seu@email.com"})
        self.fields["password"].widget.attrs["class"] = "form-control"


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ("name", "description")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Cofre residencial"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Descrição opcional"}),
        }


class MetalForm(forms.ModelForm):
    acquisition_value = BRLField(
        label="Valor de aquisição",
        min_value=Decimal("0"),
        required=True,
    )

    class Meta:
        model = Metal
        fields = (
            "type", "type_custom_label", "material", "material_custom_label",
            "serial_number", "invoice_number", "purity_percentage", "weight_grams",
            "acquisition_date", "acquisition_value", "location",
            "photo", "certificate", "invoice_file",
        )
        widgets = {
            "type": forms.Select(attrs={"class": "form-select", "id": "id_type"}),
            "type_custom_label": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Pingente, Joia, Lingote"}),
            "material": forms.Select(attrs={"class": "form-select", "id": "id_material"}),
            "material_custom_label": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Paládio, Ródio, Cobre"}),
            "serial_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: ABC-123456"}),
            "invoice_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: 001234"}),
            "purity_percentage": forms.NumberInput(attrs={"class": "form-control", "step": "0.001", "min": "0", "max": "100", "placeholder": "99,900"}),
            "weight_grams": forms.NumberInput(attrs={"class": "form-control", "step": "0.0001", "min": "0", "placeholder": "31,1035"}),
            "acquisition_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "location": forms.Select(attrs={"class": "form-select"}),
            "photo": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "certificate": forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".pdf,image/*"}),
            "invoice_file": forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".pdf,image/*"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields["location"].queryset = Location.objects.filter(user=user)
        self.fields["location"].required = False
        self.fields["location"].empty_label = "Nenhum"
        # Format initial value for BRL display
        if self.instance and self.instance.pk and self.instance.acquisition_value is not None:
            self.initial["acquisition_value"] = format_brl_initial(self.instance.acquisition_value)


class BanknoteForm(forms.ModelForm):
    acquisition_value = BRLField(
        label="Valor de aquisição (R$)",
        min_value=Decimal("0"),
        required=True,
    )

    class Meta:
        model = Banknote
        fields = (
            "currency", "currency_custom_label", "denomination", "quantity",
            "acquisition_value", "acquisition_date", "location", "serial_number", "notes",
        )
        widgets = {
            "currency": forms.Select(attrs={"class": "form-select"}),
            "currency_custom_label": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nome da moeda"}),
            "denomination": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "100,00"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": "1", "placeholder": "1"}),
            "acquisition_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "location": forms.Select(attrs={"class": "form-select"}),
            "serial_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Opcional"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Observações opcionais"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields["location"].queryset = Location.objects.filter(user=user)
        self.fields["location"].required = False
        self.fields["location"].empty_label = "Nenhum"
        if self.instance and self.instance.pk and self.instance.acquisition_value is not None:
            self.initial["acquisition_value"] = format_brl_initial(self.instance.acquisition_value)


class IrpfEditForm(forms.Form):
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}))
    irpf_group = forms.CharField(required=False, max_length=10, widget=forms.TextInput(attrs={"class": "form-control"}))
    irpf_code = forms.CharField(required=False, max_length=10, widget=forms.TextInput(attrs={"class": "form-control"}))
    vendor_name = forms.CharField(required=False, max_length=300, widget=forms.TextInput(attrs={"class": "form-control"}))
    vendor_document = forms.CharField(required=False, max_length=20, widget=forms.TextInput(attrs={"class": "form-control"}))
    sold_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))
    sold_value = BRLField(label="Valor da venda (R$)", required=False, min_value=Decimal("0"))
    irpf_include_override = forms.ChoiceField(
        choices=[("auto", "Automático (regra de R$ 5.000)"), ("always", "Sempre incluir"), ("never", "Nunca incluir")],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
