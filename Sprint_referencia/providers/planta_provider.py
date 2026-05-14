# =============================================================================
# providers/planta_provider.py — Hierarquia física Planta → Área → Equipamento
#
# O que é este provider?
# ----------------------
# Representa a localização física dos motores na instalação industrial.
# A hierarquia é: Planta (instalação inteira) → Área (setor da planta)
#                 → Equipamento (motor identificado pela TAG)
#
# Exemplo real:
#   Planta A → Linha 1 → MTR-001
#   Planta B → Utilidades → MTR-003
#
# Em produção: substituir _HIERARQUIA por query a um banco de dados
# ou sistema de gestão de ativos (EAM / CMMS), como SAP PM ou IBM Maximo.
# =============================================================================


# ---------------------------------------------------------------------------
# _HIERARQUIA — estrutura de localização dos equipamentos
#
# Dicionário aninhado: { planta: { area: [lista de TAGs] } }
# As TAGs aqui devem corresponder às TAGs cadastradas no equipamento_provider.
# ---------------------------------------------------------------------------
_HIERARQUIA: dict[str, dict[str, list[str]]] = {
    "Planta A": {
        "Linha 1": ["MTR-001"],
        "Linha 2": ["MTR-002"],
    },
    "Planta B": {
        "Utilidades": ["MTR-003"],
    },
}


def listar_plantas() -> list[str]:
    """
    Retorna a lista de plantas disponíveis (nível mais alto da hierarquia).
    Usada para popular o primeiro dropdown de navegação.
    """
    return sorted(_HIERARQUIA.keys())


def listar_areas(planta: str) -> list[str]:
    """
    Retorna as áreas de uma planta específica.
    Retorna lista vazia se a planta não existir.
    Usada para popular o segundo dropdown após a seleção da planta.
    """
    if not planta or planta not in _HIERARQUIA:
        return []
    return sorted(_HIERARQUIA[planta].keys())


def listar_equipamentos(planta: str, area: str) -> list[str]:
    """
    Retorna as TAGs dos equipamentos de uma área específica.
    Retorna lista vazia se planta ou área não existirem.
    Usada para popular o terceiro dropdown após a seleção da área.
    """
    if not planta or not area:
        return []
    return _HIERARQUIA.get(planta, {}).get(area, [])


def buscar_localizacao(tag: str) -> tuple[str, str]:
    """
    Dado uma TAG, retorna (planta, area) onde o equipamento está instalado.
    Retorna ("", "") se a TAG não for encontrada na hierarquia.

    Útil para pré-selecionar os dropdowns quando navegamos para o dashboard
    a partir da lista de equipamentos com uma TAG já escolhida.
    """
    for planta, areas in _HIERARQUIA.items():
        for area, equips in areas.items():
            if tag in equips:
                return planta, area
    return "", ""
