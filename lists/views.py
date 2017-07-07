from django.shortcuts import redirect, render
from lists.models import Item, List, Ju
from lists.forms import ItemForm, JuItemForm, ExistingListItemForm, NewListForm
from accounts.forms import EmailInputForm
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
    if request.user.is_authenticated:
        return render(request, 'view_ju.html', { 'current_ju': ju,  'owner': owner})
    return redirect('/')

# ju's onwner can modify ju's content
# the url should type manually in browser
def manage_ju(request, ju_id):
    ju = Ju.objects.get(id = ju_id)
    if ju.owner:
        if request.user != ju.owner:
            return redirect(ju)
            # return view_ju(request, ju_id)

    form = JuItemForm()
    form.fields['content'].initial = ju.content

    if request.method == 'POST':
        form = JuItemForm(data=request.POST)
        if form.is_valid():
            form.save(owner=ju.owner, ju=ju)
    return render(request, 'manage_ju.html', { 'current_ju': ju,  'form': form})

def order(request, ju_id):
    try:
        current_ju = Ju.objects.get(id=ju_id)
    except :
        return redirect ('/')

    if current_ju and request.user.is_authenticated :
        try:
            list_ = List.objects.get(ju = current_ju, owner = request.user) 
            return redirect(list_)
        # need test two cases:
        # 1.NotExists
        # 2.More than one list returned
        except:
            pass

    form = NewListForm(data=request.POST)
    if current_ju.status != 'active':
        form.fields['text'].widget.attrs['readonly'] = True 
    if form.is_valid():
        list_ = form.save(
            owner=request.user if request.user.is_authenticated else None, 
            ju=current_ju
        )
        if list_:
            return redirect(list_)
    return render(request, 'new_order.html', {'form': form, 'current_ju': current_ju })

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

def my_lists(request, email):
    try:
        owner = User.objects.get(email=email)
        return render(request, 'my_lists.html', {'owner': owner})
    except User.DoesNotExists:
        return redirect('/')

def home_page(request):
    current_ju = Ju.active_ju()
    email_input_form = EmailInputForm()
    form = NewListForm()
    if current_ju and request.user.is_authenticated:
        return order(request, current_ju.id)
    form.fields['text'].widget.attrs['placeholder'] = '怎么填都行'
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

# type url manually ! '/lists/load_users/{ju_id}
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

