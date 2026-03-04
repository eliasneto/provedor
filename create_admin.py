import os
import django

# Configura o ambiente do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User

def create_initial_admin():
    username = 'admin'
    email = 'admin@ageis.com.br'
    password = 'admin' # Altere para uma senha forte depois!

    if not User.objects.filter(username=username).exists():
        print(f"Criando superusuário inicial: {username}...")
        User.objects.create_superuser(username, email, password)
        print("Superusuário criado com sucesso!")
    else:
        print(f"O usuário '{username}' já existe no sistema.")

if __name__ == '__main__':
    create_initial_admin()