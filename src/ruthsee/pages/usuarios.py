import datetime

from nicegui import ui

from database import load_data, save_data
from layout import frame
from permissions import PERMISSION_LABELS, ROLE_PERMISSIONS, require_permission
from user_security import definir_senha, usuario_tem_senha


def _valor_filtro(valor, padrao='Todos'):
    if isinstance(valor, dict):
        return str(valor.get('label') or valor.get('value') or padrao)
    return str(valor or padrao)


def render():
    with frame('Gestão de Usuários'):
        if not require_permission('manage_users', description='Somente administradores podem criar usuários, alterar cargos e permissões.'):
            return

        usuarios = load_data('usuarios.json', [])
        editing_index = {'value': -1}
        cargos = ['Administrador', 'Coordenador', 'Professor', 'Assistente']

        ui.add_css('''
            .user-security-card {
                background: var(--app-surface-muted) !important;
                border: 1px solid var(--app-border);
                border-radius: 8px;
            }
        ''')

        def abrir_modal(user=None, index=-1):
            editing_index['value'] = index
            if user:
                nome_input.value = user.get('nome', '')
                usuario_input.value = user.get('usuario') or user.get('email', '')
                email_input.value = user.get('email', '')
                senha_input.value = ''
                cargo_input.value = user.get('cargo', 'Professor')
                foto_input.value = user.get('foto', '')
                dialog_title.set_text('Editar usuário 👥')
            else:
                nome_input.value = ''
                usuario_input.value = ''
                email_input.value = ''
                senha_input.value = ''
                cargo_input.value = 'Professor'
                foto_input.value = ''
                dialog_title.set_text('Novo usuário ✨')
            dialog.open()

        def salvar_usuario():
            criando = editing_index['value'] < 0
            senha_digitada = str(senha_input.value or '')
            if not nome_input.value or not usuario_input.value or (criando and not senha_digitada):
                ui.notify('Preencha nome, usuário e senha para novos acessos. 😊', type='warning')
                return

            usuario_acesso = usuario_input.value.strip()
            usuario_normalizado = usuario_acesso.lower()
            duplicado = any(
                i != editing_index['value']
                and (u.get('usuario') or u.get('email', '')).strip().lower() == usuario_normalizado
                for i, u in enumerate(usuarios)
            )
            if duplicado:
                ui.notify('Já existe um funcionário com este usuário de acesso.', type='warning')
                return

            usuario_anterior = usuarios[editing_index['value']] if editing_index['value'] >= 0 else {}
            dados = {
                'nome': nome_input.value.strip(),
                'usuario': usuario_acesso,
                'email': (email_input.value or '').strip(),
                'cargo': cargo_input.value,
                'foto': (foto_input.value or '').strip(),
                'preferencias': usuario_anterior.get('preferencias', {}) if editing_index['value'] >= 0 else {},
                'data_criacao': datetime.datetime.now().strftime('%d/%m/%Y'),
            }

            if senha_digitada:
                definir_senha(dados, senha_digitada)
            elif usuario_anterior.get('senha') and not usuario_anterior.get('senha_hash'):
                definir_senha(dados, usuario_anterior.get('senha'))
            else:
                for campo in ('senha_hash', 'senha', 'senha_atualizada_em'):
                    if campo in usuario_anterior:
                        dados[campo] = usuario_anterior[campo]

            if not usuario_tem_senha(dados):
                ui.notify('Defina uma senha para este usuário.', type='warning')
                return

            if editing_index['value'] >= 0:
                dados['data_criacao'] = usuario_anterior.get('data_criacao', dados['data_criacao'])
                usuarios[editing_index['value']] = dados
                ui.notify('Usuário atualizado com sucesso! ⭐', type='positive')
            else:
                usuarios.append(dados)
                ui.notify('Usuário criado com sucesso! ✨', type='positive')

            save_data('usuarios.json', usuarios)
            dialog.close()
            atualizar_lista()

        def confirmar_exclusao(user):
            with ui.dialog() as confirm_dialog, ui.card().classes('app-card w-full max-w-md p-6'):
                ui.label('Excluir usuário').classes('text-xl font-black text-red-600 mb-3')
                ui.label(f'Deseja apagar "{user["nome"]}"?').classes('app-muted text-sm')
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Cancelar', on_click=confirm_dialog.close).props('flat')
                    ui.button('Excluir', icon='delete', on_click=lambda: apagar_usuario(user, confirm_dialog)).props('unelevated color=red')
            confirm_dialog.open()

        def apagar_usuario(user, confirm_dialog):
            usuarios.remove(user)
            save_data('usuarios.json', usuarios)
            ui.notify('Usuário removido.', type='warning')
            confirm_dialog.close()
            atualizar_lista()

        with ui.dialog() as dialog, ui.card().classes('app-card w-full max-w-md p-6'):
            dialog_title = ui.label('Novo usuário ✨').classes('text-2xl font-black mb-4')
            nome_input = ui.input('Nome completo *').props('outlined').classes('w-full mb-3')
            usuario_input = ui.input('Usuário de acesso *').props('outlined').classes('w-full mb-3')
            email_input = ui.input('E-mail institucional (opcional)').props('outlined').classes('w-full mb-3')
            senha_input = ui.input('Senha / nova senha', password=True, password_toggle_button=True).props('outlined').classes('w-full mb-3')
            cargo_input = ui.select(cargos, label='Cargo *').props('outlined').classes('w-full mb-4')
            foto_input = ui.input('URL da foto (opcional)').props('outlined').classes('w-full mb-4')
            with ui.row().classes('w-full justify-end gap-2 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).props('flat')
                ui.button('Salvar ✨', icon='check', on_click=salvar_usuario).props('unelevated color=primary')

        with ui.column().classes('w-full gap-5'):
            with ui.row().classes('app-card-colorful w-full items-center justify-between gap-5 p-6'):
                with ui.column().classes('gap-2'):
                    ui.label('👥 Equipe escolar').classes('app-muted text-sm font-black uppercase')
                    ui.label('Pessoas que cuidam da rotina').classes('text-3xl font-black')
                    ui.label('Organize acessos de professores, coordenação e administração.').classes('app-muted text-sm')
                ui.button('Novo usuário ✨', icon='person_add', on_click=lambda: abrir_modal()).props('unelevated color=primary')

            with ui.card().classes('app-card w-full p-5'):
                ui.label('🔐 Regras de acesso por cargo').classes('text-xl font-black mb-1')
                ui.label('Use o menor nível de acesso possível para proteger dados de alunos e famílias.').classes('app-muted text-sm mb-4')
                with ui.grid(columns=1).classes('w-full gap-3 lg:grid-cols-4'):
                    for cargo_nome in cargos:
                        permissoes = ROLE_PERMISSIONS.get(cargo_nome, set())
                        with ui.column().classes('user-security-card w-full gap-2 p-4'):
                            ui.label(cargo_nome).classes('font-black')
                            ui.label(f'{len(permissoes)} permissões').classes('app-muted text-xs font-bold uppercase')
                            with ui.row().classes('gap-1 flex-wrap'):
                                for permissao, label in PERMISSION_LABELS.items():
                                    if permissao in permissoes:
                                        ui.label(label).classes('app-pill text-[10px] font-bold px-2 py-1')

            with ui.row().classes('app-toolbar w-full justify-between items-center gap-4 p-4'):
                with ui.row().classes('flex-1 items-center gap-3 flex-wrap'):
                    pesquisa_input = ui.input(placeholder='Pesquisar por nome, e-mail ou cargo').props('outlined dense').classes('w-full md:max-w-md flex-1')
                    with pesquisa_input.add_slot('prepend'):
                        ui.icon('search').classes('app-muted')
                    cargo_filter = ui.select(['Todos'] + cargos, value='Todos', label='Cargo').props('outlined dense').classes('w-full sm:w-48')
            container_lista = ui.column().classes('w-full gap-3')

        def atualizar_lista():
            container_lista.clear()
            termo = (pesquisa_input.value or '').strip().lower()
            cargo_selecionado = _valor_filtro(cargo_filter.value)
            filtrados = [
                usuario for usuario in usuarios
                if (cargo_selecionado == 'Todos' or usuario.get('cargo') == cargo_selecionado)
                and (not termo or termo in ' '.join([
                    usuario.get('nome', ''),
                    usuario.get('usuario', ''),
                    usuario.get('email', ''),
                    usuario.get('cargo', ''),
                ]).lower())
            ]
            with container_lista:
                if not filtrados:
                    with ui.column().classes('app-card w-full items-center justify-center gap-3 py-12 text-center'):
                        ui.label('🔎').classes('text-5xl')
                        ui.label('Nenhum usuário encontrado').classes('text-xl font-black')
                        ui.label('Tente outra busca ou crie um novo acesso.').classes('app-muted text-sm')

                for i, usuario in enumerate(usuarios):
                    if usuario not in filtrados:
                        continue

                    cargo = usuario.get('cargo', 'Professor')
                    emoji = {'Administrador': '🛡️', 'Coordenador': '🧭', 'Professor': '🍎', 'Assistente': '🤝'}.get(cargo, '👤')
                    primeira_letra = usuario.get('nome', 'U')[0].upper()
                    foto_url = usuario.get('foto', '').strip()

                    with ui.card().classes('app-card w-full p-4 flex-row items-center justify-between'):
                        with ui.row().classes('items-center gap-4 min-w-0'):
                            if foto_url:
                                ui.image(foto_url).classes('w-12 h-12 rounded-lg object-cover')
                            else:
                                ui.avatar(primeira_letra).classes('brand-badge text-white font-black w-12 h-12')
                            with ui.column().classes('gap-0 min-w-0'):
                                ui.label(usuario.get('nome', 'Sem nome')).classes('font-black text-lg line-clamp-1')
                                usuario_acesso = usuario.get('usuario') or usuario.get('email', 'sem-usuario')
                                email_info = usuario.get('email', '')
                                ui.label(f'Usuário: {usuario_acesso}').classes('app-muted text-sm line-clamp-1')
                                if email_info:
                                    ui.label(email_info).classes('app-muted text-xs line-clamp-1')

                        with ui.row().classes('items-center gap-3'):
                            ui.label(f'{emoji} {cargo}').classes('app-pill text-xs font-black px-3 py-1 hidden sm:block')
                            ui.button(icon='edit', on_click=lambda i=i, u=usuario: abrir_modal(u, i)).props('flat color=primary round size=sm').tooltip('Editar')
                            ui.button(icon='delete', on_click=lambda u=usuario: confirmar_exclusao(u)).props('flat color=red round size=sm').tooltip('Remover')

        pesquisa_input.on_value_change(lambda _: atualizar_lista())
        cargo_filter.on_value_change(lambda _: atualizar_lista())
        atualizar_lista()
