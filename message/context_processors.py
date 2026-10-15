from .models import *
from accounts.models import Follow


def nav_counters(request):
    requests = Follow.objects.filter(
        following=request.user, status=Follow.Status.PENDING
    ).count()

    return {"requests": requests}
