import csv
import io
import secrets
from datetime import date

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings as django_settings

from .models import Soci, Pagament, PagamentMatricula, PagamentQuota, DocumentSoci, CarrecJunta
from .forms import SociForm, DocumentSociForm, CarrecJuntaForm
from accounts.decorators import requereix_junta
from accounts.models import Configuracio


# ── Perfil propi del soci ─────────────────────────────────────────────────────

@login_required
def el_meu_perfil(request):
    conf = Configuracio.get()
    any_actual = timezone.now().year
    try:
        soci = request.user.soci
    except Soci.DoesNotExist:
        return render(request, 'socis/sense_perfil.html', {'conf': conf})

    estat_dni = soci.estat_dni()
    doc_dni = soci.document_obligatori('DNI')
    doc_lopd = soci.document_obligatori('PROTECCIO')
    doc_cree = soci.document_obligatori('CREE')
    doc_permis = soci.document_obligatori('PERMIS_PARE')
    mesos_pagats = soci.pagaments.filter(any=any_actual, pagat=True).count()

    if request.method == 'POST' and request.FILES.get('fitxer'):
        form = DocumentSociForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.soci = soci
            doc.save()
            tipus = doc.tipus
            if tipus == 'PROTECCIO' and not soci.proteccio_dades_firmada:
                Soci.objects.filter(pk=soci.pk).update(proteccio_dades_firmada=True)
            elif tipus == 'CREE' and not soci.te_curs_pirotecnia:
                Soci.objects.filter(pk=soci.pk).update(te_curs_pirotecnia=True)
            elif tipus == 'PERMIS_PARE' and not soci.permis_pare_signat:
                Soci.objects.filter(pk=soci.pk).update(permis_pare_signat=True)
            messages.success(request, 'Document pujat correctament.')
            return redirect('el_meu_perfil')
        else:
            messages.error(request, 'Error en pujar el document.')

    return render(request, 'socis/perfil_soci.html', {
        'soci': soci,
        'conf': conf,
        'any_actual': any_actual,
        'estat_dni': estat_dni,
        'doc_dni': doc_dni,
        'doc_lopd': doc_lopd,
        'doc_cree': doc_cree,
        'doc_permis': doc_permis,
        'mesos_pagats': mesos_pagats,
        'documents': soci.documents.all(),
        'doc_form': DocumentSociForm(),
    })


# ── Organigrama de la Junta ───────────────────────────────────────────────────

@login_required
def junta_organigrama(request):
    conf = Configuracio.get()
    carrecs = CarrecJunta.objects.select_related('soci').order_by('ordre', 'carrec')
    # Agrupar per nivell per renderitzar l'arbre
    nivell1 = [c for c in carrecs if c.nivell() == 1]
    nivell2 = [c for c in carrecs if c.nivell() == 2]
    nivell3 = [c for c in carrecs if c.nivell() == 3]
    return render(request, 'socis/junta_organigrama.html', {
        'conf': conf,
        'nivell1': nivell1,
        'nivell2': nivell2,
        'nivell3': nivell3,
        'total': carrecs.count(),
    })


@login_required
@requereix_junta
def gestionar_junta(request):
    conf = Configuracio.get()
    carrecs = CarrecJunta.objects.select_related('soci').order_by('ordre', 'carrec')
    form = CarrecJuntaForm()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            form = CarrecJuntaForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Càrrec afegit correctament.')
                return redirect('gestionar_junta')
        elif action == 'delete':
            pk = request.POST.get('pk')
            CarrecJunta.objects.filter(pk=pk).delete()
            messages.success(request, 'Càrrec eliminat.')
            return redirect('gestionar_junta')
        elif action == 'edit':
            pk = request.POST.get('pk')
            carrec_obj = get_object_or_404(CarrecJunta, pk=pk)
            form = CarrecJuntaForm(request.POST, instance=carrec_obj)
            if form.is_valid():
                form.save()
                messages.success(request, 'Càrrec actualitzat.')
                return redirect('gestionar_junta')

    edit_pk = request.GET.get('editar')
    edit_form = None
    edit_obj = None
    if edit_pk:
        edit_obj = get_object_or_404(CarrecJunta, pk=edit_pk)
        edit_form = CarrecJuntaForm(instance=edit_obj)

    return render(request, 'socis/gestio_junta.html', {
        'conf': conf,
        'carrecs': carrecs,
        'form': form,
        'edit_form': edit_form,
        'edit_obj': edit_obj,
    })


