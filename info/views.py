from django.shortcuts import render

def support_view(request):
    return render(request, 'info/support.html')

def privacy_policy_view(request):
    return render(request, 'info/privacy_policy.html')

def terms_of_service_view(request):
    return render(request, 'info/terms_of_service.html')

def driver_agreement_view(request):
    return render(request, 'info/driver_agreement.html')
