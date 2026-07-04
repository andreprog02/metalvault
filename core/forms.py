from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Metal, Banknote, Location


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
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class MetalForm(forms.ModelForm):
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
            "type_custom_label": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Pingente"}),
            "material": forms.Select(attrs={"class": "form-select", "id": "id_material"}),
            "material_custom_label": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Paládio"}),
            "serial_number": forms.TextInput(attrs={"class": "form-control"}),
            "invoice_number": forms.TextInput(attrs={"class": "form-control"}),
            "purity_percentage": forms.NumberInput(attrs={"class": "form-control", "step": "0.001", "min": "0", "max": "100"}),
            "weight_grams": forms.NumberInput(attrs={"class": "form-control", "step": "0.0001", "min": "0"}),
            "acquisition_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "acquisition_value": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
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


class BanknoteForm(forms.ModelForm):
    class Meta:
        model = Banknote
        fields = (
            "currency", "currency_custom_label", "denomination", "quantity",
            "acquisition_value", "acquisition_date", "location", "serial_number", "notes",
        )
        widgets = {
            "currency": forms.Select(attrs={"class": "form-select"}),
            "currency_custom_label": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nome da moeda"}),
            "denomination": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "acquisition_value": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "acquisition_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "location": forms.Select(attrs={"class": "form-select"}),
            "serial_number": forms.TextInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields["location"].queryset = Location.objects.filter(user=user)
        self.fields["location"].required = False
        self.fields["location"].empty_label = "Nenhum"


class IrpfEditForm(forms.Form):
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}))
    irpf_group = forms.CharField(required=False, max_length=10, widget=forms.TextInput(attrs={"class": "form-control"}))
    irpf_code = forms.CharField(required=False, max_length=10, widget=forms.TextInput(attrs={"class": "form-control"}))
    vendor_name = forms.CharField(required=False, max_length=300, widget=forms.TextInput(attrs={"class": "form-control"}))
    vendor_document = forms.CharField(required=False, max_length=20, widget=forms.TextInput(attrs={"class": "form-control"}))
    sold_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))
    sold_value = forms.DecimalField(required=False, max_digits=14, decimal_places=2, widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}))
    irpf_include_override = forms.ChoiceField(
        choices=[("auto", "Automático (regra de R$ 5.000)"), ("always", "Sempre incluir"), ("never", "Nunca incluir")],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
