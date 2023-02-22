import hashlib


def hash_password(raw_password):
    key = hashlib.sha256()
    key.update(raw_password.encode('utf-8'))
    return key.hexdigest()


def authenticate_user(user, password):
    return user["password"] == hash_password(password)


if __name__ == '__main__':
    print(hash_password("password"))
