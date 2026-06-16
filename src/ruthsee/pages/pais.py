from nicegui import ui

from database import load_data, save_data
from layout import frame
from permissions import has_permission, require_permission
from student_links import aluno_por_id, garantir_ids_alunos, id_aluno_por_nome, item_vinculado_ao_aluno, nome_aluno_vinculado, opcoes_alunos


def _texto(valor, padrao='Não informado'):
    valor = str(valor or '').strip()
    return valor if valor else padrao


def _telefone_limpo(valor):
    return ''.join(ch for ch in str(valor or '') if ch.isdigit())


def _valor_filtro(valor, padrao='Todos'):
    if isinstance(valor, dict):
        return str(valor.get('label') or valor.get('value') or padrao)
    return str(valor or padrao)


def render():
    with frame('Pais e Responsáveis'):
        if not require_permission('view_pais'):
            return

        responsaveis = load_data('pais.json', [])
        alunos = load_data('alunos.json', [])
        if garantir_ids_alunos(alunos):
            save_data('alunos.json', alunos)

        alterou_vinculos = False
        for responsavel in responsaveis:
            if not responsavel.get('aluno_id'):
                aluno_id = id_aluno_por_nome(alunos, responsavel.get('aluno'))
                if aluno_id:
                    responsavel['aluno_id'] = aluno_id
                    responsavel['aluno'] = nome_aluno_vinculado(alunos, responsavel)
                    alterou_vinculos = True
        if alterou_vinculos:
            save_data('pais.json', responsaveis)

        editing_index = {'value': -1}
        pode_gerir = has_permission('manage_pais')

        ui.add_css('''
            .parent-card {
                min-height: 280px;
                cursor: default;
                transition: transform 160ms ease, border-color 160ms ease;
            }

            .parent-card:hover {
                transform: translateY(-2px);
                border-color: var(--app-teal);
            }

            .contact-line {
                background: var(--app-surface-muted) !important;
                border-radius: 8px;
            }
        ''')

        def get_alunos_options(extra_aluno=''):
            return opcoes_alunos(alunos)

        def get_alunos_filter_options():
            return {'Todos': 'Todos', **get_alunos_options()}

        def get_parentescos_options():
            parentescos = {item.get('parentesco', '').strip() for item in responsaveis if item.get('parentesco', '').strip()}
            return ['Todos'] + sorted(parentescos)

        def get_contato_options():
            return ['Todos', 'Com WhatsApp', 'Com e-mail', 'Sem contato']

        def responsaveis_filtrados():
            termo = (pesquisa_input.value or '').strip().lower()
            aluno_selecionado = _valor_filtro(aluno_filter.value)
            parentesco_selecionado = _valor_filtro(parentesco_filter.value)
            contato_selecionado = _valor_filtro(contato_filter.value)
            filtrados = []

            for index, responsavel in enumerate(responsaveis):
                texto_busca = ' '.join([
                    responsavel.get('nome', ''),
                    nome_aluno_vinculado(alunos, responsavel),
                    responsavel.get('parentesco', ''),
                    responsavel.get('telefone', ''),
                    responsavel.get('email', ''),
                    responsavel.get('observacoes', ''),
                ]).lower()

                if termo and termo not in texto_busca:
                    continue
                aluno_filtro = aluno_por_id(alunos, aluno_selecionado)
                if aluno_selecionado != 'Todos' and (not aluno_filtro or not item_vinculado_ao_aluno(responsavel, aluno_filtro)):
                    continue
                if parentesco_selecionado != 'Todos' and responsavel.get('parentesco') != parentesco_selecionado:
                    continue

                tem_whatsapp = bool(_telefone_limpo(responsavel.get('whatsapp') or responsavel.get('telefone')))
                tem_email = bool((responsavel.get('email') or '').strip())
                if contato_selecionado == 'Com WhatsApp' and not tem_whatsapp:
                    continue
                if contato_selecionado == 'Com e-mail' and not tem_email:
                    continue
                if contato_selecionado == 'Sem contato' and (tem_whatsapp or tem_email):
                    continue

                filtrados.append((index, responsavel))

            return filtrados

        def atualizar_opcoes_filtros():
            filtros = [
                (aluno_filter, get_alunos_filter_options()),
                (parentesco_filter, get_parentescos_options()),
                (contato_filter, get_contato_options()),
            ]

            for filtro, opcoes in filtros:
                valor_atual = _valor_filtro(filtro.value)
                filtro.options = opcoes
                filtro.value = valor_atual if valor_atual in opcoes else 'Todos'
                filtro.update()

        def atualizar_resumo():
            pass

        def abrir_modal(responsavel=None, index=-1):
            if not pode_gerir:
                ui.notify('Seu cargo não permite alterar contatos familiares.', type='warning')
                return
            editing_index['value'] = index

            nome_input.value = responsavel.get('nome', '') if responsavel else ''
            aluno_atual_id = ''
            if responsavel:
                aluno_atual_id = responsavel.get('aluno_id') or id_aluno_por_nome(alunos, responsavel.get('aluno'))
            aluno_input.options = get_alunos_options()
            aluno_input.value = aluno_atual_id or (next(iter(aluno_input.options), None) if aluno_input.options else None)
            aluno_input.update()
            parentesco_input.value = responsavel.get('parentesco', 'Responsável') if responsavel else 'Responsável'
            telefone_input.value = responsavel.get('telefone', '') if responsavel else ''
            whatsapp_input.value = responsavel.get('whatsapp', '') if responsavel else ''
            email_input.value = responsavel.get('email', '') if responsavel else ''
            obs_input.value = responsavel.get('observacoes', '') if responsavel else ''

            dialog_title.set_text('Editar contato' if responsavel else 'Novo contato familiar')
            dialog.open()

        def salvar_responsavel():
            aluno_selecionado = _valor_filtro(aluno_input.value, '')
            aluno_vinculado = aluno_por_id(alunos, aluno_selecionado)

            if not nome_input.value or not aluno_vinculado:
                ui.notify('Nome do responsável e aluno são obrigatórios.', type='warning')
                return

            dados = {
                'nome': nome_input.value.strip(),
                'aluno_id': aluno_vinculado.get('id'),
                'aluno': aluno_vinculado.get('nome', ''),
                'parentesco': parentesco_input.value,
                'telefone': (telefone_input.value or '').strip(),
                'whatsapp': (whatsapp_input.value or '').strip(),
                'email': (email_input.value or '').strip(),
                'observacoes': (obs_input.value or '').strip(),
            }

            if editing_index['value'] >= 0:
                responsaveis[editing_index['value']] = dados
                ui.notify('Contato atualizado com sucesso.', type='positive')
            else:
                responsaveis.append(dados)
                ui.notify('Contato familiar cadastrado.', type='positive')

            save_data('pais.json', responsaveis)
            dialog.close()
            atualizar_opcoes_filtros()
            atualizar_resumo()
            atualizar_lista()

        def confirmar_exclusao(responsavel):
            if not pode_gerir:
                ui.notify('Seu cargo não permite excluir contatos familiares.', type='warning')
                return
            with ui.dialog() as confirm_dialog, ui.card().classes('app-card w-full max-w-md p-6'):
                ui.label('Excluir contato').classes('text-xl font-black text-red-600 mb-3')
                ui.label(f'Deseja apagar "{responsavel["nome"]}"?').classes('app-muted text-sm')
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Cancelar', on_click=confirm_dialog.close).props('flat')
                    ui.button('Excluir', icon='delete', on_click=lambda: apagar_responsavel(responsavel, confirm_dialog)).props('unelevated color=red')
            confirm_dialog.open()

        def apagar_responsavel(responsavel, confirm_dialog):
            responsaveis.remove(responsavel)
            save_data('pais.json', responsaveis)
            ui.notify('Contato removido.', type='warning')
            confirm_dialog.close()
            atualizar_opcoes_filtros()
            atualizar_resumo()
            atualizar_lista()

        with ui.dialog() as dialog, ui.card().classes('app-card w-full max-w-3xl p-0 overflow-hidden'):
            with ui.row().classes('w-full items-center justify-between gap-4 p-6 soft-teal'):
                with ui.column().classes('gap-1'):
                    dialog_title = ui.label('Novo contato familiar').classes('text-2xl font-black')
                    ui.label('Guarde os contatos principais para facilitar recados e alinhamentos.').classes('app-muted text-sm')
                ui.button(icon='close', on_click=dialog.close).props('flat round').classes('app-muted')

            with ui.column().classes('w-full gap-4 p-6'):
                with ui.grid(columns=2).classes('w-full gap-4'):
                    nome_input = ui.input('Nome do responsável *').props('outlined').classes('w-full')
                    aluno_input = ui.select(get_alunos_options(), label='Aluno vinculado *').props('outlined').classes('w-full')
                    parentesco_input = ui.select(['Mãe', 'Pai', 'Avó/Avô', 'Tia/Tio', 'Responsável'], value='Responsável', label='Parentesco').props('outlined').classes('w-full')
                    telefone_input = ui.input('Telefone').props('outlined').classes('w-full')
                    whatsapp_input = ui.input('WhatsApp').props('outlined').classes('w-full')
                    email_input = ui.input('E-mail').props('outlined').classes('w-full')
                obs_input = ui.textarea('Observações de comunicação').props('outlined autogrow').classes('w-full')

            with ui.row().classes('w-full justify-end gap-3 p-6 soft-blue'):
                ui.button('Cancelar', on_click=dialog.close).props('flat')
                ui.button('Salvar contato', icon='check', on_click=salvar_responsavel).props('unelevated color=primary')

        with ui.column().classes('w-full gap-5'):
            with ui.row().classes('app-card-colorful w-full items-center justify-between gap-5 p-6'):
                with ui.column().classes('gap-2'):
                    ui.label('☎️ Comunicação com famílias').classes('app-muted text-sm font-black uppercase')
                    ui.label('Contatos de pais e responsáveis').classes('text-3xl font-black leading-tight')
                    ui.label('Centralize telefones, WhatsApp e e-mails para recados importantes da escola.').classes('app-muted text-sm')
                if pode_gerir:
                    ui.button('Novo contato', icon='person_add', on_click=lambda: abrir_modal()).props('unelevated color=primary')

            with ui.row().classes('app-toolbar w-full items-center justify-between gap-4 p-4'):
                with ui.row().classes('flex-1 items-center gap-3 flex-wrap'):
                    pesquisa_input = ui.input(placeholder='Buscar por responsável, aluno, telefone ou e-mail').props('outlined dense').classes('w-full md:max-w-md flex-1')
                    with pesquisa_input.add_slot('prepend'):
                        ui.icon('search').classes('app-muted')
                    aluno_filter = ui.select(get_alunos_filter_options(), value='Todos', label='Aluno').props('outlined dense').classes('w-full sm:w-52')
                    parentesco_filter = ui.select(get_parentescos_options(), value='Todos', label='Parentesco').props('outlined dense').classes('w-full sm:w-44')
                    contato_filter = ui.select(get_contato_options(), value='Todos', label='Contato').props('outlined dense').classes('w-full sm:w-44')
            container_lista = ui.grid(columns=1).classes('w-full gap-5 md:grid-cols-2 xl:grid-cols-3')

        def atualizar_lista():
            container_lista.clear()
            filtrados = responsaveis_filtrados()

            with container_lista:
                for index, responsavel in filtrados:
                    nome = _texto(responsavel.get('nome'), 'Responsável')
                    aluno = _texto(nome_aluno_vinculado(alunos, responsavel), 'Aluno não informado')
                    parentesco = _texto(responsavel.get('parentesco'), 'Responsável')
                    telefone = _texto(responsavel.get('telefone'))
                    whatsapp = responsavel.get('whatsapp') or responsavel.get('telefone')
                    email = _texto(responsavel.get('email'))
                    observacoes = _texto(responsavel.get('observacoes'), 'Sem observações cadastradas')
                    numero_whatsapp = _telefone_limpo(whatsapp)

                    with ui.card().classes('app-card parent-card w-full p-5 flex flex-col'):
                        with ui.row().classes('w-full items-start justify-between gap-3 mb-4'):
                            with ui.row().classes('items-center gap-3 min-w-0'):
                                ui.avatar(nome[0].upper()).classes('brand-badge text-white font-black w-12 h-12')
                                with ui.column().classes('gap-1 min-w-0'):
                                    ui.label(nome).classes('text-lg font-black line-clamp-1')
                                    ui.label(f'{parentesco} de {aluno}').classes('app-muted text-sm line-clamp-1')
                            with ui.row().classes('gap-1 shrink-0'):
                                if pode_gerir:
                                    ui.button(icon='edit', on_click=lambda i=index, r=responsavel: abrir_modal(r, i)).props('flat color=primary round size=sm').tooltip('Editar')
                                    ui.button(icon='delete', on_click=lambda r=responsavel: confirmar_exclusao(r)).props('flat color=red round size=sm').tooltip('Excluir')

                        with ui.column().classes('w-full gap-3 flex-grow'):
                            with ui.row().classes('contact-line w-full items-center gap-2 p-3'):
                                ui.label('☎️').classes('text-lg')
                                ui.label(telefone).classes('app-muted text-sm')
                            with ui.row().classes('contact-line w-full items-center gap-2 p-3'):
                                ui.label('✉️').classes('text-lg')
                                ui.label(email).classes('app-muted text-sm line-clamp-1')
                            with ui.column().classes('contact-line w-full gap-1 p-3'):
                                ui.label('Observações').classes('text-xs font-black')
                                ui.label(observacoes).classes('app-muted text-xs leading-relaxed line-clamp-3')

                        with ui.row().classes('w-full justify-end gap-2 mt-4'):
                            if numero_whatsapp:
                                numero = numero_whatsapp if numero_whatsapp.startswith('55') else f'55{numero_whatsapp}'
                                ui.link('WhatsApp', f'https://wa.me/{numero}', new_tab=True).classes('q-btn q-btn-item non-selectable no-outline q-btn--flat q-btn--rectangle text-primary font-bold px-3 py-2')
                            if responsavel.get('email'):
                                ui.link('E-mail', f"mailto:{responsavel.get('email')}", new_tab=True).classes('q-btn q-btn-item non-selectable no-outline q-btn--flat q-btn--rectangle text-primary font-bold px-3 py-2')

                if not filtrados:
                    with ui.column().classes('app-card col-span-full items-center justify-center gap-3 py-16 text-center'):
                        ui.label('☎️').classes('text-5xl')
                        ui.label('Nenhum contato encontrado').classes('text-xl font-black')
                        ui.label('Cadastre pais e responsáveis para facilitar a comunicação.').classes('app-muted text-sm')
                        if pode_gerir:
                            ui.button('Novo contato', icon='person_add', on_click=lambda: abrir_modal()).props('unelevated color=primary')

        pesquisa_input.on_value_change(lambda _: (atualizar_resumo(), atualizar_lista()))
        aluno_filter.on_value_change(lambda _: (atualizar_resumo(), atualizar_lista()))
        parentesco_filter.on_value_change(lambda _: (atualizar_resumo(), atualizar_lista()))
        contato_filter.on_value_change(lambda _: (atualizar_resumo(), atualizar_lista()))
        atualizar_resumo()
        atualizar_lista()
