from django.shortcuts import render, redirect
from .models import Provedor
from .forms import ProvedorForm
from django.core.paginator import Paginator

def listar_provedores(request):
    lista_provedores = Provedor.objects.all().order_by('-criado_em')
    
    # Configura 20 provedores por página
    paginator = Paginator(lista_provedores, 20) 
    
    page_number = request.GET.get('page')
    provedores = paginator.get_page(page_number)
    
    return render(request, 'provedores_list.html', {'provedores': provedores})

def criar_provedor(request):
    if request.method == 'POST':
        form = ProvedorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_provedores')
    else:
        form = ProvedorForm()
    return render(request, 'provedor_form.html', {'form': form})