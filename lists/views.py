from django.shortcuts import redirect, render
from lists.models import Item, List
from jus.models import Ju
from lists.forms import ItemForm, ExistingListItemForm, NewListForm
from jus.forms import UsersForm
from accounts.forms import EmailInputForm
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.db.models import Q
import csv
User = get_user_model()
def order(request, ju_id):
    try:
        current_ju = Ju.objects.get(id=ju_id)
    except :
        current_ju = Ju.active_ju
        return render_home_page(request, current_ju)

    if current_ju and request.user.is_authenticated :
        try:
            list_ = List.objects.get(ju = current_ju, owner = request.user) 
            return redirect(list_)
        # need test two cases:
        # 1.NotExists
        # 2.More than one list returned
        except:
            pass

    form = NewListForm()
    if current_ju.status != 'active':
        form.fields['text'].widget.attrs['readonly'] = True 
    if request.method == 'POST':
        form = NewListForm(data=request.POST)
        if form.is_valid():
            list_ = form.save(
                owner=request.user if request.user.is_authenticated else None, 
                ju=current_ju
            )
            if list_:
                return redirect(list_)
    email_input_form = EmailInputForm()
    return render(
        request, 
        'new_order.html', 
        {'form': form, 'current_ju': current_ju, 'email_input_form': email_input_form }
    )
def my_lists(request, email):
    try:
        owner = User.objects.get(email=email)
        return render(request, 'my_lists.html', {'owner': owner})
    except User.DoesNotExists:
        return redirect('/')

def home_page(request):
    current_ju = Ju.active_ju()

    if request.user.is_authenticated and current_ju:
        return order(request, current_ju.id)
    return render_home_page(request, current_ju)

def next_ju(request, ju_id):
    if ju_id:
        current_ju = Ju.objects.filter(id=ju_id).first()
        next_ = Ju.objects.filter(status='active', updated_at__lt=current_ju.updated_at).exclude(id=current_ju.id).first()
        if next_:
            return order(request, next_.id)
    return render_home_page(request, Ju.active_ju())
    
def render_home_page(request, ju):
    form = NewListForm()
    form.fields['text'].widget.attrs['placeholder'] = '试试看：橙子1斤 2 2.5'
    email_input_form = EmailInputForm()
    return render(request, 'home.html', {'form': form, 'first_ju': ju, 'email_input_form': email_input_form})


def view_list(request, list_id):
    list_ = List.objects.get(id = list_id)
    orders = None
    if list_.owner:
        if request.user != list_.owner and request.user != list_.agent:
            return redirect(reverse('home'))
        if list_.ju:
            orders = List.objects.filter(Q(ju=list_.ju) & (Q(owner=request.user)|Q(agent=request.user))) 

    form = ExistingListItemForm(for_list = list_)
    if list_.ju and list_.ju.status != 'active':
        form.fields['text'].widget.attrs['readonly'] = True 

    if request.method == 'POST':
        form = ExistingListItemForm(for_list=list_, data=request.POST)
        if form.is_valid():
            if form.save():
                return redirect(list_)
    email_input_form = EmailInputForm()
    if orders:
        return render(
            request, 
            'list.html', 
            { 'list': list_,'current_ju': list_.ju,  'form': form, 'orders': orders, 'email_input_form': email_input_form}
        )
    else:
        return render(
            request, 
            'list.html', 
            { 'list': list_,'current_ju': list_.ju,  'form': form, 'email_input_form': email_input_form}
        )

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

    form = UsersForm()
    form.fields['content'].initial = '\n'.join(
        ['{};{}'.format(row.email,row.depart_name) for row in User.objects.all()]
    )

    if request.method == 'POST':
        form = UsersForm(data=request.POST)
        if form.is_valid():
            form.load_users()

    return render(request, 'load_users.html', {  'form': form, 'current_ju': ju})