# ── Llistat ───────────────────────────────────────────────────────────────────

@login_required
@requereix_junta
def llista_socis(request):
    filtre_tipus = request.GET.get('tipus', '')
    filtre_actiu = request.GET.get('actiu', 'true')
    socis = Soci.objects.all()
    if filtre_tipus:
        socis = socis.filter(tipus=filtre_tipus)
    if filtre_actiu == 'true':
        socis = socis.filter(actiu=True)
    elif filtre_actiu == 'false':
        socis = socis.filter(actiu=False)
    return render(request, 'socis/llista.html', {
        'socis': socis,
        'filtre_tipus': filtre_tipus,
        'filtre_actiu': filtre_actiu,
    })


# ── Detall ────────────────────────────────────────────────────────────────────

@login_required
@requereix_junta
def detall_soci(request, pk):
    soci = get_object_or_404(Soci, pk=pk)
    any_actual = timezone.now().year
    conf = Configuracio.get()

    pagaments = _assegurar_pagaments_any(soci, any_actual)
    quota = _assegurar_quota(soci, any_actual)
    matricula = _assegurar_matricula(soci)

    mesos_pagats = soci.pagaments.filter(any=any_actual, pagat=True).count()
    doc_dni = soci.document_obligatori('DNI')

    return render(request, 'socis/detall.html', {
        'soci': soci,
        'pagaments': pagaments,
        'quota': quota,
        'matricula': matricula,
        'documents': soci.documents.all(),
        'any_actual': any_actual,
        'estat_dni': soci.estat_dni(),
        'doc_lopd': soci.document_obligatori('PROTECCIO'),
        'doc_cree': soci.document_obligatori('CREE'),
        'doc_permis': soci.document_obligatori('PERMIS_PARE'),
        'doc_dni': doc_dni,
        'mesos_pagats': mesos_pagats,
        'conf': conf,
    })


# ── CRUD ──────────────────────────────────────────────────────────────────────

@login_required
@requereix_junta
def crear_soci(request):
    if request.method == 'POST':
        form = SociForm(request.POST, request.FILES)
        if form.is_valid():
            soci = form.save(commit=False)
            # Auto-crear compte d'accés amb l'email
            password_temp = None
            if soci.email:
                if User.objects.filter(email=soci.email).exists():
                    usuari = User.objects.get(email=soci.email)
                else:
                    password_temp = secrets.token_urlsafe(8)
                    usuari = User.objects.create_user(
                        username=soci.email,
                        email=soci.email,
                        password=password_temp,
                        first_name=soci.nom,
                        last_name=soci.cognoms,
                    )
                soci.usuari = usuari
            soci.save()

            # Rol: junta o soci
            es_junta = form.cleaned_data.get('es_junta', False)
            if soci.usuari and hasattr(soci.usuari, 'perfil'):
                soci.usuari.perfil.rol = 'junta_directiva' if es_junta else 'soci'
                soci.usuari.perfil.save()

            # Càrrec de junta
            if es_junta:
                carrec = form.cleaned_data.get('carrec_junta', '')
                if carrec:
                    CarrecJunta.objects.update_or_create(
                        soci=soci,
                        defaults={
                            'carrec': carrec,
                            'funcions': form.cleaned_data.get('funcions_junta', ''),
                            'ordre': form.cleaned_data.get('ordre_junta') or 99,
                            'data_inici': form.cleaned_data.get('data_inici_carrec'),
                        },
                    )

            any_actual = timezone.now().year
            _assegurar_pagaments_any(soci, any_actual)
            _assegurar_quota(soci, any_actual)
            _assegurar_matricula(soci)

            msg = f'Soci {soci.nom_complet()} creat correctament.'
            if password_temp:
                msg += f' Contrasenya temporal: <strong>{password_temp}</strong>'
            messages.success(request, mark_safe(msg))
            return redirect('detall_soci', pk=soci.pk)
    else:
        form = SociForm(initial={'data_alta': date.today()})
    return render(request, 'socis/formulari.html', {'form': form, 'accio': 'Crear'})


