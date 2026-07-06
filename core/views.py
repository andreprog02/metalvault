import json
import csv
import io
from collections import defaultdict
from decimal import Decimal
from datetime import date

import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Count

from django.db import models as db_models
from .models import Metal, Banknote, Location, MetalPhoto, Coin, GRAMS_PER_TROY_OUNCE
from .forms import SignUpForm, LoginForm, MetalForm, BanknoteForm, LocationForm, IrpfEditForm, CoinForm


# ---------- AUTH ----------

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("dashboard")
        messages.error(request, "E-mail ou senha incorretos.")
    else:
        form = LoginForm()
    return render(request, "core/login.html", {"form": form, "mode": "signin"})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Conta criada com sucesso!")
            return redirect("dashboard")
    else:
        form = SignUpForm()
    return render(request, "core/login.html", {"form": form, "mode": "signup"})


def logout_view(request):
    logout(request)
    return redirect("login")


# ---------- DASHBOARD ----------

@login_required
def dashboard(request):
    metals = Metal.objects.filter(user=request.user)
    coins = Coin.objects.filter(user=request.user)
    total_items = metals.count() + coins.count()
    total_value = (metals.aggregate(s=Sum("acquisition_value"))["s"] or 0) + (coins.aggregate(s=Sum("acquisition_value"))["s"] or 0)
    total_grams = (metals.aggregate(s=Sum("weight_grams"))["s"] or 0) + (coins.aggregate(s=Sum("weight_grams"))["s"] or 0)

    by_material = defaultdict(lambda: {"grams": Decimal(0), "value": Decimal(0), "count": 0, "label": "", "key": ""})
    for m in metals:
        label = m.material_label()
        by_material[label]["grams"] += m.weight_grams
        by_material[label]["value"] += m.acquisition_value
        by_material[label]["count"] += 1
        by_material[label]["label"] = label
        by_material[label]["key"] = m.material
    for c in coins:
        label = c.metal_label()
        by_material[label]["grams"] += c.weight_grams
        by_material[label]["value"] += c.acquisition_value
        by_material[label]["count"] += 1
        by_material[label]["label"] = label
        by_material[label]["key"] = c.metal

    chart_data = []
    for d in by_material.values():
        avg_per_gram = float(d["value"]) / float(d["grams"]) if d["grams"] > 0 else 0
        chart_data.append({
            "name": d["label"],
            "key": d["key"],
            "grams": float(d["grams"]),
            "value": float(d["value"]),
            "avg_per_gram": round(avg_per_gram, 2),
        })

    return render(request, "core/dashboard.html", {
        "total_items": total_items,
        "total_value": total_value,
        "total_grams": total_grams,
        "materials_count": len(by_material),
        "by_material": dict(by_material),
        "chart_data": json.dumps(chart_data),
        "metal_count": metals.count(),
        "coin_count": coins.count(),
    })


# ---------- MARKET QUOTES API ----------

@login_required
def api_quotes(request):
    try:
        r = requests.get("https://economia.awesomeapi.com.br/json/last/USD-BRL,XAU-BRL,XAG-BRL", timeout=10)
        r.raise_for_status()
        return JsonResponse(r.json())
    except Exception:
        return JsonResponse({"error": "Falha ao obter cotações"}, status=500)


