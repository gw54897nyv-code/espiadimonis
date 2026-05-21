import json
from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum
from .models import Factura, Despesa, Client, Producte, PARTIDES, FacturaProveidor
from .forms import FacturaForm, LineaFormSet, DespesaForm, DespesaSociForm, RevisarDespesaForm, ClientForm, ProducteForm, FacturaProveidorForm


def _json_productes():
    return json.dumps([
        {
            'id': p.id,
            'nom': p.nom,
            'descripcio': p.descripcio or p.nom,
            'preu_unitari': float(p.preu_unitari),
            'iva': float(p.iva),
        }
        for p in Producte.objects.filter(actiu=True)
    ])


def _json_clients():
    return json.dumps([
        {
            'id': c.id,
            'nom': c.nom,
            'nif': c.nif,
            'adreca': c.adreca,
        }
        for c in Client.objects.all()
    ])
from .pdf import generar_pdf_factura
from accounts.decorators import requereix_junta


# ── Factures ──────────────────────────────────────────────────────────────────

@login_required
@requereix_junta
def llista_factures(request):
    filtre_tipus   = request.GET.get('tipus', '')
    filtre_estat   = request.GET.get('estat', '')
    filtre_partida = request.GET.get('partida', '')
    factures = Factura.objects.prefetch_related('linies')
    if filtre_tipus:
        factures = factures.filter(tipus=filtre_tipus)
    if filtre_estat:
        factures = factures.filter(estat=filtre_estat)
    if filtre_partida:
        factures = factures.filter(partida=filtre_partida)
    return render(request, 'facturacio/llista.html', {
        'factures': factures,
        'filtre_tipus': filtre_tipus,
        'filtre_estat': filtre_estat,
        'filtre_partida': filtre_partida,
    })


@login_required
@requereix_junta
def detall_factura(request, pk):
    factura = get_object_or_404(Factura, pk=pk)
    return render(request, 'facturacio/detall.html', {'factura': factura})


@login_required
@requereix_junta
def crear_factura(request):
    if request.method == 'POST':
        form = FacturaForm(request.POST)
        formset = LineaFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            factura = form.save()
            formset.instance = factura
            formset.save()
            messages.success(request, f'Factura {factura.numero} creada.')
            return redirect('detall_factura', pk=factura.pk)
    else:
        form = FacturaForm(initial={
            'data': timezone.now().date(),
            'numero': _seguent_numero_factura(),
        })
        formset = LineaFormSet()
    return render(request, 'facturacio/formulari.html', {
        'form': form, 'formset': formset, 'accio': 'Crear',
        'productes_json': _json_productes(), 'clients_json': _json_clients(),
    })


@login_required
@requereix_junta
def editar_factura(request, pk):
    factura = get_object_or_404(Factura, pk=pk)
    if request.method == 'POST':
        form = FacturaForm(request.POST, instance=factura)
        formset = LineaFormSet(request.POST, instance=factura)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Factura actualitzada.')
            return redirect('detall_factura', pk=factura.pk)
    else:
        form = FacturaForm(instance=factura)
        formset = LineaFormSet(instance=factura)
    return render(request, 'facturacio/formulari.html', {
        'form': form, 'formset': formset, 'accio': 'Editar', 'factura': factura,
        'productes_json': _json_productes(), 'clients_json': _json_clients(),
    })


@login_required
@requereix_junta
def canvi_estat_factura(request, pk):
    factura = get_object_or_404(Factura, pk=pk)
    if request.method == 'POST':
        nou_estat = request.POST.get('estat')
        if nou_estat in dict(Factura.ESTAT_CHOICES):
            factura.estat = nou_estat
            factura.save(update_fields=['estat'])
    return redirect('llista_factures')


@login_required
@requereix_junta
def eliminar_factura(request, pk):
    factura = get_object_or_404(Factura, pk=pk)
    if request.method == 'POST':
        num = factura.numero
        factura.delete()
        messages.success(request, f'Factura {num} eliminada.')
        return redirect('llista_factures')
    return render(request, 'facturacio/confirmar_eliminar.html', {'factura': factura})


