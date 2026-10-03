from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse


@login_required
def index(request):
    return redirect(reverse('warehouse_dashboard'))


