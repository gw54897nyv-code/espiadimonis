from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def requereix_junta(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'perfil') or not request.user.perfil.es_junta():
            messages.error(request, 'No tens permisos per accedir a aquesta secció.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
