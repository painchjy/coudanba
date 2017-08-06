from django.shortcuts import redirect, render
from jus.models import Ju, Location,LocationUser
from lists.models import Item, List
from jus.forms import JuItemForm, LocationForm, LocationDepartForm
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
import csv,json
User = get_user_model()
def follow(request, l_id):
    location = Location.objects.filter(id=l_id).first()
    if location and request.user.is_authenticated:
        lu = LocationUser.objects.filter(location=location, user=request.user).first()
        if not lu:
            lu = LocationUser.objects.create(location=location, user=request.user)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
def unfollow(request, l_id):
    location = Location.objects.filter(id=l_id).first()
    if location and request.user.is_authenticated:
        lu = LocationUser.objects.filter(location=location, user=request.user).first()
        if lu:
            lu.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
def view_location(request, location_id):
    if not request.user.is_authenticated:
        return redirect('/')
    location = Location.objects.filter(id = location_id).first()
    if not location:
        return redirect('/')
    l_form = LocationForm(location=location)
    ld_form = LocationDepartForm(location=location)
    if request.method == 'POST':
        l_form = LocationForm(location=location, data=request.POST)
        ld_form = LocationDepartForm(location=location, data=request.POST)
        if l_form.is_valid():
            depart_names = request.POST.getlist('depart_names')
            location = l_form.save(location=location, depart_names=depart_names)
            if location:
                return redirect(location)
    return render(
        request, 
        'view_location.html', 
        {'location': location, 'l_form': l_form, 'ld_form': ld_form, 'locations': Location.objects.all()}
    )



    pass
def new_location(request):
    if not request.user.is_authenticated:
        return redirect('/')
    l_form = LocationForm()
    ld_form = LocationDepartForm()
    if request.method == 'POST':
        l_form = LocationForm(data=request.POST)
        ld_form = LocationDepartForm(data=request.POST)
        if l_form.is_valid():
            depart_names = request.POST['depart_names']
            location = l_form.save(depart_names=depart_names)
            if location:
                return redirect(location)
    return render(
        request, 
        'new_location.html', 
        {'l_form': l_form, 'ld_form': ld_form, 'locations': Location.objects.all()}
    )


# list the ju's orders, all list owner's  department  
# should be as same as the request user
def view_ju(request, ju_id):
    ju = Ju.objects.get(id = ju_id)
    if not request.user.is_authenticated:
        return redirect('/')

    if ju.owner:
        if request.user != ju.owner:
            return render(request, 'view_ju.html', { 'current_ju': ju,  'user': request.user})
            # return view_ju(request, ju_id)
    else:
        ju.owner = request.user

    form = JuItemForm()
    form.fields['address'].initial = ju.address
    # form.fields['content'].initial = ju.content
    form.fields['items'].initial = json.dumps(ju.items,ensure_ascii=False,indent=1)
    form.fields['stop_date_time'].initial = ju.stop_date_time
    form.fields['status'].initial = ju.status
    form.fields['ju_type'].initial = ju.ju_type
    form.fields['location'].queryset = ju.owner.prefered_locations()
    form.fields['location'].initial = ju.location

    if request.method == 'POST':
        form = JuItemForm(data=request.POST)
        form.fields['location'].queryset = ju.owner.prefered_locations()
        if form.is_valid():
            form.save(owner=request.user, ju=ju)
    return render(request, 'manage_ju.html', { 'current_ju': ju,  'form': form})

def new_ju(request, p_id=None):
    parent = None
    if p_id:
        parent = Ju.objects.filter(id=p_id).first()
        
    if not request.user.is_authenticated:
        return redirect('/')
    owner = request.user
    form = JuItemForm()
    if parent:
        form.fields['items'].initial = json.dumps(
            parent.items,
            ensure_ascii=False,
            indent=1
        )
        if parent.ju_type == 'category':
            form.fields['ju_type'].initial = 'order'
    else:
        form.fields['items'].initial = json.dumps(
            {
                "A":{"desc":"较完整的项目","price":0,"href":"http://...","max_total_qty":100,"max_qty":10},
                "B":{"desc":"最简单的项目"},
            },
            ensure_ascii=False,
            indent=1
        )
    form.fields['location'].queryset = owner.prefered_locations()
    if request.method == 'POST':
        form = JuItemForm(data=request.POST)
        form.fields['location'].queryset = owner.prefered_locations()
        if form.is_valid():
            ju = form.save(owner=owner,parent=parent)
            if ju:
                return redirect(ju)
    if p_id:
        return render(request, 'new_ju.html', {'form': form, 'owner': owner, 'p_id': p_id })
    return render(request, 'new_ju.html', {'form': form, 'owner': owner})

def list_jus(request):
    if request.user.is_authenticated:
        return render(
            request,
            'list_jus.html', 
            { 
            }
        )
    return redirect('/')

def list_categories(request):
    if request.user.is_authenticated:
        return render(
            request,
            'list_categories.html', 
            { 
            }
        )
    return redirect('/')

