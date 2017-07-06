from django.shortcuts import redirect, render
from lists.models import Item, List, Ju
from lists.forms import ItemForm, JuItemForm, ExistingListItemForm, NewListForm
from accounts.forms import EmailInputForm
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
import csv
User = get_user_model()

# Create your views here.
def view_ju(request, ju_id):
    ju = Ju.objects.get(id = ju_id)
    owner = request.user
    if request.user.is_authenticated:
        return render(request, 'view_ju.html', { 'current_ju': ju,  'owner': owner})
    return redirect('/')

def manage_ju(request, ju_id):
    ju = Ju.objects.get(id = ju_id)
    if ju.owner:
        if request.user != ju.owner:
            return view_ju(request, ju_id)

    form = JuItemForm()
    form.fields['content'].initial = ju.content

    if request.method == 'POST':
        form = JuItemForm(data=request.POST)
        if form.is_valid():
            saved_ju = form.save(owner=ju.owner, ju=ju)
            if saved_ju:
                return redirect(saved_ju)
    return render(request, 'manage_ju.html', { 'current_ju': ju,  'form': form})

def manage_jus(request, email):
    owner = User.objects.get(email=email)
    form = JuItemForm()
    if request.method == 'POST':
        form = JuItemForm(data=request.POST)
        if form.is_valid():
            ju = form.save(owner=owner)
            if ju:
                return redirect(ju)
    return render(request, 'manage_jus.html', {'form': form, 'owner': owner})

def list_jus(request):
    if request.user.is_authenticated:
        return render(request, 'list_jus.html', { 'owner': request.user})
    return redirect('/')

def my_lists(request, email):
    owner = User.objects.get(email=email)
    return render(request, 'my_lists.html', {'owner': owner})

def home_page(request):
    current_ju = Ju.active_ju()
    email_input_form = EmailInputForm()
    if current_ju and request.user.is_authenticated :
        try:
            list_ = List.objects.get(ju = current_ju, owner = request.user) 
            return redirect(list_)
        except:
            pass

    form = NewListForm()
    if not current_ju:
        form.fields['text'].widget.attrs['placeholder'] = '怎么填都行'
    if request.method == 'POST':
        if current_ju:
            return new_order(request)
        else:
            return new_list(request)
    return render(request, 'home.html', {'form': form, 'current_ju': current_ju, 'email_input_form': email_input_form})


def view_list(request, list_id):
    list_ = List.objects.get(id = list_id)
    if list_.owner:
        if request.user != list_.owner:
            return redirect(reverse('home'))

    form = ExistingListItemForm(for_list = list_)
    if list_.ju and list_.ju.status != 'active':
        form.fields['text'].widget.attrs['readonly'] = True 

    if request.method == 'POST':
        form = ExistingListItemForm(for_list=list_, data=request.POST)
        if form.is_valid():
            if form.save():
                return redirect(list_)
    return render(request, 'list.html', { 'list': list_,  'form': form, 'current_ju': list_.ju})

def new_list(request):
    form = NewListForm(data=request.POST)
    form.fields['text'].widget.attrs['placeholder'] = '怎么填都行'
    if form.is_valid():
        list_ = form.save(owner=request.user if request.user.is_authenticated else None)
        if list_:
            return redirect(list_)
    return render(request, 'home.html', {'form': form })

def new_order(request):
    form = NewListForm(data=request.POST)
    current_ju = Ju.active_ju()
    if form.is_valid():
        list_ = form.save(owner=request.user if request.user.is_authenticated else None, ju=current_ju)
        if list_:
            return redirect(list_)
    return render(request, 'home.html', {'form': form, 'current_ju': current_ju })

def load_users(request, ju_id):
    ju = Ju.objects.get(id = ju_id)
    if ju.owner:
        if request.user != ju.owner:
            return redirect(reverse('home'))

    form = JuItemForm()
    form.fields['content'].initial = '\n'.join(
        ['{};{}'.format(row.email,row.depart_name) for row in User.objects.all()]
    )

    if request.method == 'POST':
        form = JuItemForm(data=request.POST)
        if form.is_valid():
            form.load_users()

    return render(request, 'load_users.html', {  'form': form, 'current_ju': ju})

