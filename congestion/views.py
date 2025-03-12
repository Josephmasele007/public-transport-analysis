from django.shortcuts import render

def congestion(request):
    return render(request, 'congestion/congestion.html')


def analysis(request):
    return render(request, 'congestion/analysis.html')

def congestion_map(request):
    return render(request, 'congestion/congestion_map.html')