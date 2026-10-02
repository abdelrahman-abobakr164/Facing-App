from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404


def owner_ship_required(model, id_kwarg="id", user="user"):
    def decorators(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            obj = get_object_or_404(model, id=kwargs[id_kwarg])
            if getattr(obj, user) != request.user:
                return HttpResponseForbidden("You are not Authorized.")
            request.owned_object = obj
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorators
