# =============================================================================
# checklist_pre_apresentacao.py — Aula 25: Showcase, checklist automatizado
#
# Responsabilidade: script de linha de comando (introdutório, um único
# arquivo) que roda alguns dos itens do checklist da aula automaticamente,
# em vez de o aluno verificar cada item manualmente. Roda no dia anterior
# à apresentação, dentro da pasta do projeto.
#
# NOVO NESTA AULA: este arquivo inteiro. Reúne conceitos já vistos em
# aulas anteriores (variáveis de ambiente, .gitignore) só que agora usados
# para AUDITAR o projeto, e não para rodá-lo.
#
# Como rodar (dentro da pasta raiz do projeto do Sprint):
#   python checklist_pre_apresentacao.py
# =============================================================================

import os
import re

# Padrões de texto que NUNCA deveriam aparecer em código versionado —
# cada um indica um tipo diferente de segredo vazado.
PADROES_PROIBIDOS = {
    "Chave da Anthropic":        re.compile(r"sk-ant-[a-zA-Z0-9]+"),
    "Variável hardcoded":        re.compile(r'API_KEY\s*=\s*["\'][^"\']+["\']'),
    "URL local (não funciona em produção)": re.compile(r"http://localhost"),
}

# Extensões de arquivo que faz sentido varrer neste checklist.
EXTENSOES_VERIFICADAS = (".py", ".toml", ".env", ".yml", ".yaml")

# Pastas que não devem ser varridas (ambiente virtual, cache, etc.)
PASTAS_IGNORADAS = {".git", ".venv", "venv", "__pycache__", "node_modules"}


def verificar_segredos_no_codigo(raiz: str = ".") -> list[str]:
    """
    Percorre os arquivos do projeto procurando por padrões que indicam
    segredos ou URLs locais esquecidas no código.

    Returns:
        Lista de mensagens de alerta (vazia se nada suspeito foi encontrado).
    """
    alertas = []

    for pasta_atual, subpastas, arquivos in os.walk(raiz):
        # Remove pastas ignoradas da busca, "in-place", para o os.walk
        # não entrar nelas nas próximas iterações.
        subpastas[:] = [p for p in subpastas if p not in PASTAS_IGNORADAS]

        for nome_arquivo in arquivos:
            if not nome_arquivo.endswith(EXTENSOES_VERIFICADAS):
                continue

            caminho = os.path.join(pasta_atual, nome_arquivo)
            try:
                with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
                    conteudo = f.read()
            except OSError:
                continue

            for descricao, padrao in PADROES_PROIBIDOS.items():
                if padrao.search(conteudo):
                    alertas.append(f"[{descricao}] encontrado em {caminho}")

    return alertas


def verificar_gitignore(raiz: str = ".") -> list[str]:
    """
    Confere se o .gitignore existe e contém as entradas mínimas esperadas
    para um projeto de IA com Streamlit/FastAPI.
    """
    caminho_gitignore = os.path.join(raiz, ".gitignore")
    entradas_esperadas = [".env", "__pycache__", "secrets.toml"]

    if not os.path.exists(caminho_gitignore):
        return ["Arquivo .gitignore não encontrado na raiz do projeto."]

    with open(caminho_gitignore, "r", encoding="utf-8") as f:
        conteudo = f.read()

    faltando = [item for item in entradas_esperadas if item not in conteudo]
    return [f".gitignore não cobre: {item}" for item in faltando]


def verificar_requirements(raiz: str = ".") -> list[str]:
    """Confere se existe algum requirements.txt no projeto."""
    for pasta_atual, _, arquivos in os.walk(raiz):
        if "requirements.txt" in arquivos:
            return []
    return ["Nenhum requirements.txt encontrado no projeto."]


def rodar_checklist():
    """Executa todas as verificações e imprime um resumo no terminal."""
    print("=" * 60)
    print("CHECKLIST PRÉ-APRESENTAÇÃO — Aula 25")
    print("=" * 60)

    verificacoes = {
        "Segredos no código": verificar_segredos_no_codigo(),
        ".gitignore":         verificar_gitignore(),
        "requirements.txt":   verificar_requirements(),
    }

    algum_problema = False

    for nome_verificacao, problemas in verificacoes.items():
        print(f"\n{nome_verificacao}:")
        if not problemas:
            print("  OK — nenhum problema encontrado.")
        else:
            algum_problema = True
            for problema in problemas:
                print(f"  ATENÇÃO: {problema}")

    print("\n" + "=" * 60)
    if algum_problema:
        print("Resultado: existem pontos para corrigir antes da apresentação.")
    else:
        print("Resultado: nenhum problema automatizável encontrado. Bom showcase!")
    print("=" * 60)


# Protegido por __main__: só roda quando chamado diretamente no terminal,
# igual fizemos no scraper_nlp_provider.py da Aula 06.
if __name__ == "__main__":
    rodar_checklist()
