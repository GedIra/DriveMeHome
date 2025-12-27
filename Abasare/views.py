from django.shortcuts import render

def support_view(request):
    return render(request, 'Abasare/support.html')

def privacy_policy_view(request):
    return render(request, 'Abasare/privacy_policy.html')

def terms_of_service_view(request):
    return render(request, 'Abasare/terms_of_service.html')

def driver_agreement_view(request):
    return render(request, 'Abasare/driver_agreement.html')
