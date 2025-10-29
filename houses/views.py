from django.http import HttpResponse

def house_home(request):
    return HttpResponse("🏠 I am the Houses Views!")