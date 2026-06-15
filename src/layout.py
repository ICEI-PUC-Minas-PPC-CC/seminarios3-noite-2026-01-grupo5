from contextlib import contextmanager

from nicegui import app, ui

from database import load_data, save_data
from permissions import has_permission
from theme import add_app_theme


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


def _salvar_preferencias_usuario(user, config, preferencias):
    user['preferencias'] = preferencias

    if user.get('tipo') == 'admin_padrao':
        config['modo_escuro'] = bool(preferencias.get('modo_escuro'))
        config['preferencias'] = {
            **(config.get('preferencias', {}) if isinstance(config.get('preferencias'), dict) else {}),
            **preferencias,
        }
        save_data('config.json', config)
        return

    usuarios = load_data('usuarios.json', [])
    login_atual = _login_usuario(user)
    for index, usuario in enumerate(usuarios):
        if _login_usuario(usuario) == login_atual:
            usuario['preferencias'] = preferencias
            usuarios[index] = usuario
            save_data('usuarios.json', usuarios)
            return

    config['modo_escuro'] = bool(preferencias.get('modo_escuro'))
    config['preferencias'] = {
        **(config.get('preferencias', {}) if isinstance(config.get('preferencias'), dict) else {}),
        **preferencias,
    }
    save_data('config.json', config)


@contextmanager
def frame(nav_title: str):
    config = load_data('config.json', {'modo_escuro': False})
    add_app_theme()
    user = app.storage.user
    preferencias = _preferencias_usuario(user, config)
    dark = ui.dark_mode(preferencias.get('modo_escuro'))

    if not user.get('nome'):
        ui.navigate.to('/login')
        with ui.column().classes('hidden'):
            yield
        return

    nome_usuario = user.get('nome', 'Usuário')
    cargo_usuario = user.get('cargo', 'Professor')
    foto_usuario = user.get('foto', '').strip()
    nome_topo = nome_usuario if preferencias.get('nome_completo_topo') else nome_usuario.split(' ')[0]

    def toggle_theme():
        novo_modo = not dark.value
        if not novo_modo:
            dark.disable()
        else:
            dark.enable()
        preferencias['modo_escuro'] = novo_modo
        _salvar_preferencias_usuario(user, config, preferencias)
        theme_button.props(f'icon={"light_mode" if novo_modo else "dark_mode"}')

    def fazer_logout():
        app.storage.user.clear()
        ui.navigate.to('/login')

    page_emojis = {
        'Dashboard': '🏫',
        'Agenda / Rotina do Dia': '🗓️',
        'Alunos': '☀️',
        'Turmas': '🏷️',
        'Prontuário do Aluno': '📁',
        'Pais e Responsáveis': '☎️',
        'Registros de Acompanhamento': '📝',
        'Relatórios': '📊',
        'Impressão/PDF': '🖨️',
        'Biblioteca de Estratégias': '💡',
        'Gestão de Usuários': '👥',
        'Administração do Sistema': '📣',
        'Configurações': '⚙️',
    }
    page_emoji = page_emojis.get(nav_title, '✨')

    with ui.header(elevated=False).classes('app-header fixed top-0 left-0 right-0 justify-between items-center px-6 py-3'):
        with ui.row().classes('items-center gap-4'):
            ui.button(on_click=lambda: left_drawer.toggle(), icon='menu').props('flat round').classes('app-muted')
            with ui.row().classes('items-center gap-3'):
                ui.image('/assets/ruth-see-logo.png').classes('w-11 h-11 rounded-lg object-contain bg-white p-1')
                with ui.column().classes('gap-0'):
                    ui.label('Ruth See Escola').classes('text-xl font-black leading-tight')
                    ui.label('Rotina escolar com carinho').classes('app-muted text-[11px] font-bold uppercase hidden sm:block')

        with ui.row().classes('items-center gap-4'):
            theme_icon = 'light_mode' if preferencias.get('modo_escuro') else 'dark_mode'
            theme_button = ui.button(icon=theme_icon, on_click=toggle_theme).props('flat round').classes('app-muted').tooltip('Alternar tema')

            with ui.row().classes('items-center gap-2 cursor-pointer'):
                with ui.column().classes('gap-0 items-end hidden md:flex'):
                    ui.label(nome_topo).classes('font-bold leading-none')
                    ui.label(cargo_usuario).classes('app-muted text-[10px] uppercase')

                if foto_usuario:
                    ui.image(foto_usuario).classes('w-10 h-10 rounded-full object-cover')
                else:
                    ui.avatar(nome_usuario[0].upper()).classes('bg-primary text-white font-bold w-10 h-10')

                with ui.menu():
                    ui.menu_item('Sair do Sistema', on_click=fazer_logout).classes('text-red-600 font-bold')

    with ui.left_drawer(elevated=False).classes('app-drawer flex flex-col justify-between') as left_drawer:
        with ui.column().classes('w-full p-4 gap-2 items-stretch'):
            ui.label('MENU PRINCIPAL ✨').classes('app-muted text-xs font-bold')

            def menu_btn(emoji, label, icon, route):
                item = ui.row().classes('menu-link items-center justify-start').on('click', lambda r=route: ui.navigate.to(r))
                with item:
                    ui.icon(icon).classes('menu-link-icon')
                    ui.label(f'{emoji} {label}').classes('menu-link-text')

            if has_permission('view_dashboard'):
                menu_btn('🏫', 'Dashboard', 'space_dashboard', '/')
            if has_permission('view_agenda'):
                menu_btn('🗓️', 'Agenda', 'event_note', '/agenda')
            if has_permission('view_alunos'):
                menu_btn('☀️', 'Alunos', 'face', '/alunos')
            if has_permission('view_turmas'):
                menu_btn('🏷️', 'Turmas', 'class', '/turmas')
            if has_permission('view_pais'):
                menu_btn('☎️', 'Pais', 'contact_phone', '/pais')
            if has_permission('view_registros'):
                menu_btn('📝', 'Registros', 'edit_note', '/registros')
            if has_permission('view_relatorios'):
                menu_btn('📊', 'Relatórios', 'analytics', '/relatorios')
            if has_permission('view_impressao'):
                menu_btn('🖨️', 'Impressão/PDF', 'print', '/impressao')
            if has_permission('view_estrategias'):
                menu_btn('💡', 'Estratégias', 'auto_awesome', '/estrategias')

            if has_permission('view_admin') or has_permission('manage_users'):
                ui.separator().classes('my-2')
                ui.label('GESTÃO 🤝').classes('app-muted text-xs font-bold')
                if has_permission('manage_users'):
                    menu_btn('👥', 'Usuários', 'people', '/usuarios')
                if has_permission('view_admin'):
                    menu_btn('📣', 'Administração', 'admin_panel_settings', '/admin')

        with ui.column().classes('w-full p-4 items-stretch'):
            if has_permission('view_config'):
                menu_btn('⚙️', 'Configurações', 'tune', '/config')

    with ui.column().classes('w-full max-w-7xl mx-auto px-5 md:px-8 py-6 mt-16 gap-6'):
        with ui.row().classes('items-center gap-3'):
            ui.label(page_emoji).classes('emoji-badge')
            ui.label(nav_title).classes('app-page-title')
        yield
