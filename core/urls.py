from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

# Importação das views dos módulos
from provedor.views import listar_provedores, criar_provedor # Garanta que criar_provedor esteja aqui
from automacao.views import listar_automacoes, iniciar_automacao, parar_automacao, upload_planilha

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('', login_required(TemplateView.as_view(template_name='home.html')), name='home'),

    # Módulo Provedores
    path('provedores/', listar_provedores, name='listar_provedores'),
    path('provedores/novo/', criar_provedor, name='criar_provedor'), # <--- ESTA LINHA RESOLVE O ERRO

    # Módulo Automação
    path('automacao/', listar_automacoes, name='listar_automacoes'),
    path('automacao/iniciar/<int:pk>/', iniciar_automacao, name='iniciar_automacao'),
    path('automacao/parar/<int:pk>/', parar_automacao, name='parar_automacao'),
    path('automacao/upload/<int:pk>/', upload_planilha, name='upload_planilha'),
]