@login_required
def api_valuation(request):
    """Returns inventory valuation data as JSON."""
    try:
        r = requests.get("https://economia.awesomeapi.com.br/json/last/XAU-BRL,XAG-BRL", timeout=10)
        r.raise_for_status()
        quotes = r.json()
    except Exception:
        quotes = {}

    gold_per_gram = float(quotes.get("XAUBRL", {}).get("bid", 0)) / GRAMS_PER_TROY_OUNCE if "XAUBRL" in quotes else 0
    silver_per_gram = float(quotes.get("XAGBRL", {}).get("bid", 0)) / GRAMS_PER_TROY_OUNCE if "XAGBRL" in quotes else 0
    spots = {"gold": gold_per_gram, "silver": silver_per_gram, "platinum": 0, "other": 0}

    metals = Metal.objects.filter(user=request.user)
    groups = defaultdict(lambda: {"label": "", "key": "", "grams": 0, "pure_grams": 0, "acquisition": 0, "current": 0, "has_price": False, "items": 0})

    for m in metals:
        label = m.material_label()
        g = float(m.weight_grams)
        purity = float(m.purity_percentage) / 100
        pure = g * purity
        price = spots.get(m.material, 0)
        current = pure * price

        groups[label]["label"] = label
        groups[label]["key"] = m.material
        groups[label]["grams"] += g
        groups[label]["pure_grams"] += pure
        groups[label]["acquisition"] += float(m.acquisition_value)
        groups[label]["current"] += current
        groups[label]["has_price"] = price > 0
        groups[label]["items"] += 1

    rows = list(groups.values())
    total_acq = sum(r["acquisition"] for r in rows)
    total_cur = sum(r["current"] for r in rows)

    for r in rows:
        r["spot_per_gram"] = spots.get(r["key"], 0)

    return JsonResponse({
        "rows": rows,
        "total_acquisition": total_acq,
        "total_current": total_cur,
        "spots": spots,
    })


@login_required
def api_purchase_vs_market(request):
    """Returns each metal purchase with price/gram paid and market price/gram on that date."""
    metals = Metal.objects.filter(user=request.user).order_by("acquisition_date")
    if not metals.exists():
        return JsonResponse({"purchases": []})

    # Build purchase data
    purchases = []
    for m in metals:
        purity = float(m.purity_percentage) / 100 if m.purity_percentage else 1
        pure_grams = float(m.weight_grams) * purity if m.weight_grams else 0
        price_per_gram_raw = float(m.acquisition_value) / float(m.weight_grams) if m.weight_grams > 0 else 0
        price_per_pure_gram = float(m.acquisition_value) / pure_grams if pure_grams > 0 else 0
        purchases.append({
            "id": str(m.pk),
            "date": m.acquisition_date.strftime("%Y-%m-%d"),
            "date_label": m.acquisition_date.strftime("%d/%m/%Y"),
            "material": m.material,
            "material_label": m.material_label(),
            "type_label": m.type_label(),
            "weight_grams": float(m.weight_grams),
            "pure_grams": round(pure_grams, 4),
            "purity": round(purity * 100, 2),
            "acquisition_value": float(m.acquisition_value),
            "price_per_gram": round(price_per_gram_raw, 2),
            "price_per_pure_gram": round(price_per_pure_gram, 2),
            "serial_number": m.serial_number or "",
        })

    # Fetch historical market prices for each unique (material, date)
    material_api_map = {"gold": "XAU-BRL", "silver": "XAG-BRL", "platinum": "XPT-BRL"}
    unique_queries = set()
    for p in purchases:
        if p["material"] in material_api_map:
            unique_queries.add((p["material"], p["date"]))

    # Fetch from AwesomeAPI daily endpoint
    market_prices = {}  # (material, date_str) -> price_per_gram
    for material, date_str in unique_queries:
        api_pair = material_api_map.get(material)
        if not api_pair:
            continue
        try:
            dt = date_str.replace("-", "")
            # Fetch a small range around the date (±3 days) to handle weekends/holidays
            from datetime import timedelta, datetime as dt_class
            d = dt_class.strptime(date_str, "%Y-%m-%d")
            start = (d - timedelta(days=5)).strftime("%Y%m%d")
            end = (d + timedelta(days=1)).strftime("%Y%m%d")
            url = f"https://economia.awesomeapi.com.br/json/daily/{api_pair}?start_date={start}&end_date={end}"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data and isinstance(data, list) and len(data) > 0:
                    # Get closest date (data comes sorted by most recent first)
                    bid = float(data[0].get("bid", 0))
                    price_per_gram = bid / GRAMS_PER_TROY_OUNCE if bid > 0 else 0
                    market_prices[(material, date_str)] = round(price_per_gram, 2)
        except Exception:
            pass

    # Also get current spot prices for reference
    try:
        r = requests.get("https://economia.awesomeapi.com.br/json/last/XAU-BRL,XAG-BRL", timeout=10)
        if r.status_code == 200:
            quotes = r.json()
            current_spots = {}
            if "XAUBRL" in quotes:
                current_spots["gold"] = round(float(quotes["XAUBRL"]["bid"]) / GRAMS_PER_TROY_OUNCE, 2)
            if "XAGBRL" in quotes:
                current_spots["silver"] = round(float(quotes["XAGBRL"]["bid"]) / GRAMS_PER_TROY_OUNCE, 2)
        else:
            current_spots = {}
    except Exception:
        current_spots = {}

    # Attach market price to each purchase
    for p in purchases:
        key = (p["material"], p["date"])
        p["market_price_per_gram"] = market_prices.get(key)
        p["current_spot_per_gram"] = current_spots.get(p["material"])

    return JsonResponse({"purchases": purchases, "current_spots": current_spots})