@login_required
@requereix_junta
def pdf_factura(request, pk):
    factura = get_object_or_404(Factura, pk=pk)
    return generar_pdf_factura(factura)


# ── Clients ───────────────────────────────────────────────────────────────────

@login_required
@requereix_junta
def llista_clients(request):
    clients = Client.objects.all()
    return render(request, 'facturacio/clients/llista.html', {'clients': clients})


@login_required
@requereix_junta
def crear_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, f'Client {client.nom} creat.')
            return redirect('llista_clients')
    else:
        form = ClientForm()
    return render(request, 'facturacio/clients/formulari.html', {'form': form, 'accio': 'Crear'})


@login_required
@requereix_junta
def editar_client(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Client actualitzat.')
            return redirect('llista_clients')
    else:
        form = ClientForm(instance=client)
    return render(request, 'facturacio/clients/formulari.html', {'form': form, 'accio': 'Editar', 'client': client})


@login_required
@requereix_junta
def eliminar_client(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.delete()
        messages.success(request, 'Client eliminat.')
        return redirect('llista_clients')
    return render(request, 'facturacio/clients/confirmar_eliminar.html', {'client': client})


# ── Productes ─────────────────────────────────────────────────────────────────

@login_required
@requereix_junta
def llista_productes(request):
    productes = Producte.objects.all()
    return render(request, 'facturacio/productes/llista.html', {'productes': productes})


@login_required
@requereix_junta
def crear_producte(request):
    if request.method == 'POST':
        form = ProducteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producte creat.')
            return redirect('llista_productes')
    else:
        form = ProducteForm()
    return render(request, 'facturacio/productes/formulari.html', {'form': form, 'accio': 'Crear'})


@login_required
@requereix_junta
def editar_producte(request, pk):
    producte = get_object_or_404(Producte, pk=pk)
    if request.method == 'POST':
        form = ProducteForm(request.POST, instance=producte)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producte actualitzat.')
            return redirect('llista_productes')
    else:
        form = ProducteForm(instance=producte)
    return render(request, 'facturacio/productes/formulari.html', {'form': form, 'accio': 'Editar', 'producte': producte})


@login_required
@requereix_junta
def eliminar_producte(request, pk):
    producte = get_object_or_404(Producte, pk=pk)
    if request.method == 'POST':
        producte.delete()
        messages.success(request, 'Producte eliminat.')
        return redirect('llista_productes')
    return render(request, 'facturacio/productes/confirmar_eliminar.html', {'producte': producte})


# ── Despeses ──────────────────────────────────────────────────────────────────

@login_required
@requereix_junta
def llista_despeses(request):
    any_sel = int(request.GET.get('any', timezone.now().year))
    filtre_partida = request.GET.get('partida', '')
    filtre_estat = request.GET.get('estat', '')
    despeses = Despesa.objects.filter(data__year=any_sel).select_related('soci')
    if filtre_partida:
        despeses = despeses.filter(partida=filtre_partida)
    if filtre_estat:
        despeses = despeses.filter(estat=filtre_estat)
    total = despeses.aggregate(t=Sum('import_total'))['t'] or 0
    pendents = Despesa.objects.filter(estat=Despesa.ESTAT_PENDENT).count()
    return render(request, 'facturacio/despeses/llista.html', {
        'despeses': despeses, 'any_sel': any_sel, 'total': total,
        'filtre_partida': filtre_partida, 'filtre_estat': filtre_estat,
        'pendents': pendents, 'partides': PARTIDES, 'estats': Despesa.ESTATS,
    })


@login_required
@requereix_junta
def crear_despesa(request):
    if request.method == 'POST':
        form = DespesaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Despesa registrada.')
            return redirect('llista_despeses')
    else:
        form = DespesaForm(initial={'data': timezone.now().date()})
    return render(request, 'facturacio/despeses/formulari.html', {'form': form, 'accio': 'Crear'})


@login_required
@requereix_junta
def editar_despesa(request, pk):
    despesa = get_object_or_404(Despesa, pk=pk)
    if request.method == 'POST':
        form = DespesaForm(request.POST, request.FILES, instance=despesa)
        if form.is_valid():
            form.save()
            messages.success(request, 'Despesa actualitzada.')
            return redirect('llista_despeses')
    else:
        form = DespesaForm(instance=despesa)
    return render(request, 'facturacio/despeses/formulari.html', {'form': form, 'accio': 'Editar'})


@login_required
@requereix_junta
def eliminar_despesa(request, pk):
    despesa = get_object_or_404(Despesa, pk=pk)
    if request.method == 'POST':
        despesa.delete()
        messages.success(request, 'Despesa eliminada.')
        return redirect('llista_despeses')
    return render(request, 'facturacio/despeses/confirmar_eliminar.html', {'despesa': despesa})


@login_required
@requereix_junta
def revisar_despesa(request, pk):
    despesa = get_object_or_404(Despesa, pk=pk)
    if request.method == 'POST':
        form = RevisarDespesaForm(request.POST, instance=despesa)
        if form.is_valid():
            form.save()
            messages.success(request, 'Despesa revisada i classificada.')
            return redirect('llista_despeses')
    else:
        form = RevisarDespesaForm(instance=despesa)
    return render(request, 'facturacio/despeses/revisar.html', {'form': form, 'despesa': despesa})


@login_required
def registrar_despesa(request):
    if request.method == 'POST':
        form = DespesaSociForm(request.POST, request.FILES)
        if form.is_valid():
            despesa = form.save(commit=False)
            despesa.soci = request.user
            despesa.estat = Despesa.ESTAT_PENDENT
            despesa.save()
            messages.success(request, 'Despesa enviada. La junta directiva la revisarà aviat.')
            return redirect('les_meves_despeses')
    else:
        form = DespesaSociForm(initial={'data': timezone.now().date()})
    return render(request, 'facturacio/despeses/registrar.html', {'form': form})


@login_required
def les_meves_despeses(request):
    despeses = Despesa.objects.filter(soci=request.user).order_by('-data')
    return render(request, 'facturacio/despeses/meves.html', {'despeses': despeses})


# ── Dashboard ─────────────────────────────────────────────────────────────────

@login_required
@requereix_junta
def dashboard_facturacio(request):
    any_sel = int(request.GET.get('any', timezone.now().year))
    factures = list(
        Factura.objects.filter(tipus='FACTURA', data__year=any_sel).prefetch_related('linies')
    )
    despeses = Despesa.objects.filter(data__year=any_sel)

    total_facturat = sum(f.total() for f in factures)
    total_cobrat = sum(f.total() for f in factures if f.estat == 'PAGAT')
    total_pendent = sum(f.total() for f in factures if f.estat == 'PENDENT')
    total_despeses = despeses.aggregate(t=Sum('import_total'))['t'] or Decimal('0')
    balanc_general = total_cobrat - total_despeses

    partides_data = []
    for codi, nom in PARTIDES:
        facts_p = [f for f in factures if f.partida == codi]
        desp_p = despeses.filter(partida=codi).aggregate(t=Sum('import_total'))['t'] or Decimal('0')
        ingressos_p = sum(f.total() for f in facts_p)
        partides_data.append({
            'codi': codi,
            'nom': nom,
            'ingressos': ingressos_p,
            'despeses': desp_p,
            'balanc': ingressos_p - desp_p,
            'n_factures': len(facts_p),
        })

    pendents_despeses = Despesa.objects.filter(estat='PENDENT').count()
    recents = Factura.objects.filter(tipus='FACTURA').prefetch_related('linies').order_by('-data')[:8]

    anys_disponibles = sorted(set(
        list(Factura.objects.values_list('data__year', flat=True).distinct()) +
        list(Despesa.objects.values_list('data__year', flat=True).distinct())
    ), reverse=True)

    return render(request, 'facturacio/dashboard.html', {
        'any_sel': any_sel,
        'anys_disponibles': anys_disponibles,
        'total_facturat': total_facturat,
        'total_cobrat': total_cobrat,
        'total_pendent': total_pendent,
        'total_despeses': total_despeses,
        'balanc_general': balanc_general,
        'partides_data': partides_data,
        'pendents_despeses': pendents_despeses,
        'recents': recents,
    })


# ── Factures proveïdors ───────────────────────────────────────────────────────

@login_required
@requereix_junta
def llista_factures_proveidor(request):
    any_sel = int(request.GET.get('any', timezone.now().year))
    filtre_estat = request.GET.get('estat', '')
    filtre_partida = request.GET.get('partida', '')
    factures = FacturaProveidor.objects.filter(data__year=any_sel)
    if filtre_estat:
        factures = factures.filter(estat=filtre_estat)
    if filtre_partida:
        factures = factures.filter(partida=filtre_partida)
    total = factures.aggregate(t=Sum('import_total'))['t'] or 0
    pendents = FacturaProveidor.objects.filter(estat=FacturaProveidor.ESTAT_PENDENT).count()
    return render(request, 'facturacio/proveidor/llista.html', {
        'factures': factures, 'any_sel': any_sel, 'total': total,
        'filtre_estat': filtre_estat, 'filtre_partida': filtre_partida,
        'partides': PARTIDES, 'estats': FacturaProveidor.ESTAT_CHOICES,
        'pendents': pendents, 'today': timezone.now().date(),
    })


@login_required
@requereix_junta
def crear_factura_proveidor(request):
    if request.method == 'POST':
        form = FacturaProveidorForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Factura de proveïdor registrada.')
            return redirect('llista_factures_proveidor')
    else:
        form = FacturaProveidorForm(initial={'data': timezone.now().date()})
    return render(request, 'facturacio/proveidor/formulari.html', {'form': form, 'accio': 'Nova'})


@login_required
@requereix_junta
def editar_factura_proveidor(request, pk):
    factura = get_object_or_404(FacturaProveidor, pk=pk)
    if request.method == 'POST':
        form = FacturaProveidorForm(request.POST, request.FILES, instance=factura)
        if form.is_valid():
            form.save()
            messages.success(request, 'Factura actualitzada.')
            return redirect('llista_factures_proveidor')
    else:
        form = FacturaProveidorForm(instance=factura)
    return render(request, 'facturacio/proveidor/formulari.html', {'form': form, 'accio': 'Editar', 'factura': factura})


@login_required
@requereix_junta
def eliminar_factura_proveidor(request, pk):
    factura = get_object_or_404(FacturaProveidor, pk=pk)
    if request.method == 'POST':
        factura.delete()
        messages.success(request, 'Factura eliminada.')
        return redirect('llista_factures_proveidor')
    return render(request, 'facturacio/proveidor/confirmar_eliminar.html', {'factura': factura})


@login_required
@requereix_junta
def canvi_estat_factura_proveidor(request, pk):
    factura = get_object_or_404(FacturaProveidor, pk=pk)
    if request.method == 'POST':
        nou_estat = request.POST.get('estat')
        if nou_estat in dict(FacturaProveidor.ESTAT_CHOICES):
            factura.estat = nou_estat
            factura.save(update_fields=['estat'])
    return redirect('llista_factures_proveidor')


# ── Helper ────────────────────────────────────────────────────────────────────

def _seguent_numero_factura():
    any_actual = timezone.now().year
    prefix = f'F{any_actual}-'
    ultima = Factura.objects.filter(numero__startswith=prefix, tipus='FACTURA').order_by('-numero').first()
    if ultima:
        try:
            num = int(ultima.numero.split('-')[-1]) + 1
        except ValueError:
            num = 1
    else:
        num = 1
    return f'{prefix}{num:04d}'
