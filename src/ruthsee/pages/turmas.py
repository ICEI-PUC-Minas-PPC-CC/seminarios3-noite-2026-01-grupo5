from nicegui import ui

from database import load_data, save_data
from layout import frame
from permissions import has_permission, require_permission


def _texto(valor, padrao='Não informado'):
    valor = str(valor or '').strip()
    return valor if valor else padrao


def _normalizar(valor):
    return str(valor or '').strip().lower()


def _valor_filtro(valor, padrao='Todos'):
    if isinstance(valor, dict):
        return str(valor.get('label') or valor.get('value') or padrao)
    return str(valor or padrao)


def render():
    with frame('Turmas'):
        if not require_permission('view_turmas'):
            return

        turmas = load_data('turmas.json', [])
        alunos = load_data('alunos.json', [])
        editing_index = {'value': -1}
        nome_anterior = {'value': ''}
        pode_gerir = has_permission('manage_turmas')

        periodos = ['Manhã', 'Tarde', 'Integral', 'Noite']

        ui.add_css('''
            .class-card {
                min-height: 300px;
                transition: transform 160ms ease, border-color 160ms ease;
            }

            .class-card:hover {
                transform: translateY(-2px);
                border-color: var(--app-primary);
            }

            .class-line {
                background: var(--app-surface-muted) !important;
                border-radius: 8px;
            }

            .class-roster {
                min-height: 4.25rem;
            }
        ''')

        def alunos_da_turma(nome_turma):
            turma_normalizada = _normalizar(nome_turma)
            return [
                (index, aluno)
                for index, aluno in enumerate(alunos)
                if _normalizar(aluno.get('turma')) == turma_normalizada
            ]

        def dados_turmas():
            dados = {}
            for index, turma in enumerate(turmas):
                nome = str(turma.get('nome', '')).strip()
                if nome:
                    dados[_normalizar(nome)] = {'index': index, 'turma': turma}
            return dados

        def nomes_turmas():
            nomes = {str(turma.get('nome', '')).strip() for turma in turmas if str(turma.get('nome', '')).strip()}
            nomes.update(str(aluno.get('turma', '')).strip() for aluno in alunos if str(aluno.get('turma', '')).strip())
            return sorted(nomes, key=str.lower)

        def turmas_filtradas():
            termo = (pesquisa_input.value or '').strip().lower()
            periodo_selecionado = _valor_filtro(periodo_filter.value)
            dados = dados_turmas()
            filtradas = []

            for nome in nomes_turmas():
                info = dados.get(_normalizar(nome), {})
                turma = info.get('turma', {'nome': nome})
                alunos_turma = alunos_da_turma(nome)
                nomes_alunos = ' '.join(aluno.get('nome', '') for _, aluno in alunos_turma)
                texto_busca = ' '.join([
                    nome,
                    turma.get('professor', ''),
                    turma.get('periodo', ''),
                    turma.get('sala', ''),
                    turma.get('rotina', ''),
                    turma.get('observacoes', ''),
                    nomes_alunos,
                ]).lower()

                if termo and termo not in texto_busca:
                    continue
                if periodo_selecionado != 'Todos' and turma.get('periodo') != periodo_selecionado:
                    continue

                filtradas.append((nome, info, alunos_turma))

            return filtradas

        def abrir_modal(turma=None, index=-1, nome_predefinido=''):
            if not pode_gerir:
                ui.notify('Seu cargo não permite alterar turmas.', type='warning')
                return
            editing_index['value'] = index
            nome_atual = turma.get('nome', nome_predefinido) if turma else nome_predefinido
            nome_anterior['value'] = nome_atual

            nome_input.value = nome_atual
            periodo_atual = turma.get('periodo', periodos[0]) if turma else periodos[0]
            periodo_input.value = periodo_atual if periodo_atual in periodos else periodos[0]
            professor_input.value = turma.get('professor', '') if turma else ''
            sala_input.value = turma.get('sala', '') if turma else ''
            rotina_input.value = turma.get('rotina', '') if turma else ''
            observacoes_input.value = turma.get('observacoes', '') if turma else ''

            dialog_title.set_text('Editar turma' if index >= 0 else 'Nova turma')
            dialog.open()

        def salvar_turma():
            if not pode_gerir:
                ui.notify('Seu cargo não permite salvar turmas.', type='warning')
                return
            nome = (nome_input.value or '').strip()
            if not nome:
                ui.notify('Informe o nome da turma.', type='warning')
                return

            nome_normalizado = _normalizar(nome)
            for index, turma in enumerate(turmas):
                if index != editing_index['value'] and _normalizar(turma.get('nome')) == nome_normalizado:
                    ui.notify('Já existe uma turma cadastrada com esse nome.', type='warning')
                    return

            dados = {
                'nome': nome,
                'periodo': _valor_filtro(periodo_input.value, periodos[0]),
                'professor': (professor_input.value or '').strip(),
                'sala': (sala_input.value or '').strip(),
                'rotina': (rotina_input.value or '').strip(),
                'observacoes': (observacoes_input.value or '').strip(),
            }

            if editing_index['value'] >= 0:
                turmas[editing_index['value']] = dados
                if _normalizar(nome_anterior['value']) != nome_normalizado:
                    for aluno in alunos:
                        if _normalizar(aluno.get('turma')) == _normalizar(nome_anterior['value']):
                            aluno['turma'] = nome
                    save_data('alunos.json', alunos)
                ui.notify('Turma atualizada.', type='positive')
            else:
                turmas.append(dados)
                ui.notify('Turma cadastrada.', type='positive')

            save_data('turmas.json', turmas)
            dialog.close()
            atualizar_lista()

        def confirmar_exclusao(turma):
            if not pode_gerir:
                ui.notify('Seu cargo não permite remover turmas.', type='warning')
                return
            alunos_vinculados = len(alunos_da_turma(turma.get('nome')))
            with ui.dialog() as confirm_dialog, ui.card().classes('app-card w-full max-w-md p-6'):
                ui.label('Remover dados da turma').classes('text-xl font-black text-red-600 mb-3')
                ui.label(f'Deseja remover o cadastro de "{turma.get("nome", "turma")}"? Os alunos não serão apagados.').classes('app-muted text-sm leading-relaxed')
                if alunos_vinculados:
                    ui.label(f'{alunos_vinculados} aluno(s) continuarão com esse nome de turma no cadastro.').classes('app-muted text-xs font-bold mt-2')
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Cancelar', on_click=confirm_dialog.close).props('flat')
                    ui.button('Remover', icon='delete', on_click=lambda: apagar_turma(turma, confirm_dialog)).props('unelevated color=red')
            confirm_dialog.open()

        def apagar_turma(turma, confirm_dialog):
            turmas.remove(turma)
            save_data('turmas.json', turmas)
            ui.notify('Dados da turma removidos.', type='warning')
            confirm_dialog.close()
            atualizar_lista()

        with ui.dialog() as dialog, ui.card().classes('app-card w-full max-w-4xl p-0 overflow-hidden'):
            with ui.row().classes('w-full items-center justify-between gap-4 p-6 soft-green'):
                with ui.column().classes('gap-1'):
                    dialog_title = ui.label('Nova turma').classes('text-2xl font-black')
                    ui.label('Organize período, professor, sala e combinados da rotina.').classes('app-muted text-sm')
                ui.button(icon='close', on_click=dialog.close).props('flat round').classes('app-muted')

            with ui.scroll_area().classes('w-full max-h-[68vh]'):
                with ui.column().classes('w-full gap-4 p-6'):
                    with ui.grid(columns=2).classes('w-full gap-4'):
                        nome_input = ui.input('Nome da turma *').props('outlined').classes('w-full')
                        periodo_input = ui.select(periodos, value=periodos[0], label='Período').props('outlined').classes('w-full')
                        professor_input = ui.input('Professor(a) responsável').props('outlined').classes('w-full')
                        sala_input = ui.input('Sala / espaço').props('outlined').classes('w-full')
                    rotina_input = ui.textarea('Rotina da turma').props('outlined autogrow').classes('w-full')
                    observacoes_input = ui.textarea('Observações e combinados').props('outlined autogrow').classes('w-full')

            with ui.row().classes('w-full justify-end gap-3 p-6 soft-blue'):
                ui.button('Cancelar', on_click=dialog.close).props('flat')
                ui.button('Salvar turma', icon='check', on_click=salvar_turma).props('unelevated color=primary')

        with ui.column().classes('w-full gap-5'):
            with ui.row().classes('app-card-colorful w-full items-center justify-between gap-5 p-6'):
                with ui.column().classes('gap-2'):
                    ui.label('🏷️ Organização por turma').classes('app-muted text-sm font-black uppercase')
                    ui.label('Turmas da Ruth See').classes('text-3xl font-black leading-tight')
                    ui.label('Acompanhe professor, período, sala e alunos vinculados a cada turma.').classes('app-muted text-sm')
                if pode_gerir:
                    ui.button('Nova turma', icon='add', on_click=lambda: abrir_modal()).props('unelevated color=primary')

            with ui.row().classes('app-toolbar w-full items-center justify-between gap-4 p-4'):
                with ui.row().classes('flex-1 items-center gap-3 flex-wrap'):
                    pesquisa_input = ui.input(placeholder='Buscar por turma, professor, sala, rotina ou aluno').props('outlined dense').classes('w-full md:max-w-md flex-1')
                    with pesquisa_input.add_slot('prepend'):
                        ui.icon('search').classes('app-muted')
                    periodo_filter = ui.select(['Todos'] + periodos, value='Todos', label='Período').props('outlined dense').classes('w-full sm:w-44')

            container_lista = ui.grid(columns=1).classes('w-full gap-5 md:grid-cols-2 xl:grid-cols-3 items-stretch')

        def atualizar_lista():
            container_lista.clear()
            filtradas = turmas_filtradas()

            with container_lista:
                for nome, info, alunos_turma in filtradas:
                    turma = info.get('turma', {'nome': nome})
                    index = info.get('index', -1)
                    tem_cadastro = index >= 0
                    professor = _texto(turma.get('professor'), 'Professor não informado')
                    periodo = _texto(turma.get('periodo'), 'Período não informado')
                    sala = _texto(turma.get('sala'), 'Sala não informada')
                    rotina = _texto(turma.get('rotina'), 'Rotina ainda não descrita.')
                    observacoes = _texto(turma.get('observacoes'), 'Sem observações cadastradas.')

                    with ui.card().classes('app-card class-card w-full p-5 flex flex-col'):
                        with ui.row().classes('w-full items-start justify-between gap-3 mb-4'):
                            with ui.column().classes('gap-1 min-w-0'):
                                ui.label(nome).classes('text-2xl font-black leading-tight line-clamp-1')
                                with ui.row().classes('items-center gap-2 flex-wrap'):
                                    ui.label(f'🕒 {periodo}').classes('app-pill text-xs font-black px-3 py-1')
                                    ui.label(f'☀️ {len(alunos_turma)} aluno(s)').classes('app-pill text-xs font-black px-3 py-1')
                            with ui.row().classes('gap-1 shrink-0'):
                                if pode_gerir:
                                    ui.button(icon='edit', on_click=lambda t=turma, i=index, n=nome: abrir_modal(t, i, n)).props('flat color=primary round size=sm').tooltip('Editar turma')
                                    if tem_cadastro:
                                        ui.button(icon='delete', on_click=lambda t=turma: confirmar_exclusao(t)).props('flat color=red round size=sm').tooltip('Remover dados da turma')

                        with ui.column().classes('w-full gap-3 flex-grow'):
                            with ui.column().classes('class-line gap-1 p-3'):
                                ui.label('Professor(a)').classes('app-muted text-xs font-black uppercase')
                                ui.label(professor).classes('font-bold')
                            with ui.column().classes('class-line gap-1 p-3'):
                                ui.label('Sala / espaço').classes('app-muted text-xs font-black uppercase')
                                ui.label(sala).classes('font-bold')
                            with ui.column().classes('class-line gap-1 p-3'):
                                ui.label('Rotina').classes('app-muted text-xs font-black uppercase')
                                ui.label(rotina).classes('app-muted text-sm leading-relaxed line-clamp-2')
                            with ui.column().classes('class-line class-roster gap-2 p-3'):
                                ui.label('Alunos vinculados').classes('app-muted text-xs font-black uppercase')
                                if not alunos_turma:
                                    ui.label('Nenhum aluno vinculado ainda.').classes('app-muted text-sm')
                                else:
                                    with ui.row().classes('gap-2 flex-wrap'):
                                        for aluno_index, aluno in alunos_turma[:6]:
                                            ui.button(
                                                _texto(aluno.get('nome'), 'Aluno'),
                                                on_click=lambda i=aluno_index: ui.navigate.to(f'/alunos/{i}/prontuario'),
                                            ).props('flat dense no-caps color=primary').classes('app-pill text-xs font-black px-2 py-1')
                                        if len(alunos_turma) > 6:
                                            ui.label(f'+{len(alunos_turma) - 6}').classes('app-muted text-xs font-black px-2 py-1')

                        with ui.row().classes('w-full justify-between items-center gap-3 pt-4'):
                            ui.label(observacoes).classes('app-muted text-xs leading-relaxed line-clamp-2')
                            ui.button('Ver alunos', icon='groups', on_click=lambda: ui.navigate.to('/alunos')).props('flat color=primary no-caps')

                if not filtradas:
                    with ui.column().classes('app-card col-span-full items-center justify-center gap-3 py-16 text-center'):
                        ui.label('🏷️').classes('text-5xl')
                        ui.label('Nenhuma turma encontrada').classes('text-xl font-black')
                        ui.label('Cadastre uma turma ou ajuste os filtros de busca.').classes('app-muted text-sm')
                        if pode_gerir:
                            ui.button('Nova turma', icon='add', on_click=lambda: abrir_modal()).props('unelevated color=primary')

        pesquisa_input.on_value_change(lambda _: atualizar_lista())
        periodo_filter.on_value_change(lambda _: atualizar_lista())
        atualizar_lista()
