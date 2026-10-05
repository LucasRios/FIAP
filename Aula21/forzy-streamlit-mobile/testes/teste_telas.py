"""
Testes de fumaça das telas do Forzy mobile, sem navegador (streamlit.testing).

Pré-requisito: a API (real ou simulada) respondendo em API_URL.
Rode a partir da raiz do front:  python -m testes.teste_telas
"""
import os
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).resolve().parent.parent
APP = str(RAIZ / "app.py")
sys.path.insert(0, str(RAIZ))
os.chdir(RAIZ)
os.environ.setdefault("API_URL", "http://localhost:8000")
os.environ.setdefault("API_KEY", "chave-local-dev")

falhas = 0


def novo(**estado) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=60)
    for chave, valor in estado.items():
        at.session_state[chave] = valor
    return at


def checar(rotulo: str, at: AppTest, condicao: bool = True, detalhe: str = "") -> None:
    global falhas
    ok = not at.exception and condicao
    falhas += 0 if ok else 1
    print(f"{'ok   ' if ok else 'FALHA'}  {rotulo} {detalhe}")
    for e in at.exception:
        print("       ", e.value)


def botao(at: AppTest, rotulo: str):
    return next(b for b in at.button if b.label == rotulo)


# 1. Cada página renderiza sem exceção
for pagina in ("equipamentos", "dashboard", "dados"):
    at = novo(pagina=pagina, tag_selecionada="MTR-007", modo_cadastro="novo").run()
    checar(f"página {pagina}", at)

at = novo(pagina="cadastro", tag_selecionada="", modo_cadastro="novo").run()
checar("cadastro (novo)", at, len(at.text_input) >= 3)
at = novo(pagina="cadastro", tag_selecionada="MTR-003", modo_cadastro="edicao").run()
checar("cadastro (ficha)", at, any("MTR-003" in m.value for m in at.markdown))

# 2. Deep link: a URL define página e motor na primeira execução
at = AppTest.from_file(APP, default_timeout=60)
at.query_params["pagina"] = "dashboard"
at.query_params["tag"] = "MTR-012"
at.run()
checar("deep link ?pagina=dashboard&tag=MTR-012", at,
       at.session_state["pagina"] == "dashboard" and at.session_state["tag_selecionada"] == "MTR-012")

# 3. Deep link malicioso ou inválido é ignorado
at = AppTest.from_file(APP, default_timeout=60)
at.query_params["pagina"] = "<script>"
at.query_params["tag"] = "../../etc"
at.run()
checar("deep link inválido cai no padrão", at,
       at.session_state["pagina"] == "equipamentos" and at.session_state["tag_selecionada"] == "")

# 4. Card da lista navega para o painel do motor
at = novo().run()
botao_painel = next(b for b in at.button if b.key == "painel_MTR-007")
botao_painel.click().run()
checar("card MTR-007 -> painel", at,
       at.session_state["pagina"] == "dashboard" and at.session_state["tag_selecionada"] == "MTR-007")

# 5. Busca filtra os cards (MTR-010 a MTR-019)
at = novo().run()
at.text_input(key="busca_equipamentos").input("MTR-01").run()
painel_keys = [b.key for b in at.button if (b.key or "").startswith("painel_")]
checar("busca 'MTR-01' filtra a lista", at, len(painel_keys) == 10, f"({len(painel_keys)} cards)")

# 6. Cadastro: grava, volta em modo edição e deixa o aviso para o toast
at = novo(pagina="cadastro", tag_selecionada="", modo_cadastro="novo").run()
at.text_input[0].set_value("MTR-099")
at.text_input[1].set_value("W22 Teste Mobile")
botao(at, "Salvar").click().run()
checar("cadastro -> salvar", at,
       at.session_state["modo_cadastro"] == "edicao" and at.session_state["tag_selecionada"] == "MTR-099")

print(f"\n{'Tudo certo.' if not falhas else f'{falhas} falha(s).'}")
sys.exit(1 if falhas else 0)
