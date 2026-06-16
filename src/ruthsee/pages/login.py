from nicegui import app, ui

from auth import get_admin_credentials
from database import load_data, save_data
from permissions import permissoes_do_cargo
from theme import add_app_theme
from user_security import migrar_senha_legada, senha_confere


PAGINA_PERMISSAO = {
    '/': 'view_dashboard',
    '/agenda': 'view_agenda',
    '/alunos': 'view_alunos',
    '/turmas': 'view_turmas',
    '/pais': 'view_pais',
    '/registros': 'view_registros',
    '/relatorios': 'view_relatorios',
    '/impressao': 'view_impressao',
    '/estrategias': 'view_estrategias',
}


def render():
    app.storage.user.clear()

    config = load_data('config.json', {'modo_escuro': False})
    usuarios = load_data('usuarios.json', [])
    add_app_theme()

    if config.get('modo_escuro'):
        ui.dark_mode().enable()
    else:
        ui.dark_mode().disable()

    ui.add_css('''
        .login-shell {
            background:
                linear-gradient(135deg, color-mix(in srgb, var(--app-primary) 12%, transparent), transparent 38%),
                linear-gradient(315deg, color-mix(in srgb, var(--app-teal) 16%, transparent), transparent 44%),
                var(--app-bg);
        }

        .login-card {
            position: relative;
            width: min(455px, calc(100vw - 2rem));
        }

        .login-form-panel {
            background:
                radial-gradient(circle at top right, color-mix(in srgb, var(--app-teal) 13%, transparent), transparent 34%),
                radial-gradient(circle at bottom left, color-mix(in srgb, var(--app-primary) 10%, transparent), transparent 36%),
                var(--app-surface) !important;
        }

        .login-form-inner {
            width: 100%;
        }

        .login-logo-frame {
            width: 5.35rem;
            height: 5.35rem;
            border-radius: 8px;
            background: white;
            object-fit: contain;
            padding: 0.45rem;
            border: 1px solid var(--app-border);
            box-shadow: var(--app-soft-shadow);
        }

        .login-mini-note {
            background: var(--app-surface-muted) !important;
            border: 1px solid var(--app-border);
            border-radius: 8px;
        }

        .login-access-pill {
            background: color-mix(in srgb, var(--app-primary) 12%, transparent);
            border: 1px solid color-mix(in srgb, var(--app-primary) 22%, transparent);
            border-radius: 999px;
            color: var(--app-primary-strong) !important;
        }

        @media (max-width: 640px) {
            .login-card {
                width: min(100%, calc(100vw - 1.25rem));
            }
        }
    ''')

    def _login_usuario(usuario):
        return str(usuario or '').strip().lower()

    def _preferencias(usuario):
        preferencias = usuario.get('preferencias') or {}
        return preferencias if isinstance(preferencias, dict) else {}

    def _pagina_inicial(usuario):
        rotas_validas = {'/', '/agenda', '/alunos', '/turmas', '/pais', '/registros', '/relatorios', '/impressao', '/estrategias'}
        pagina = _preferencias(usuario).get('pagina_inicial', '/')
        permissao = PAGINA_PERMISSAO.get(pagina)
        if pagina in rotas_validas and permissao in permissoes_do_cargo(usuario.get('cargo', 'Professor')):
            return pagina
        return '/'

    with ui.row().classes('login-shell w-full min-h-screen items-center justify-center p-4'):
        with ui.row().classes('app-card login-card overflow-hidden'):
            with ui.column().classes('login-form-panel w-full p-7 md:p-8 items-center justify-center'):
                with ui.column().classes('login-form-inner items-center'):
                    ui.image('/assets/ruth-see-logo.png').classes('login-logo-frame mb-4')
                    ui.label('Acesso da equipe').classes('login-access-pill text-xs font-black px-3 py-1 mb-4')
                    ui.label('Bem-vindo(a)').classes('text-3xl font-black mb-1 text-center leading-tight')
                    ui.label('Entre para acompanhar a rotina escolar.').classes('app-muted mb-5 text-center text-sm')

                    with ui.row().classes('login-mini-note w-full items-center gap-3 p-3 mb-4'):
                        ui.icon('verified_user', size='sm').classes('tone-teal')
                        ui.label('Use seu usuário de acesso e senha cadastrados pela coordenação.').classes('app-muted text-xs font-bold leading-snug')

                    usuario_input = ui.input('Usuário').classes('w-full mb-3').props('outlined autocomplete=username')
                    with usuario_input.add_slot('prepend'):
                        ui.icon('person').classes('app-muted')

                    senha_input = ui.input('Senha', password=True, password_toggle_button=True).classes('w-full mb-5').props('outlined autocomplete=current-password')
                    with senha_input.add_slot('prepend'):
                        ui.icon('lock').classes('app-muted')

                    def fazer_login():
                        login = usuario_input.value
                        senha = senha_input.value

                        if not login or not senha:
                            ui.notify('Por favor, preencha todos os campos. 😊', type='warning')
                            return

                        admin_usuario, admin_password = get_admin_credentials()
                        if _login_usuario(login) == _login_usuario(admin_usuario) and senha == admin_password:
                            usuario_admin = {
                                'nome': config.get('nome') or 'Administrador Padrão',
                                'usuario': admin_usuario,
                                'email': '',
                                'cargo': 'Administrador',
                                'foto': config.get('foto', ''),
                                'bio': config.get('bio', ''),
                                'tipo': 'admin_padrao',
                                'preferencias': {
                                    **(config.get('preferencias', {}) if isinstance(config.get('preferencias'), dict) else {}),
                                    'modo_escuro': bool(config.get('modo_escuro')),
                                },
                            }
                            app.storage.user.update(usuario_admin)
                            ui.notify('Login de administrador realizado! ✨', type='positive')
                            ui.navigate.to(_pagina_inicial(usuario_admin))
                            return

                        usuario_valido = next(
                            (
                                u for u in usuarios
                                if _login_usuario(u.get('usuario') or u.get('email')) == _login_usuario(login)
                                and senha_confere(u, senha)
                            ),
                            None,
                        )

                        if usuario_valido:
                            usuario_alterado = False
                            if not usuario_valido.get('usuario'):
                                usuario_valido['usuario'] = usuario_valido.get('email', '')
                                usuario_alterado = True
                            if migrar_senha_legada(usuario_valido, senha):
                                usuario_alterado = True
                            if usuario_alterado:
                                save_data('usuarios.json', usuarios)
                            app.storage.user.update(usuario_valido)
                            primeiro_nome = usuario_valido.get('nome', 'Usuário').split(' ')[0]
                            ui.notify(f'Bem-vindo(a), {primeiro_nome}! ⭐', type='positive')
                            ui.navigate.to(_pagina_inicial(usuario_valido))
                        else:
                            ui.notify('Usuário ou senha incorretos.', type='negative')

                    senha_input.on('keydown.enter', lambda _: fazer_login())
                    usuario_input.on('keydown.enter', lambda _: fazer_login())

                    ui.button('Entrar no sistema', icon='login', on_click=fazer_login).classes('w-full py-3 text-base font-bold mb-4').props('unelevated color=primary no-caps')
                    ui.label('Dados salvos localmente em banco SQLite.').classes('app-muted text-xs text-center')
