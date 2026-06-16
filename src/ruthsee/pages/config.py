from nicegui import app, ui

from database import load_data, save_data
from layout import frame
from permissions import has_permission, require_permission


PAGINAS_INICIAIS = {
    'Dashboard': '/',
    'Agenda / Rotina': '/agenda',
    'Alunos': '/alunos',
    'Turmas': '/turmas',
    'Pais e responsáveis': '/pais',
    'Registros': '/registros',
    'Relatórios': '/relatorios',
    'Impressão/PDF': '/impressao',
    'Estratégias': '/estrategias',
}

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


def _login_usuario(user):
    return str(user.get('usuario') or user.get('email') or '').strip().lower()


def _preferencias_usuario(user, config):
    preferencias = user.get('preferencias') if user else {}
    if not isinstance(preferencias, dict):
        preferencias = {}
    return {
        'modo_escuro': preferencias.get('modo_escuro', config.get('modo_escuro', False)),
        'pagina_inicial': preferencias.get('pagina_inicial', '/'),
        'nome_completo_topo': preferencias.get('nome_completo_topo', False),
    }


def _pagina_label(rota):
    for label, pagina in PAGINAS_INICIAIS.items():
        if pagina == rota:
            return label
    return 'Dashboard'


def _paginas_permitidas():
    return {
        label: rota
        for label, rota in PAGINAS_INICIAIS.items()
        if has_permission(PAGINA_PERMISSAO.get(rota, 'view_dashboard'))
    }


def _salvar_usuario_logado(perfil, preferencias):
    user = app.storage.user
    config = load_data('config.json', {'modo_escuro': False})

    user.update(perfil)
    user['preferencias'] = preferencias

    if user.get('tipo') == 'admin_padrao':
        config.update({
            'nome': perfil['nome'],
            'foto': perfil['foto'],
            'bio': perfil['bio'],
            'modo_escuro': preferencias['modo_escuro'],
            'preferencias': {
                **(config.get('preferencias', {}) if isinstance(config.get('preferencias'), dict) else {}),
                **preferencias,
            },
        })
        save_data('config.json', config)
        return

    usuarios = load_data('usuarios.json', [])
    login_atual = _login_usuario(user)
    for index, usuario in enumerate(usuarios):
        if _login_usuario(usuario) == login_atual:
            usuario.update({
                'nome': perfil['nome'],
                'foto': perfil['foto'],
                'bio': perfil['bio'],
                'preferencias': preferencias,
            })
            usuarios[index] = usuario
            save_data('usuarios.json', usuarios)
            return