@login_required
@requereix_junta
def editar_soci(request, pk):
    soci = get_object_or_404(Soci, pk=pk)
    if request.method == 'POST':
        form = SociForm(request.POST, request.FILES, instance=soci)
        if form.is_valid():
            form.save()

            # Rol: junta o soci
            es_junta = form.cleaned_data.get('es_junta', False)
            if soci.usuari and hasattr(soci.usuari, 'perfil'):
                soci.usuari.perfil.rol = 'junta_directiva' if es_junta else 'soci'
                soci.usuari.perfil.save()

            # Actualitzar o eliminar càrrec de junta
            if es_junta:
                carrec = form.cleaned_data.get('carrec_junta', '')
                if carrec:
                    CarrecJunta.objects.update_or_create(
                        soci=soci,
                        defaults={
                            'carrec': carrec,
                            'funcions': form.cleaned_data.get('funcions_junta', ''),
                            'ordre': form.cleaned_data.get('ordre_junta') or 99,
                            'data_inici': form.cleaned_data.get('data_inici_carrec'),
                        },
                    )
            else:
                CarrecJunta.objects.filter(soci=soci).delete()

            messages.success(request, 'Dades del soci actualitzades.')
            return redirect('detall_soci', pk=soci.pk)
    else:
        form = SociForm(instance=soci)
    return render(request, 'socis/formulari.html', {'form': form, 'accio': 'Editar', 'soci': soci})


@login_required
@requereix_junta
def eliminar_soci(request, pk):
    soci = get_object_or_404(Soci, pk=pk)
    if request.method == 'POST':
        nom = soci.nom_complet()
        soci.delete()
        messages.success(request, f'Soci {nom} eliminat.')
        return redirect('llista_socis')
    return render(request, 'socis/confirmar_eliminar.html', {'soci': soci})


# ── Carnet ────────────────────────────────────────────────────────────────────

@login_required
@requereix_junta
def carnet_soci(request, pk):
    soci = get_object_or_404(Soci, pk=pk)
    any_actual = timezone.now().year
    mesos_pagats = soci.pagaments.filter(any=any_actual, pagat=True).count()
    return render(request, 'socis/carnet.html', {
        'soci': soci,
        'any_actual': any_actual,
        'mesos_pagats': mesos_pagats,
    })


# ── Pagaments ─────────────────────────────────────────────────────────────────

@login_required
@requereix_junta
def toggle_pagament(request, pk):
    pagament = get_object_or_404(Pagament, pk=pk)
    if request.method == 'POST':
        conf = Configuracio.get()
        pagament.pagat = not pagament.pagat
        if pagament.pagat:
            pagament.data_pagament = timezone.now().date()
            if not pagament.import_pagat:
                pagament.import_pagat = conf.mensualitat_batucada
        else:
            pagament.data_pagament = None
        pagament.save()
    return redirect('detall_soci', pk=pagament.soci.pk)


@login_required
@requereix_junta
def toggle_quota(request, pk):
    quota = get_object_or_404(PagamentQuota, pk=pk)
    if request.method == 'POST':
        conf = Configuracio.get()
        quota.pagat = not quota.pagat
        if quota.pagat:
            quota.data_pagament = timezone.now().date()
            if not quota.import_pagat:
                quota.import_pagat = conf.quota_anual
        else:
            quota.data_pagament = None
        quota.save()
    return redirect('detall_soci', pk=quota.soci.pk)


@login_required
@requereix_junta
def toggle_matricula(request, pk):
    matricula = get_object_or_404(PagamentMatricula, pk=pk)
    if request.method == 'POST':
        conf = Configuracio.get()
        matricula.pagat = not matricula.pagat
        if matricula.pagat:
            matricula.data_pagament = timezone.now().date()
            if not matricula.import_pagat:
                matricula.import_pagat = conf.matricula
        else:
            matricula.data_pagament = None
        matricula.save()
    return redirect('detall_soci', pk=matricula.soci.pk)


