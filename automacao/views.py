import threading
from django.shortcuts import get_object_or_404, redirect, render
from .models import Automacao
from .tasks import REGISTRY

def listar_automacoes(request):
    automacoes = Automacao.objects.all().order_by('-ultima_execucao')
    return render(request, 'automacao_list.html', {'automacoes': automacoes})

def iniciar_automacao(request, pk):
    tarefa = get_object_or_404(Automacao, pk=pk)
    if tarefa.planilha and tarefa.slug_script in REGISTRY:
        tarefa.status = 'executando'
        tarefa.save()
        
        # Executa em Background
        func = REGISTRY[tarefa.slug_script]
        thread = threading.Thread(target=func, args=(tarefa.id, tarefa.planilha.path))
        thread.daemon = True
        thread.start()
        
    return redirect('listar_automacoes')

def parar_automacao(request, pk):
    tarefa = get_object_or_404(Automacao, pk=pk)
    tarefa.status = 'parado'
    tarefa.save()
    return redirect('listar_automacoes')

def upload_planilha(request, pk):
    if request.method == 'POST' and request.FILES.get('planilha'):
        tarefa = get_object_or_404(Automacao, pk=pk)
        tarefa.planilha = request.FILES['planilha']
        tarefa.save()
    return redirect('listar_automacoes')