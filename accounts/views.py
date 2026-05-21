from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from socis.models import Soci, Pagament
from facturacio.models import Factura, Despesa
from django.utils import timezone
from django.db.models import Sum
from .models import Acta, Configuracio
from .decorators import requereix_junta


@login_required
def dashboard(request):
    usuari = request.user
    es_junta = hasattr(usuari, 'perfil') and usuari.perfil.es_junta()

    if es_junta:
        return dashboard_junta(request)
    else:
        return dashboard_soci(request)


def dashboard_junta(request):
    any_actual = timezone.now().year
    mes_actual = timezone.now().month

    total_socis = Soci.objects.filter(actiu=True).count()
    socis_al_dia = Pagament.objects.filter(
        any=any_actual, mes=mes_actual, pagat=True
    ).count()
    socis_pendents = total_socis - socis_al_dia

    ingressos = Factura.objects.filter(
        estat='PAGAT', data__year=any_actual
    ).aggregate(total=Sum('linies__quantitat') * 0)['total'] or 0

    ingressos_raw = 0
    for f in Factura.objects.filter(estat='PAGAT', data__year=any_actual):
        ingressos_raw += f.total()

    despeses_any = Despesa.objects.filter(
        data__year=any_actual
    ).aggregate(total=Sum('import_total'))['total'] or 0

    factures_pendents = Factura.objects.filter(
        tipus='FACTURA', estat='PENDENT'
    ).count()

    context = {
        'es_junta': True,
        'any_actual': any_actual,
        'mes_actual': mes_actual,
        'total_socis': total_socis,
        'socis_al_dia': socis_al_dia,
        'socis_pendents': socis_pendents,
        'ingressos_any': ingressos_raw,
        'despeses_any': despeses_any,
        'balanc': ingressos_raw - despeses_any,
        'factures_pendents': factures_pendents,
        'ultims_socis': Soci.objects.filter(actiu=True).order_by('-data_alta')[:5],
        'ultimes_despeses': Despesa.objects.order_by('-data')[:5],
        'ultims_actes': Acta.objects.filter(publicat=True).order_by('-data')[:4],
    }
    return render(request, 'accounts/dashboard_junta.html', context)


# ── Actes (zona pública) ──────────────────────────────────────────────────────

def actes_public(request):
    filtre = request.GET.get('tipus', '')
    actes = Acta.objects.filter(publicat=True)
    if filtre:
        actes = actes.filter(tipus=filtre)
    return render(request, 'actes/llista.html', {
        'actes': actes, 'filtre': filtre, 'tipus_choices': Acta.TIPUS_CHOICES,
    })


@login_required
@requereix_junta
def actes_gestio(request):
    if request.method == 'POST':
        tipus = request.POST.get('tipus', Acta.TIPUS_COLLA)
        titol = request.POST.get('titol', '').strip()
        data = request.POST.get('data', '')
        fitxer = request.FILES.get('fitxer')
        publicat = request.POST.get('publicat') == 'on'
        if titol and data:
            acta = Acta(tipus=tipus, titol=titol, data=data, publicat=publicat)
            if fitxer:
                acta.fitxer = fitxer
            acta.save()
            messages.success(request, 'Acta publicada correctament.')
        else:
            messages.error(request, 'Títol i data són obligatoris.')
        return redirect('actes_gestio')
    actes = Acta.objects.all()
    return render(request, 'actes/gestio.html', {
        'actes': actes, 'tipus_choices': Acta.TIPUS_CHOICES,
    })


@login_required
@requereix_junta
def eliminar_acta(request, pk):
    acta = get_object_or_404(Acta, pk=pk)
    if request.method == 'POST':
        if acta.fitxer:
            acta.fitxer.delete(save=False)
        acta.delete()
        messages.success(request, 'Acta eliminada.')
    return redirect('actes_gestio')


@login_required
@requereix_junta
def toggle_acta_publicat(request, pk):
    acta = get_object_or_404(Acta, pk=pk)
    if request.method == 'POST':
        acta.publicat = not acta.publicat
        acta.save(update_fields=['publicat'])
    return redirect('actes_gestio')


@login_required
def dades_associacio(request):
    from socis.models import CarrecJunta
    from .forms import ConfiguracioForm
    conf = Configuracio.get()
    carrecs_junta = CarrecJunta.objects.select_related('soci').order_by('ordre', 'carrec')
    form = None

    if request.user.perfil.es_junta():
        if request.method == 'POST':
            form = ConfiguracioForm(request.POST, request.FILES, instance=conf)
            if form.is_valid():
                form.save()
                messages.success(request, 'Dades de l\'associació actualitzades.')
                return redirect('dades_associacio')
        else:
            form = ConfiguracioForm(instance=conf)

    return render(request, 'associacio/dades.html', {
        'conf': conf,
        'carrecs_junta': carrecs_junta,
        'form': form,
    })


def dashboard_soci(request):
    from facturacio.models import Despesa
    usuari = request.user
    try:
        soci = Soci.objects.get(usuari=usuari)
    except Soci.DoesNotExist:
        soci = None

    despeses = Despesa.objects.filter(soci=usuari).order_by('-data')[:5]

    context = {
        'es_junta': False,
        'soci': soci,
        'despeses': despeses,
        'ultims_actes': Acta.objects.filter(publicat=True).order_by('-data')[:4],
    }
    return render(request, 'accounts/dashboard_soci.html', context)