# ---------- INVENTORY ----------

@login_required
def inventory(request):
    tab = request.GET.get("tab", "metals")
    metals = Metal.objects.filter(user=request.user).select_related("location")
    banknotes = Banknote.objects.filter(user=request.user).select_related("location")
    coins = Coin.objects.filter(user=request.user).select_related("location")
    locations = Location.objects.filter(user=request.user)

    # Filters
    q = request.GET.get("q", "")
    material_filter = request.GET.get("material", "all")
    type_filter = request.GET.get("type", "all")
    location_filter = request.GET.get("location", "all")

    if q:
        metals = metals.filter(
            db_models.Q(serial_number__icontains=q) |
            db_models.Q(invoice_number__icontains=q) |
            db_models.Q(type_custom_label__icontains=q) |
            db_models.Q(material_custom_label__icontains=q)
        )
    if material_filter != "all":
        metals = metals.filter(material=material_filter)
    if type_filter != "all":
        metals = metals.filter(type=type_filter)
    if location_filter != "all":
        metals = metals.filter(location_id=location_filter)

    return render(request, "core/inventory.html", {
        "metals": metals,
        "banknotes": banknotes,
        "coins": coins,
        "locations": locations,
        "tab": tab,
        "q": q,
        "material_filter": material_filter,
        "type_filter": type_filter,
        "location_filter": location_filter,
    })


# ---------- METALS CRUD ----------

@login_required
def metal_create(request):
    if request.method == "POST":
        form = MetalForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            metal = form.save(commit=False)
            metal.user = request.user
            metal.save()
            # Handle extra photos
            for f in request.FILES.getlist("extra_photos"):
                MetalPhoto.objects.create(metal=metal, user=request.user, image=f, sort_order=metal.extra_photos.count())
            messages.success(request, "Metal cadastrado com sucesso!")
            return redirect("metal_detail", pk=metal.pk)
    else:
        form = MetalForm(user=request.user)
    return render(request, "core/metal_form.html", {"form": form, "is_edit": False})


@login_required
def metal_edit(request, pk):
    metal = get_object_or_404(Metal, pk=pk, user=request.user)
    if request.method == "POST":
        form = MetalForm(request.POST, request.FILES, instance=metal, user=request.user)
        if form.is_valid():
            form.save()
            for f in request.FILES.getlist("extra_photos"):
                MetalPhoto.objects.create(metal=metal, user=request.user, image=f, sort_order=metal.extra_photos.count())
            messages.success(request, "Metal atualizado!")
            return redirect("metal_detail", pk=metal.pk)
    else:
        form = MetalForm(instance=metal, user=request.user)
    return render(request, "core/metal_form.html", {"form": form, "is_edit": True, "metal": metal})


@login_required
def metal_detail(request, pk):
    metal = get_object_or_404(Metal, pk=pk, user=request.user)
    extra_photos = metal.extra_photos.all()
    return render(request, "core/metal_detail.html", {"metal": metal, "extra_photos": extra_photos})


@login_required
def metal_delete(request, pk):
    metal = get_object_or_404(Metal, pk=pk, user=request.user)
    if request.method == "POST":
        metal.delete()
        messages.success(request, "Metal removido.")
        return redirect("inventory")
    return redirect("metal_detail", pk=pk)


