from langsmith import traceable

_HIERARQUIA: dict[str, dict[str, list[str]]] = {
    "Planta A": {
        "Linha 1": ["MTR-001", "MTR-002", "MTR-003", "MTR-004", "MTR-005"],
        "Linha 2": ["MTR-006", "MTR-007", "MTR-008", "MTR-009", "MTR-010"],
    },
    "Planta B": {
        "Utilidades":   ["MTR-011", "MTR-012", "MTR-013", "MTR-014", "MTR-015"],
        "Compressores": ["MTR-016", "MTR-017", "MTR-018", "MTR-019", "MTR-020"],
    },
}


@traceable(name="hierarquia_listar_plantas" , run_type="tool", tags=["forzy",  "plantas"])
def listar_plantas() -> list[str]:
    """
    Retorna a lista de plantas disponíveis (nível mais alto da hierarquia).
    Usada para popular o primeiro dropdown de navegação.
    """
    return sorted(_HIERARQUIA.keys())

@traceable(name="listar_areas" , run_type="tool", tags=["forzy",  "plantas"])
def listar_areas(planta: str) -> list[str]:
    """
    Retorna as áreas de uma planta específica.
    Retorna lista vazia se a planta não existir.
    Usada para popular o segundo dropdown após a seleção da planta.
    """
    if not planta or planta not in _HIERARQUIA:
        return []
    return sorted(_HIERARQUIA[planta].keys())

@traceable(  run_type="tool", tags=["forzy",  "plantas"])
def listar_equipamentos(planta: str, area: str) -> list[str]:
    """
    Retorna as TAGs dos equipamentos de uma área específica.
    Retorna lista vazia se planta ou área não existirem.
    Usada para popular o terceiro dropdown após a seleção da área.
    """
    if not planta or not area:
        return []
    return _HIERARQUIA.get(planta, {}).get(area, [])

@traceable( name="hierarquia_buscar_localizacao" , run_type="tool", tags=["forzy",  "plantas"])
def buscar_localizacao(tag: str) -> tuple[str, str]:
    """
    Dado uma TAG, retorna (planta, area) onde o equipamento está instalado.
    Retorna ("", "") se a TAG não for encontrada na hierarquia.
    """
    for planta, areas in _HIERARQUIA.items():
        for area, equips in areas.items():
            if tag in equips:
                return planta, area
    return "", ""
