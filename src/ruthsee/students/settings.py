# Onde o usuário cai após logar
LOGIN_REDIRECT_URL = 'core:home'

# Onde o usuário cai após deslogar
LOGOUT_REDIRECT_URL = 'core:home'

# URL da página de login (para o @login_required saber para onde mandar)
LOGIN_URL = 'login'
# ruthsee/settings.py

# ADICIONE A BARRA INICIAL AQUI:
STATIC_URL = '/static/'  

# Garanta que o STATICFILES_DIRS esteja apontando para a pasta correta
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"