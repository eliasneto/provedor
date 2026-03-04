"""automacao/tasks.py

Este arquivo só faz o *carregamento automático* das automações.

Para adicionar uma automação nova:
1) Crie um arquivo dentro de `automacao/automacoes/`, por exemplo `minha_automacao.py`.
2) No arquivo, crie uma função com assinatura (tarefa_id, file_path).
3) Exponha um dicionário REGISTRY, por exemplo:

    def minha_automacao(tarefa_id, file_path):
        ...

    REGISTRY = {
        "minha_automacao": minha_automacao,
    }

O sistema vai juntar automaticamente todos os REGISTRYs.
"""

from __future__ import annotations

from importlib import import_module
from pkgutil import iter_modules
from types import ModuleType
from typing import Callable, Dict


def _merge_registry(target: Dict[str, Callable], module: ModuleType) -> None:
    reg = getattr(module, "REGISTRY", None)
    if not isinstance(reg, dict):
        return

    for slug, func in reg.items():
        if not callable(func):
            continue
        # último ganha (útil pra overrides). Se preferir, troque por raise pra impedir duplicados.
        target[slug] = func


def load_registry() -> Dict[str, Callable]:
    registry: Dict[str, Callable] = {}

    # Ex.: automacao.tasks -> automacao.automacoes
    pkg_name = __name__.rsplit(".", 1)[0] + ".automacoes"
    pkg = import_module(pkg_name)

    for m in iter_modules(pkg.__path__):
        # ignora arquivos “privados” (ex.: _template.py)
        if m.name.startswith("_"):
            continue
        # ignora subpacotes
        if m.ispkg:
            continue

        mod_name = f"{pkg_name}.{m.name}"
        try:
            module = import_module(mod_name)
        except Exception as e:
            # Não derruba o sistema por uma automação quebrada
            print(f"[AUTOMACAO] Falha ao importar {mod_name}: {e}")
            continue

        _merge_registry(registry, module)

    return registry


# Exportado para o resto do sistema (views.py usa isso)
REGISTRY = load_registry()