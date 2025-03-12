from django.shortcuts import render

from django.shortcuts import render
from dashboard.models import TransportationData  # Import model from dashboard app

def explorer_view(request):
    data = TransportationData.objects.all()  # Fetch all transportation data
    return render(request, 'explorer/index.html', {'data': data})

def index(request):
    return render(request, 'explorer/index.html')

def roads(request):
    return render(request, 'explorer/roads.html')

def routes(request):
    return render(request, 'explorer/routes.html')

