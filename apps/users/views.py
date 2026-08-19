"""Views для users приложения."""

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AppointmentForm, UserLoginForm, UserProfileForm, UserRegisterForm
from .models import Appointment, UserProfile


def register(request):
    """Регистрация пользователя."""

    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # Создаем профиль
                UserProfile.objects.create(user=user)
                username = form.cleaned_data.get("username")
                raw_password = form.cleaned_data.get("password1")
                user = authenticate(username=username, password=raw_password)
                login(request, user)
                messages.success(request, "Регистрация успешна! Добро пожаловать.")
                return redirect("core:index")
            except IntegrityError:
                form.add_error("username", "Пользователь с таким именем уже существует.")
    else:
        form = UserRegisterForm()

    return render(request, "users/register.html", {"form": form})


def user_login(request):
    """Вход пользователя."""

    if request.method == "POST":
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Вы успешно вошли в систему!")
                return redirect("users:dashboard")
            else:
                form.add_error(None, "Неверное имя пользователя или пароль.")
    else:
        form = UserLoginForm()

    return render(request, "users/login.html", {"form": form})


@login_required
def dashboard(request):
    """Личный кабинет."""

    appointments = (
        Appointment.objects.filter(user=request.user)
        .select_related("service")
        .prefetch_related("result")
        .order_by("-date", "-time")
    )

    # Профиль пользователя
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    context = {
        "appointments": appointments,
        "profile": profile,
    }
    return render(request, "users/dashboard.html", context)


@login_required
def profile_edit(request):
    """Редактирование профиля."""

    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль успешно обновлен!")
            return redirect("users:dashboard")
    else:
        form = UserProfileForm(instance=profile)

    return render(request, "users/profile_edit.html", {"form": form})


@login_required
def appointment_create(request):
    """Создание записи на приём."""

    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.user = request.user
            appointment.save()
            messages.success(request, "Запись на приём создана! Ожидайте подтверждения.")
            return redirect("users:dashboard")
    else:
        form = AppointmentForm()

    return render(request, "users/appointment_form.html", {"form": form})


@login_required
def appointment_detail(request, pk):
    """Детали записи."""

    appointment = get_object_or_404(Appointment, pk=pk, user=request.user)

    return render(request, "users/appointment_detail.html", {"appointment": appointment})


@login_required
def appointment_cancel(request, pk):
    """Отмена записи."""

    appointment = get_object_or_404(Appointment, pk=pk, user=request.user)

    if appointment.status in ["pending", "confirmed"]:
        appointment.status = "cancelled"
        appointment.save()
        messages.success(request, "Запись успешно отменена.")

    return redirect("users:dashboard")


def user_logout(request):
    """Выход пользователя."""

    logout(request)
    messages.success(request, "Вы успешно вышли из системы.")
    return redirect("core:index")
