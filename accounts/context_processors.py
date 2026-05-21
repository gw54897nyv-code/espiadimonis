from .models import Configuracio


def configuracio(request):
    return {'conf': Configuracio.get()}
