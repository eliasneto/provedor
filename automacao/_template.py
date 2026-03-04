"""Template de automação.

Copie este arquivo e renomeie (ex.: `minha_automacao.py`).
Depois ajuste o REGISTRY.
"""

from __future__ import annotations

import pandas as pd

from automacao.models import Automacao


def minha_automacao(tarefa_id, file_path):
    tarefa = Automacao.objects.get(id=tarefa_id)
    try:
        df = pd.read_excel(file_path)
        for _, row in df.iterrows():
            tarefa.refresh_from_db()
            if tarefa.status != "executando":
                break

            # sua lógica aqui
            print(row.to_dict())

        tarefa.refresh_from_db()
        if tarefa.status == "executando":
            tarefa.status = "concluido"
            tarefa.save()

    except Exception:
        tarefa.status = "falha"
        tarefa.save()


REGISTRY = {
    # "minha_automacao": minha_automacao,
}