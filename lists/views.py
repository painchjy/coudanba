from django.shortcuts import redirect, render
from lists.models import Item, List, Ju
from lists.forms import ItemForm, ExistingListItemForm, NewListForm
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your views here.
def my_lists(request, email):
    owner = User.objects.get(email=email)
    return render(request, 'my_lists.html', {'owner': owner})

def home_page(request):
    active_ju = Ju.active_ju()
    if active_ju and request.user.is_authenticated :
        try:
            list_ = List.objects.get(ju = active_ju, owner = request.user) 
            return redirect(list_)
        except:
            pass

    if active_ju:
        return new_order(request)
    else:
        return new_list(request)

def view_list(request, list_id):
    list_ = List.objects.get(id = list_id)
    form = ExistingListItemForm(for_list = list_)

    if request.method == 'POST':
        form = ExistingListItemForm(for_list=list_, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect(list_)
    return render(request, 'list.html', { 'list': list_,  'form': form, 'active_ju': list_.ju})

def new_list(request):
    form = NewListForm(data=request.POST)
    form.fields['text'].widget.attrs['placeholder'] = '账单格式：名称 数量 单价；示例：车厘子1公斤 1.5 129.9'
    if form.is_valid():
        list_ = form.save(owner=request.user if request.user.is_authenticated else None)
        if list_:
            return redirect(list_)
    return render(request, 'home.html', {'form': form })

def new_order(request):
    form = NewListForm(data=request.POST)
    active_ju = Ju.active_ju()
    if form.is_valid():
        list_ = form.save(owner=request.user if request.user.is_authenticated else None, ju=active_ju)
        if list_:
            return redirect(list_)
    return render(request, 'home.html', {'form': form, 'active_ju': active_ju })


