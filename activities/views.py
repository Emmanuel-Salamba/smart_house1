from django.http import HttpResponse

def activity_home(request):
    return HttpResponse("📊 I am the Activity Views!")