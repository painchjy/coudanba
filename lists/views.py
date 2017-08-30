from django.shortcuts import redirect, render
from lists.models import Item, List
from jus.models import Ju
from lists.forms import ExistingListItemForm, NewListForm, ListForm, NewOrderForm
from jus.forms import UsersForm
from accounts.forms import EmailInputForm
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.db.models import Q
import csv
from wechat.views import oauth
NEED_TO_LOGIN_ERROR = "别着急，先登录再凑单！"
User = get_user_model()

def view_order(request, list_id):
    list_ = List.objects.filter(id = list_id).first()
    if (not list_) or (not list_.owner) or (not list_.ju):
        return redirect(reverse('home'))
    if request.user != list_.owner and request.user != list_.agent:
        return redirect(reverse('home'))

    orders = List.objects.filter(Q(ju=list_.ju) & (Q(owner=request.user)|Q(agent=request.user))) 

    form = ExistingListItemForm(for_list = list_)
    if not list_.ju.can_order(request.user):
        form.fields['text'].widget.attrs['readonly'] = True 

    if request.method == 'POST':
        form = ExistingListItemForm(for_list=list_, data=request.POST)
        if form.is_valid():
            if form.save():
                return redirect(list_)
    return render(
        request, 
        'view_order.html', 
        { 'list': list_,'current_ju': list_.ju,  'form': form, 'orders': orders}
    )

def next_category(request, ju_id):
    current_ju = Ju.objects.filter(id=ju_id).first()
    if current_ju:
        if request.user.is_authenticated:
            next_ = request.user.next_ju(current_ju, ju_type='category')
        else:
            next_ = current_ju.next(ju_type='category')
        if next_:
            return render(
                request, 
                'view_category.html', 
                { 'current_ju': next_ }
            )

    return category(request)

def category(request):
    current_ju = Ju.active_ju(ju_type='category')
    return render(
        request, 
        'view_category.html', 
        { 'current_ju': current_ju }
    )


def order(request, ju_id):
    try:
        current_ju = Ju.objects.get(id=ju_id)
    except :
        if request.user.is_authenticated:
            current_ju = request.user.active_ju()
        else:
            current_ju = Ju.active_ju()
        return render_home_page(request, current_ju)

    if request.user.is_authenticated :
        # 通过new_order可以把owner的代理人改成自己，当然可以用来取消别人对自己的代理。
        if request.method == 'POST':
            form_list = ListForm(depart_name=request.user.depart_name, data=request.POST)
            if form_list.is_valid():
                owner = form_list.cleaned_data['owner'] or request.user
                list_ = List.objects.filter(ju=current_ju, owner=owner).first()
                if list_: 
                    if list_.agent != request.user:
                        list_.agent = request.user
                        list_.save()
                    return view_order(request, list_.id)
            return new_order(request, current_ju.id)
        list_ = List.objects.filter(ju=current_ju, owner=request.user).first()
        if not list_:
            list_ = List.objects.filter(ju=current_ju, agent=request.user).first()
        if list_:
            return view_order(request, list_.id)
    return new_order(request, current_ju.id)

            
def new_order(request, ju_id):
    try:
        current_ju = Ju.objects.get(id=ju_id)
    except :
        if request.user.is_authenticated:
            current_ju = request.user.active_ju()
        else:
            current_ju = Ju.active_ju()
        return render_home_page(request, current_ju)

    depart_name = None
    form = NewOrderForm()
    if not current_ju.can_order(request.user):
        form.fields['text'].widget.attrs['readonly'] = True 
    
    if request.user.is_authenticated :
        depart_name=request.user.depart_name
        form_list = ListForm(depart_name=depart_name)
        # form_list.fields['owner'].initial = request.user
        if request.method == 'POST':
            form = NewOrderForm(data=request.POST)
            form_list = ListForm(depart_name=depart_name, data=request.POST)
            if form.is_valid() and form_list.is_valid():
                owner = form_list.cleaned_data['owner'] or request.user
                list_ = form.save(
                    owner=owner,
                    agent=request.user,
                    ju=current_ju
                )
                if list_:
                    return redirect(list_)
        return render(
            request, 
            'new_order.html', 
            {'form': form, 'form_list': form_list, 'current_ju': current_ju}
        )

    email_input_form = EmailInputForm()
    if request.method == 'POST':
        form = NewOrderForm(data=request.POST)
        form.add_error('text',NEED_TO_LOGIN_ERROR)
    return render(
        request, 
        'new_order.html', 
        {'form': form,  'current_ju': current_ju, 'email_input_form': email_input_form }
    )
def my_lists(request, email):
    try:
        owner = User.objects.get(email=email)
        return render(request, 'my_lists.html', {'owner': owner})
    except User.DoesNotExists:
        return redirect('/')
@oauth
def home_page(request):
    if request.user.is_authenticated:
        current_ju = request.user.active_ju()
    else:
        current_ju = Ju.active_ju()

    if request.user.is_authenticated and current_ju:
        return order(request, current_ju.id)
    return render_home_page(request, current_ju)

def render_home_page(request, ju):
    form = NewListForm()
    form.fields['text'].widget.attrs['placeholder'] = '试试看：橙子1斤 2 2.5'
    if request.user.is_authenticated:
        return render(request, 'home.html', {'form': form, 'first_ju': ju})
    email_input_form = EmailInputForm()
    return render(request, 'home.html', {'form': form, 'first_ju': ju, 'email_input_form': email_input_form})
def new_list(request):
    form = NewListForm(data=request.POST)
    form.fields['text'].widget.attrs['placeholder'] = '怎么填都行'
    if form.is_valid():
        list_ = form.save(owner=request.user if request.user.is_authenticated else None)
        if list_:
            return redirect(list_)
    return render(request, 'home.html', {'form': form })


def next_ju(request, ju_id):
    current_ju = Ju.objects.filter(id=ju_id).first()
    if current_ju:
        if request.user.is_authenticated:
            next_ = request.user.next_ju(current_ju)
        else:
            next_ = current_ju.next()
        if next_:
            return order(request, next_.id)
    if request.user.is_authenticated:
        current_ju = request.user.active_ju()
    else:
        current_ju = Ju.active_ju()
    return render_home_page(request, current_ju)
    
def view_list(request, list_id):
    list_ = List.objects.filter(id = list_id).first()
    if not list_:
        return redirect(reverse('home'))

    if list_.ju:
        return view_order(request, list_id)

    form = ExistingListItemForm(for_list = list_)

    if request.method == 'POST':
        form = ExistingListItemForm(for_list=list_, data=request.POST)
        if form.is_valid():
            if form.save():
                return redirect(list_)
    if request.user.is_authenticated:
        return render(
            request, 
            'list.html', 
            { 'list': list_, 'form': form}
        )

    email_input_form = EmailInputForm()
    return render(
        request, 
        'list.html', 
        { 'list': list_, 'form': form, 'email_input_form': email_input_form}
    )


# type url manually ! '/lists/load_users/{ju_id}
def load_users(request, ju_id):
    ju = Ju.objects.get(id = ju_id)
    if ju.owner:
        if request.user != ju.owner:
            return redirect(reverse('home'))

    form = UsersForm()
    form.fields['content'].initial = '\n'.join(
        ['{};{};{}'.format(row.email,row.depart_name,row.display_name) for row in User.objects.all()]
    )

    if request.method == 'POST':
        form = UsersForm(data=request.POST)
        if form.is_valid():
            form.load_users()

    return render(request, 'load_users.html', {  'form': form, 'current_ju': ju})