@login_required
@requereix_junta
def pagaments_anuals(request):
    any_sel = int(request.GET.get('any', timezone.now().year))
    socis = Soci.objects.filter(actiu=True)
    dades = []
    for soci in socis:
        pagaments = {p.mes: p for p in soci.pagaments.filter(any=any_sel)}
        quota = soci.quotes.filter(any=any_sel).first()
        dades.append({'soci': soci, 'pagaments': pagaments, 'quota': quota})
    return render(request, 'socis/pagaments_anuals.html', {
        'dades': dades,
        'any_sel': any_sel,
        'mesos': Pagament.MESOS,
    })


# ── Rebuts individuals ────────────────────────────────────────────────────────

@login_required
@requereix_junta
def rebut_quota(request, pk, any):
    soci = get_object_or_404(Soci, pk=pk)
    quota = get_object_or_404(PagamentQuota, soci=soci, any=any)
    conf = Configuracio.get()
    enviat = False
    if request.method == 'POST' and 'enviar_email' in request.POST:
        enviat = _enviar_rebut_email(soci, 'socis/email/rebut_quota.html', {
            'soci': soci, 'quota': quota, 'conf': conf,
        }, f'Rebut quota anual {any} — {conf.nom_colla}')
    return render(request, 'socis/rebuts/quota.html', {
        'soci': soci, 'quota': quota, 'conf': conf, 'enviat': enviat,
    })


@login_required
@requereix_junta
def rebut_matricula(request, pk):
    soci = get_object_or_404(Soci, pk=pk)
    matricula = get_object_or_404(PagamentMatricula, soci=soci)
    conf = Configuracio.get()
    enviat = False
    if request.method == 'POST' and 'enviar_email' in request.POST:
        enviat = _enviar_rebut_email(soci, 'socis/email/rebut_matricula.html', {
            'soci': soci, 'matricula': matricula, 'conf': conf,
        }, f'Rebut matrícula — {conf.nom_colla}')
    return render(request, 'socis/rebuts/matricula.html', {
        'soci': soci, 'matricula': matricula, 'conf': conf, 'enviat': enviat,
    })


@login_required
@requereix_junta
def rebut_mensualitat(request, pagament_pk):
    pagament = get_object_or_404(Pagament, pk=pagament_pk)
    soci = pagament.soci
    conf = Configuracio.get()
    enviat = False
    if request.method == 'POST' and 'enviar_email' in request.POST:
        enviat = _enviar_rebut_email(soci, 'socis/email/rebut_mensualitat.html', {
            'soci': soci, 'pagament': pagament, 'conf': conf,
        }, f'Rebut mensualitat {pagament.get_mes_display()} {pagament.any} — {conf.nom_colla}')
    return render(request, 'socis/rebuts/mensualitat.html', {
        'soci': soci, 'pagament': pagament, 'conf': conf, 'enviat': enviat,
    })


# ── Documents ─────────────────────────────────────────────────────────────────

@login_required
@requereix_junta
def pujar_document(request, pk):
    soci = get_object_or_404(Soci, pk=pk)
    if request.method == 'POST':
        form = DocumentSociForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.soci = soci
            doc.save()
            tipus = doc.tipus
            if tipus == 'PROTECCIO' and not soci.proteccio_dades_firmada:
                Soci.objects.filter(pk=soci.pk).update(proteccio_dades_firmada=True)
            elif tipus == 'CREE' and not soci.te_curs_pirotecnia:
                Soci.objects.filter(pk=soci.pk).update(te_curs_pirotecnia=True)
            elif tipus == 'PERMIS_PARE' and not soci.permis_pare_signat:
                Soci.objects.filter(pk=soci.pk).update(permis_pare_signat=True)
            messages.success(request, 'Document pujat correctament.')
        else:
            messages.error(request, 'Error en pujar el document.')
    return redirect('detall_soci', pk=pk)


