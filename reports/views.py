from django.shortcuts import render

def index(request):
    return render(request, 'reports/index.html')

def reports(request):
    # Your logic for the dashboard page goes here
    return render(request, 'reports/reports.html')