from django.shortcuts import render

def travel_cost(request):
    # Your logic for the dashboard page goes here
    return render(request, 'travel_cost/travel_cost.html')

def index(request):
    return render(request, 'travel_cost/index.html')