@login_required
@requereix_junta
def eliminar_document(request, pk):
    doc = get_object_or_404(DocumentSoci, pk=pk)
    soci_pk = doc.soci.pk
    if request.method == 'POST':
        doc.fitxer.delete(save=False)
        doc.delete()
        messages.success(request, 'Document eliminat.')
    return redirect('detall_soci', pk=soci_pk)


# ── Compte d'accés ────────────────────────────────────────────────────────────

@login_required
@requereix_junta
def crear_compte(request, pk):
    soci = get_object_or_404(Soci, pk=pk)
    if request.method == 'POST':
        if soci.usuari:
            messages.warning(request, 'El soci ja té un compte d\'accés.')
            return redirect('detall_soci', pk=pk)
        if User.objects.filter(email=soci.email).exists():
            usuari = User.objects.get(email=soci.email)
            soci.usuari = usuari
            soci.save(update_fields=['usuari'])
            messages.success(request, f'Compte existent ({soci.email}) associat al soci.')
        else:
            password = secrets.token_urlsafe(8)
            usuari = User.objects.create_user(
                username=soci.email,
                email=soci.email,
                password=password,
                first_name=soci.nom,
                last_name=soci.cognoms,
            )
            soci.usuari = usuari
            soci.save(update_fields=['usuari'])
            messages.success(
                request,
                f'Compte creat. Usuari: {soci.email} · Contrasenya temporal: {password}'
            )
    return redirect('detall_soci', pk=pk)


@login_required
@requereix_junta
def canvi_contrasenya(request, pk):
    soci = get_object_or_404(Soci, pk=pk)
    if not soci.usuari:
        messages.error(request, 'El soci no té compte d\'accés.')
        return redirect('detall_soci', pk=pk)
    if request.method == 'POST':
        nova = request.POST.get('nova_contrasenya', '').strip()
        confirma = request.POST.get('confirmar_contrasenya', '').strip()
        if not nova:
            messages.error(request, 'La contrasenya no pot estar buida.')
        elif nova != confirma:
            messages.error(request, 'Les contrasenyes no coincideixen.')
        elif len(nova) < 6:
            messages.error(request, 'Mínim 6 caràcters.')
        else:
            soci.usuari.set_password(nova)
            soci.usuari.save()
            messages.success(request, 'Contrasenya actualitzada.')
            return redirect('detall_soci', pk=pk)
    return render(request, 'socis/canvi_contrasenya.html', {'soci': soci})


# ── Importació CSV ────────────────────────────────────────────────────────────

@login_required
@requereix_junta
def importar_socis(request):
    resultats = None
    if request.method == 'POST':
        fitxer = request.FILES.get('fitxer_csv')
        if not fitxer:
            messages.error(request, 'Selecciona un fitxer CSV.')
        else:
            resultats = _processar_csv(fitxer)
            if resultats['importats']:
                messages.success(request, f"{resultats['importats']} socis importats correctament.")
            if resultats['errors']:
                messages.warning(request, f"{len(resultats['errors'])} files amb errors.")
    return render(request, 'socis/importar.html', {'resultats': resultats})


@login_required
@requereix_junta
def descarregar_plantilla_csv(request):
    from django.http import HttpResponse
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="plantilla_socis.csv"'
    response.write('﻿')  # BOM per Excel
    writer = csv.writer(response)
    writer.writerow([
        'numero_soci', 'data_alta', 'nom', 'cognoms', 'dni', 'data_naixement',
        'adreca', 'codi_postal', 'ciutat', 'telefon', 'email',
        'rol', 'tipus', 'data_baixa',
    ])
    writer.writerow([
        '1', '2024-01-15', 'Maria', 'Garcia López', '43123456A', '1985-03-20',
        'Carrer Major 5', '07200', 'Felanitx', '971123456', 'maria@example.com',
        'soci', 'DIMONIS', '',
    ])
    return response


# ── Helpers ───────────────────────────────────────────────────────────────────

def _assegurar_pagaments_any(soci, any):
    if soci.tipus == Soci.TIPUS_BATUCADA:
        for mes in range(1, 13):
            Pagament.objects.get_or_create(soci=soci, any=any, mes=mes)
    return soci.pagaments.filter(any=any).order_by('mes')


