from providers.auth_provider import authenticate_user

def login_user(username: str, password: str):
    """
    Pipeline de autenticação com validações de negócio.
    """

    # 1. Validação básica
    if not username or not password:
        return {"success": False, "error": "Credenciais inválidas"}

    # 2. Provider (fonte de verdade)
    user_data = authenticate_user(username, password)

    if not user_data:
        return {"success": False, "error": "Usuário ou senha incorretos"}

    # 3. Regra de negócio (exemplo)
    if user_data.get("blocked"):
        return {"success": False, "error": "Usuário bloqueado"}

    return {
        "success": True,
        "username": username,
        "role": user_data["role"]
    }


def logout_user():
    """
    Pipeline de logout (pode evoluir para logs, auditoria, etc)
    """
    return {"success": True}