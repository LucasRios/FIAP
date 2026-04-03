def authenticate_user(username, password):
    users = {
        "admin": {"password": "123", "role": "admin"},
        "aluno": {"password": "456", "role": "user"}
    }

    if username in users and users[username]["password"] == password:
        return users[username]

    return None