def render():
    with frame('Configurações'):
        if not require_permission('view_config'):
            return

        config = load_data('config.json', {'nome': 'Professor(a)', 'foto': '', 'cargo': 'Professor', 'bio': '', 'modo_escuro': False})
        user = app.storage.user
        preferencias = _preferencias_usuario(user, config)
        paginas_permitidas = _paginas_permitidas()

        perfil = {
            'nome': user.get('nome') or config.get('nome', 'Professor(a)'),
            'foto': user.get('foto') or '',
            'bio': user.get('bio') or '',
        }
        cargo = user.get('cargo', 'Professor')
        usuario_acesso = user.get('usuario') or user.get('email') or 'admin'

        ui.add_css('''
            .settings-hero {
                background: var(--app-happy) !important;
            }

            .settings-avatar {
                width: 5.75rem;
                height: 5.75rem;
                border-radius: 8px;
                object-fit: cover;
                border: 1px solid var(--app-border);
            }

            .settings-block {
                background: var(--app-surface-muted) !important;
                border: 1px solid var(--app-border);
                border-radius: 8px;
            }

            .settings-pref-line {
                background: var(--app-surface-muted) !important;
                border: 1px solid var(--app-border);
                border-radius: 8px;
            }

            .settings-preview {
                min-height: 7.5rem;
            }
        ''')

        with ui.column().classes('w-full max-w-5xl mx-auto gap-5'):
            with ui.row().classes('app-card-colorful settings-hero w-full items-center justify-between gap-5 p-6'):
                with ui.row().classes('items-center gap-5 min-w-0'):
                    foto_url = perfil['foto'].strip()
                    if foto_url:
                        ui.image(foto_url).classes('settings-avatar shrink-0')
                    else:
                        primeira_letra = perfil['nome'][0].upper() if perfil['nome'] else 'P'
                        ui.label(primeira_letra).classes('brand-badge w-24 h-24 flex items-center justify-center text-4xl font-black shrink-0')

                    with ui.column().classes('gap-2 min-w-0'):
                        ui.label('⚙️ Preferências pessoais').classes('app-muted text-sm font-black uppercase')
                        ui.label(perfil['nome']).classes('text-3xl font-black leading-tight line-clamp-1')
                        with ui.row().classes('items-center gap-2 flex-wrap'):
                            ui.label(f'Usuário: {usuario_acesso}').classes('app-pill text-xs font-black px-3 py-1')
                            ui.label(cargo).classes('app-pill text-xs font-black px-3 py-1')
                            ui.label('Tema escuro' if preferencias['modo_escuro'] else 'Tema claro').classes('app-pill text-xs font-black px-3 py-1')

                ui.icon('tune', size='3rem').classes('app-muted hidden sm:block')

            with ui.grid(columns=1).classes('w-full gap-5 lg:grid-cols-3'):
                with ui.card().classes('app-card w-full p-6 lg:col-span-2'):
                    ui.label('👤 Perfil de exibição').classes('text-xl font-black mb-1')
                    ui.label('Essas informações aparecem no topo do sistema e ajudam a equipe a identificar quem está usando.').classes('app-muted text-sm mb-5')

                    with ui.grid(columns=1).classes('w-full gap-4 md:grid-cols-2'):
                        nome_input = ui.input('Nome de exibição').props('outlined').classes('w-full').bind_value(perfil, 'nome')
                        ui.input('Usuário de acesso', value=usuario_acesso).props('outlined readonly').classes('w-full')
                        ui.input('Cargo / função', value=cargo).props('outlined readonly').classes('w-full')
                        foto_input = ui.input('URL da foto').props('outlined').classes('w-full').bind_value(perfil, 'foto')

                    bio_input = ui.textarea('Notas pessoais / apresentação curta').props('outlined autogrow').classes('w-full mt-4').bind_value(perfil, 'bio')

                    with ui.row().classes('settings-block w-full items-start gap-3 p-4 mt-5'):
                        ui.icon('info', size='sm').classes('tone-blue mt-1')
                        ui.label('O cargo e o usuário de acesso são administrados na tela de usuários para manter as permissões organizadas.').classes('app-muted text-sm leading-relaxed')

                with ui.card().classes('app-card w-full p-6'):
                    ui.label('✨ Prévia rápida').classes('text-xl font-black mb-4')
                    with ui.column().classes('settings-block settings-preview w-full items-center justify-center gap-3 p-5 text-center'):
                        if perfil['foto'].strip():
                            ui.image(perfil['foto'].strip()).classes('settings-avatar')
                        else:
                            ui.label(perfil['nome'][0].upper() if perfil['nome'] else 'P').classes('brand-badge w-20 h-20 flex items-center justify-center text-3xl font-black')
                        ui.label(perfil['nome']).classes('font-black text-lg leading-tight')
                        ui.label(cargo).classes('app-muted text-xs font-bold uppercase')

            with ui.card().classes('app-card w-full p-6'):
                ui.label('🎛️ Preferências do sistema').classes('text-xl font-black mb-1')
                ui.label('Estas opções ficam salvas somente para o seu usuário e serão aplicadas nos próximos acessos.').classes('app-muted text-sm mb-5')

                with ui.grid(columns=1).classes('w-full gap-4 md:grid-cols-2'):
                    with ui.column().classes('settings-pref-line gap-3 p-4'):
                        with ui.row().classes('items-center gap-3'):
                            ui.icon('contrast', size='sm').classes('tone-blue')
                            ui.label('Tema visual').classes('font-black')
                        tema_input = ui.radio(['Claro', 'Escuro'], value='Escuro' if preferencias['modo_escuro'] else 'Claro').props('inline')
                        ui.label('Escolha o modo que fica mais confortável para trabalhar por mais tempo.').classes('app-muted text-xs leading-relaxed')

                    with ui.column().classes('settings-pref-line gap-3 p-4'):
                        with ui.row().classes('items-center gap-3'):
                            ui.icon('home', size='sm').classes('tone-teal')
                            ui.label('Página inicial').classes('font-black')
                        pagina_input = ui.select(
                            list(paginas_permitidas.keys()),
                            value=_pagina_label(preferencias.get('pagina_inicial', '/')) if _pagina_label(preferencias.get('pagina_inicial', '/')) in paginas_permitidas else 'Dashboard',
                            label='Abrir após o login',
                        ).props('outlined dense').classes('w-full')
                        ui.label('Você pode entrar direto na área que mais usa no dia a dia.').classes('app-muted text-xs leading-relaxed')

                    with ui.column().classes('settings-pref-line gap-3 p-4'):
                        with ui.row().classes('items-center gap-3'):
                            ui.icon('badge', size='sm').classes('tone-amber')
                            ui.label('Nome no topo').classes('font-black')
                        nome_completo_input = ui.checkbox('Mostrar nome completo no cabeçalho', value=preferencias.get('nome_completo_topo', False))
                        ui.label('Desative para mostrar apenas o primeiro nome e deixar o cabeçalho mais compacto.').classes('app-muted text-xs leading-relaxed')

                    with ui.column().classes('settings-pref-line gap-3 p-4'):
                        with ui.row().classes('items-center gap-3'):
                            ui.icon('security', size='sm').classes('tone-green')
                            ui.label('Dados locais').classes('font-black')
                        ui.label('O sistema continua simples para uma escola pequena: os dados ficam em um banco SQLite local dentro da pasta data.').classes('app-muted text-sm leading-relaxed')

                def salvar_configuracoes():
                    novas_preferencias = {
                        'modo_escuro': tema_input.value == 'Escuro',
                        'pagina_inicial': paginas_permitidas.get(pagina_input.value, '/'),
                        'nome_completo_topo': bool(nome_completo_input.value),
                    }
                    _salvar_usuario_logado(perfil, novas_preferencias)

                    if novas_preferencias['modo_escuro']:
                        ui.dark_mode().enable()
                    else:
                        ui.dark_mode().disable()

                    ui.notify('Preferências salvas para o seu usuário. ✨', type='positive')

                with ui.row().classes('w-full justify-end gap-3 mt-6'):
                    ui.button('Voltar ao dashboard', icon='arrow_back', on_click=lambda: ui.navigate.to('/')).props('flat color=primary no-caps')
                    ui.button('Salvar preferências', icon='save', on_click=salvar_configuracoes).props('unelevated color=primary no-caps')