def _assegurar_quota(soci, any):
    quota, _ = PagamentQuota.objects.get_or_create(soci=soci, any=any)
    return quota


def _assegurar_matricula(soci):
    any_alta = soci.data_alta.year if soci.data_alta else timezone.now().year
    matricula, _ = PagamentMatricula.objects.get_or_create(soci=soci, defaults={'any': any_alta})
    return matricula


def _enviar_rebut_email(soci, template, context, assumpte):
    if not soci.email:
        return False
    try:
        cos = render_to_string(template, context)
        send_mail(
            subject=assumpte,
            message='',
            html_message=cos,
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            recipient_list=[soci.email],
            fail_silently=False,
        )
        return True
    except Exception:
        return False


def _processar_csv(fitxer):
    importats = 0
    errors = []
    any_actual = timezone.now().year

    try:
        contingut = fitxer.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(contingut))
    except Exception as e:
        return {'importats': 0, 'errors': [f'Error llegint fitxer: {e}']}

    for i, fila in enumerate(reader, start=2):
        try:
            email = fila.get('email', '').strip()
            if not email:
                errors.append(f'Fila {i}: email obligatori.')
                continue

            nom = fila.get('nom', '').strip()
            cognoms = fila.get('cognoms', '').strip()

            # Si nom_complet ve junt, intenta separar
            if not cognoms and ' ' in nom:
                parts = nom.split(' ', 1)
                nom, cognoms = parts[0], parts[1]

            tipus_raw = fila.get('tipus', 'DIMONIS').strip().upper()
            tipus = tipus_raw if tipus_raw in ('DIMONIS', 'BATUCADA') else 'DIMONIS'

            rol_raw = fila.get('rol', 'soci').strip().lower()
            rol = 'junta_directiva' if 'junta' in rol_raw else 'soci'

            data_alta_str = fila.get('data_alta', '').strip()
            data_alta = _parse_date(data_alta_str) if data_alta_str else date.today()

            data_baixa_str = fila.get('data_baixa', '').strip()
            data_baixa = _parse_date(data_baixa_str) if data_baixa_str else None

            num_str = fila.get('numero_soci', '').strip()
            numero_soci = int(num_str) if num_str else None

            soci, created = Soci.objects.update_or_create(
                email=email,
                defaults={
                    'nom': nom,
                    'cognoms': cognoms,
                    'dni': fila.get('dni', '').strip(),
                    'data_naixement': _parse_date(fila.get('data_naixement', '').strip()),
                    'adreca': fila.get('adreca', '').strip(),
                    'codi_postal': fila.get('codi_postal', '').strip(),
                    'ciutat': fila.get('ciutat', '').strip(),
                    'telefon': fila.get('telefon', '').strip(),
                    'tipus': tipus,
                    'data_alta': data_alta,
                    'data_baixa': data_baixa,
                    'actiu': data_baixa is None,
                }
            )

            # Assignar numero_soci manualment si ve del CSV
            if numero_soci and (created or not soci.numero_soci):
                Soci.objects.filter(pk=soci.pk).update(numero_soci=numero_soci)

            # Crear/actualitzar quota i matrícula
            _assegurar_quota(soci, any_actual)
            _assegurar_matricula(soci)
            _assegurar_pagaments_any(soci, any_actual)

            # Crear compte Django si no existeix
            if email and not soci.usuari:
                if User.objects.filter(email=email).exists():
                    usuari = User.objects.get(email=email)
                else:
                    usuari = User.objects.create_user(
                        username=email, email=email,
                        first_name=nom, last_name=cognoms,
                        password=secrets.token_urlsafe(12),
                    )
                soci.usuari = usuari
                soci.save(update_fields=['usuari'])
                # Assignar rol
                if hasattr(usuari, 'perfil'):
                    usuari.perfil.rol = rol
                    usuari.perfil.save()

            importats += 1
        except Exception as e:
            errors.append(f'Fila {i}: {e}')

    return {'importats': importats, 'errors': errors}


def _parse_date(s):
    if not s:
        return None
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
        try:
            from datetime import datetime
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None