# ---------- BANKNOTES CRUD ----------

@login_required
def banknote_create(request):
    if request.method == "POST":
        form = BanknoteForm(request.POST, user=request.user)
        if form.is_valid():
            b = form.save(commit=False)
            b.user = request.user
            b.save()
            messages.success(request, "Cédula cadastrada!")
            return redirect("inventory") if "next" not in request.GET else redirect(request.GET["next"])
    else:
        form = BanknoteForm(user=request.user)
    return render(request, "core/banknote_form.html", {"form": form, "is_edit": False})


@login_required
def banknote_edit(request, pk):
    banknote = get_object_or_404(Banknote, pk=pk, user=request.user)
    if request.method == "POST":
        form = BanknoteForm(request.POST, instance=banknote, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Cédula atualizada!")
            return redirect("inventory")
    else:
        form = BanknoteForm(instance=banknote, user=request.user)
    return render(request, "core/banknote_form.html", {"form": form, "is_edit": True, "banknote": banknote})


@login_required
def banknote_delete(request, pk):
    banknote = get_object_or_404(Banknote, pk=pk, user=request.user)
    if request.method == "POST":
        banknote.delete()
        messages.success(request, "Cédula removida.")
    return redirect("inventory")


# ---------- LOCATIONS ----------

@login_required
def locations(request):
    locs = Location.objects.filter(user=request.user).annotate(
        metal_count_val=Count("metals", distinct=True),
        banknote_count_val=Count("banknotes", distinct=True),
        total_metal_value=Sum("metals__acquisition_value"),
        total_metal_grams=Sum("metals__weight_grams"),
    )
    return render(request, "core/locations.html", {"locations": locs})


@login_required
def location_create(request):
    if request.method == "POST":
        form = LocationForm(request.POST)
        if form.is_valid():
            loc = form.save(commit=False)
            loc.user = request.user
            loc.save()
            messages.success(request, "Local criado!")
            return redirect("locations")
    else:
        form = LocationForm()
    return render(request, "core/location_form.html", {"form": form, "is_edit": False})


@login_required
def location_edit(request, pk):
    loc = get_object_or_404(Location, pk=pk, user=request.user)
    if request.method == "POST":
        form = LocationForm(request.POST, instance=loc)
        if form.is_valid():
            form.save()
            messages.success(request, "Local atualizado!")
            return redirect("locations")
    else:
        form = LocationForm(instance=loc)
    return render(request, "core/location_form.html", {"form": form, "is_edit": True, "location": loc})


@login_required
def location_delete(request, pk):
    loc = get_object_or_404(Location, pk=pk, user=request.user)
    if request.method == "POST":
        if loc.metals.exists():
            messages.error(request, f"Não é possível excluir: {loc.metals.count()} metais associados.")
        else:
            loc.delete()
            messages.success(request, "Local removido.")
    return redirect("locations")


# ---------- IRPF REPORT ----------

def _format_brl(val):
    try:
        n = Decimal(str(val))
        return f"R$ {n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def _format_date_br(d):
    if not d:
        return "—"
    return d.strftime("%d/%m/%Y")


def _situation_on_dec31(item, year):
    acq_year = item["acquisition_date"].year
    if acq_year > year:
        return Decimal(0)
    if item["sold_date"]:
        sold_year = item["sold_date"].year
        if sold_year <= year:
            return Decimal(0)
    return item["acquisition_value"]


def _build_discrimination(item):
    desc = item["description"] or item["default_description"]
    parts = [f"{desc}."]
    seller = []
    if item["vendor_name"]:
        seller.append(f"Vendedor: {item['vendor_name']}")
    if item["vendor_document"]:
        seller.append(f"CPF/CNPJ: {item['vendor_document']}")
    if seller:
        parts.append(f" {' - '.join(seller)}.")
    parts.append(f" Adquirido em {_format_date_br(item['acquisition_date'])} pelo valor de {_format_brl(item['acquisition_value'])}.")
    if item["sold_date"]:
        sold_str = f" Bem alienado em {_format_date_br(item['sold_date'])}"
        if item["sold_value"] is not None:
            sold_str += f" pelo valor de {_format_brl(item['sold_value'])}"
        sold_str += "."
        parts.append(sold_str)
    return " ".join(parts).strip()


def _build_irpf_items(user):
    items = []
    for m in Metal.objects.filter(user=user):
        items.append({
            "id": str(m.pk),
            "source": "metal",
            "obj": m,
            "default_description": m.default_description_irpf(),
            "description": m.description,
            "vendor_name": m.vendor_name,
            "vendor_document": m.vendor_document,
            "acquisition_date": m.acquisition_date,
            "acquisition_value": m.acquisition_value,
            "sold_date": m.sold_date,
            "sold_value": m.sold_value,
            "irpf_group": m.effective_irpf_group(),
            "irpf_code": m.effective_irpf_code(),
            "include_override": m.irpf_include_override,
            "is_precious_metal": m.type == "bar",
        })
    for b in Banknote.objects.filter(user=user):
        items.append({
            "id": str(b.pk),
            "source": "banknote",
            "obj": b,
            "default_description": b.default_description_irpf(),
            "description": b.description,
            "vendor_name": b.vendor_name,
            "vendor_document": b.vendor_document,
            "acquisition_date": b.acquisition_date,
            "acquisition_value": b.acquisition_value,
            "sold_date": b.sold_date,
            "sold_value": b.sold_value,
            "irpf_group": b.effective_irpf_group(),
            "irpf_code": b.effective_irpf_code(),
            "include_override": b.irpf_include_override,
            "is_precious_metal": False,
        })
    return items


@login_required
def irpf_report(request):
    current_year = date.today().year
    year = int(request.GET.get("year", current_year - 1))
    include_metals = request.GET.get("include_metals", "1") == "1"
    show_small = request.GET.get("show_small", "0") == "1"
    min_value = Decimal("5000")

    items = _build_irpf_items(request.user)
    filtered = []
    for it in items:
        if not include_metals and it["is_precious_metal"]:
            continue
        prev = _situation_on_dec31(it, year - 1)
        curr = _situation_on_dec31(it, year)
        sold_in_year = it["sold_date"] and it["sold_date"].year == year
        if prev == 0 and curr == 0 and not sold_in_year:
            continue
        if it["include_override"] is False:
            continue
        if it["include_override"] is True:
            pass
        elif it["acquisition_value"] < min_value and not show_small:
            continue
        it["prev_value"] = prev
        it["curr_value"] = curr
        it["sold_in_year"] = sold_in_year
        it["discrimination"] = _build_discrimination(it)
        filtered.append(it)

    total_prev = sum(it["prev_value"] for it in filtered)
    total_curr = sum(it["curr_value"] for it in filtered)
    years = list(range(current_year, current_year - 6, -1))

    return render(request, "core/irpf.html", {
        "items": filtered,
        "year": year,
        "years": years,
        "include_metals": include_metals,
        "show_small": show_small,
        "total_prev": total_prev,
        "total_curr": total_curr,
    })


@login_required
def irpf_edit(request, source, pk):
    if source == "metal":
        obj = get_object_or_404(Metal, pk=pk, user=request.user)
    else:
        obj = get_object_or_404(Banknote, pk=pk, user=request.user)

    if request.method == "POST":
        form = IrpfEditForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            obj.description = d["description"]
            obj.irpf_group = d["irpf_group"]
            obj.irpf_code = d["irpf_code"]
            obj.vendor_name = d["vendor_name"]
            obj.vendor_document = d["vendor_document"]
            obj.sold_date = d["sold_date"]
            obj.sold_value = d["sold_value"]
            override = d["irpf_include_override"]
            obj.irpf_include_override = None if override == "auto" else (override == "always")
            obj.save()
            messages.success(request, "Dados IRPF atualizados!")
            return redirect("irpf_report")
    else:
        override_val = "auto"
        if obj.irpf_include_override is True:
            override_val = "always"
        elif obj.irpf_include_override is False:
            override_val = "never"
        form = IrpfEditForm(initial={
            "description": obj.description,
            "irpf_group": obj.irpf_group,
            "irpf_code": obj.irpf_code,
            "vendor_name": obj.vendor_name,
            "vendor_document": obj.vendor_document,
            "sold_date": obj.sold_date,
            "sold_value": obj.sold_value,
            "irpf_include_override": override_val,
        })
    return render(request, "core/irpf_edit.html", {"form": form, "source": source, "obj": obj})


@login_required
def irpf_export_csv(request):
    year = int(request.GET.get("year", date.today().year - 1))
    include_metals = request.GET.get("include_metals", "1") == "1"
    show_small = request.GET.get("show_small", "0") == "1"
    min_value = Decimal("5000")

    items = _build_irpf_items(request.user)
    filtered = []
    for it in items:
        if not include_metals and it["is_precious_metal"]:
            continue
        prev = _situation_on_dec31(it, year - 1)
        curr = _situation_on_dec31(it, year)
        sold_in_year = it["sold_date"] and it["sold_date"].year == year
        if prev == 0 and curr == 0 and not sold_in_year:
            continue
        if it["include_override"] is False:
            continue
        if it["include_override"] is True:
            pass
        elif it["acquisition_value"] < min_value and not show_small:
            continue
        it["prev_value"] = prev
        it["curr_value"] = curr
        it["discrimination"] = _build_discrimination(it)
        filtered.append(it)

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="IRPF_{year}.csv"'
    response.write("\ufeff")  # BOM
    writer = csv.writer(response, delimiter=";")
    writer.writerow(["Grupo", "Código", "Discriminação", f"Situação 31/12/{year-1}", f"Situação 31/12/{year}",
                      "Data aquisição", "Valor aquisição", "Data venda", "Valor venda", "Vendedor", "CPF/CNPJ vendedor"])
    for it in filtered:
        writer.writerow([
            it["irpf_group"], it["irpf_code"], it["discrimination"],
            str(it["prev_value"]).replace(".", ","), str(it["curr_value"]).replace(".", ","),
            _format_date_br(it["acquisition_date"]),
            str(it["acquisition_value"]).replace(".", ","),
            _format_date_br(it["sold_date"]) if it["sold_date"] else "",
            str(it["sold_value"]).replace(".", ",") if it["sold_value"] is not None else "",
            it["vendor_name"] or "", it["vendor_document"] or "",
        ])
    return response


# ---------- COINS CRUD ----------

@login_required
def coin_create(request):
    if request.method == "POST":
        form = CoinForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            coin = form.save(commit=False)
            coin.user = request.user
            coin.save()
            messages.success(request, "Moeda cadastrada com sucesso!")
            return redirect("coin_detail", pk=coin.pk)
    else:
        form = CoinForm(user=request.user)
    return render(request, "core/coin_form.html", {"form": form, "is_edit": False})


@login_required
def coin_edit(request, pk):
    coin = get_object_or_404(Coin, pk=pk, user=request.user)
    if request.method == "POST":
        form = CoinForm(request.POST, request.FILES, instance=coin, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Moeda atualizada!")
            return redirect("coin_detail", pk=coin.pk)
    else:
        form = CoinForm(instance=coin, user=request.user)
    return render(request, "core/coin_form.html", {"form": form, "is_edit": True, "coin": coin})


@login_required
def coin_detail(request, pk):
    coin = get_object_or_404(Coin, pk=pk, user=request.user)
    return render(request, "core/coin_detail.html", {"coin": coin})


@login_required
def coin_delete(request, pk):
    coin = get_object_or_404(Coin, pk=pk, user=request.user)
    if request.method == "POST":
        coin.delete()
        messages.success(request, "Moeda removida.")
        return redirect("inventory")
    return redirect("coin_detail", pk=pk)


@login_required
def api_countries(request):
    """Returns country-continent mapping as JSON."""
    from .countries import COUNTRIES, CONTINENTS
    return JsonResponse({
        "countries": [{"code": c, "name": n, "continent": ct} for c, n, ct in COUNTRIES],
        "continents": CONTINENTS,
    })
