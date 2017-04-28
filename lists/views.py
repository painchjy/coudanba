from django.shortcuts import redirect, render
from lists.models import Item, List
from lists.forms import ItemForm
from django.core.exceptions import ValidationError

# Create your views here.
def home_page(request):
    return render(request,'home.html',{'form': ItemForm()})

def view_list(request, list_id):
    list_ = List.objects.get(id = list_id)
    form = ItemForm()

    if request.method == 'POST':
        form = ItemForm(data=request.POST)
        if form.is_valid():
            form.save( for_list = list_)
            return redirect(list_)
    return render(request, 'list.html', { 'list': list_,  'form': form})

def new_list(request):
    form = ItemForm(data=request.POST)
    if form.is_valid():
        list_ = List.objects.create()
        form.save( for_list = list_)
        return redirect(list_)
    else:
        return render(request, 'home.html', {'form': form})

    #try:
    #    item.full_clean()
    #    item.save()
    #except ValidationError:
    #    list_.delete()
    #    error = "You can't have an empty list item"
    #    return render(request, 'home.html',{'error': error, 'form': ItemForm()})
    #return redirect(list_)

