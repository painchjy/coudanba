from django.shortcuts import redirect, render
from jus.models import Ju
from lists.models import Item, List
from jus.forms import JuItemForm
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
import csv
User = get_user_model()

# list the ju's orders, all list owner's  department  
# should be as same as the request user
def view_ju(request, ju_id):
    ju = Ju.objects.get(id = ju_id)
    owner = request.user
    if not request.user.is_authenticated:
        return redirect('/')

    if ju.owner:
        if request.user != ju.owner:
            return render(request, 'view_ju.html', { 'current_ju': ju,  'owner': owner})
            # return view_ju(request, ju_id)

    form = JuItemForm()
    form.fields['content'].initial = ju.content

    if request.method == 'POST':
        form = JuItemForm(data=request.POST)
        if form.is_valid():
            form.save(owner=ju.owner, ju=ju)
    return render(request, 'manage_ju.html', { 'current_ju': ju,  'form': form})

def new_ju(request):
    owner = request.user
    form = JuItemForm()
    if request.method == 'POST':
        form = JuItemForm(data=request.POST)
        if form.is_valid():
            ju = form.save(owner=owner)
            if ju:
                return redirect(ju)
    return render(request, 'new_ju.html', {'form': form, 'owner': owner})

def list_jus(request):
    #active_jus = Ju.objects.filter(status='active')
    #unactive_jus = Ju.objects.filter(status='active')
    list_dict = dict(
        [(list.ju.id, list)  for list in List.objects.filter(
            owner=request.user,
            ju__isnull=False
    )])
    if request.user.is_authenticated:
        return render(
            request,
            'list_jus.html', 
            { 'owner': request.user, 'jus': Ju.objects.all, 'list_dict': list_dict}
        )
    return redirect('/')

