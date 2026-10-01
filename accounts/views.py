from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .forms import SettingsForm

User = get_user_model()


@login_required
def settings(request):
    if request.method == "POST":
        form = SettingsForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("settings")
        else:
            return redirect("settings")
    else:
        form = SettingsForm(instance=request.user)

    return render(request, "accounts/settings.html", {"form": form})


@login_required
def profile(request):
    return render(request, "accounts/profile.html")
