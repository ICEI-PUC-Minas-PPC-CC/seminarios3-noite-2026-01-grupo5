import uuid

from nicegui import ui

from database import load_data, save_data
from layout import frame
from permissions import has_permission, require_permission
from student_links import garantir_ids_alunos, item_vinculado_ao_aluno, normalizar


def _texto(valor, padrao='Não informado'):
    valor = str(valor or '').strip()
    return valor if valor else padrao


def _valor_filtro(valor, padrao='Todos'):
    if isinstance(valor, dict):
        return str(valor.get('label') or valor.get('value') or padrao)
    return str(valor or padrao)


def render():
    with frame('Alunos'):
        if not require_permission('view_alunos'):
            return

        alunos = load_data('alunos.json', [])
        if garantir_ids_alunos(alunos):
            save_data('alunos.json', alunos)

        editing_index = {'value': -1}
        pode_gerir = has_permission('manage_alunos')

        ui.add_css('''
            .students-page {
                color: var(--app-text);
            }

            .student-card {
                background: var(--app-surface) !important;
                color: var(--app-text) !important;
                border: 1px solid var(--app-border);
                border-radius: 8px !important;
                min-height: 330px;
                box-shadow: var(--app-shadow);
                transition: transform 160ms ease, border-color 160ms ease;
            }

            .student-card:hover {
                transform: translateY(-2px);
                border-color: var(--app-primary);
            }

            .student-card-top, .student-card-footer, .student-note {
                background: var(--app-surface-muted) !important;
            }

            .student-card-top {
                border-bottom: 4px solid transparent;
                border-image: var(--app-accent-band) 1;
            }

            .student-name, .student-strong {
                color: var(--app-text) !important;
            }

            .student-muted {
                color: var(--app-muted) !important;
            }

            .student-pill {
                background: color-mix(in srgb, var(--app-primary) 14%, transparent);
                color: var(--app-primary-strong);
                border: 1px solid color-mix(in srgb, var(--app-primary) 24%, transparent);
                border-radius: 999px;
            }

            body.body--dark .student-pill {
                background: rgba(96, 165, 250, 0.14);
                border-color: color-mix(in srgb, var(--app-primary) 30%, transparent);
            }

            .student-accent {
                color: var(--app-teal) !important;
            }

            .students-page .q-field__control {
                border-radius: 8px;
            }
        ''')

        def get_turmas():
            turmas = {a.get('turma', '').strip() for a in alunos if a.get('turma', '').strip()}
            return ['Todas'] + sorted(turmas)

        def get_acompanhamento_options():
            return ['Todos', 'Com diagnóstico', 'Com necessidades', 'Sem diagnóstico']

        def alunos_filtrados():
            termo = (pesquisa_input.value or '').strip().lower()
            turma_selecionada = _valor_filtro(turma_filter.value, 'Todas')
            acompanhamento_selecionado = _valor_filtro(acompanhamento_filter.value)
            filtrados = []

            for index, aluno in enumerate(alunos):
                texto_busca = ' '.join([
                    aluno.get('nome', ''),
                    aluno.get('turma', ''),
                    aluno.get('diagnostico', ''),
                    aluno.get('necessidades', ''),
                    aluno.get('observacoes', ''),
                ]).lower()

                if termo and termo not in texto_busca:
                    continue
                if turma_selecionada != 'Todas' and aluno.get('turma') != turma_selecionada:
                    continue

                tem_diagnostico = bool((aluno.get('diagnostico') or '').strip())
                tem_necessidades = bool((aluno.get('necessidades') or '').strip())
                if acompanhamento_selecionado == 'Com diagnóstico' and not tem_diagnostico:
                    continue
                if acompanhamento_selecionado == 'Com necessidades' and not tem_necessidades:
                    continue
                if acompanhamento_selecionado == 'Sem diagnóstico' and tem_diagnostico:
                    continue

                filtrados.append((index, aluno))

            return filtrados

        def atualizar_resumo():
            pass

        def atualizar_opcoes_turma():
            valor_atual = _valor_filtro(turma_filter.value, 'Todas')
            turma_filter.options = get_turmas()
            turma_filter.value = valor_atual
            if turma_filter.value not in turma_filter.options:
                turma_filter.value = 'Todas'
            turma_filter.update()

        def abrir_modal(aluno=None, index=-1):
            editing_index['value'] = index

            nome_input.value = aluno.get('nome', '') if aluno else ''
            turma_input.value = aluno.get('turma', '') if aluno else ''
            nascimento_input.value = aluno.get('nascimento', '') if aluno else ''
            diagnostico_input.value = aluno.get('diagnostico', '') if aluno else ''
            necessidades_input.value = aluno.get('necessidades', '') if aluno else ''
            obs_input.value = aluno.get('observacoes', '') if aluno else ''

            dialog_title.set_text('Editar aluno' if aluno else 'Novo aluno')
            dialog_subtitle.set_text('Preencha com cuidado para facilitar a rotina da equipe escolar. 💛')
            dialog.open()

        def salvar_aluno():
            if not pode_gerir:
                ui.notify('Seu cargo não permite alterar cadastros de alunos.', type='warning')
                return
            if not nome_input.value or not turma_input.value:
                ui.notify('Nome e turma são obrigatórios.', type='warning')
                return

            aluno_anterior = alunos[editing_index['value']] if editing_index['value'] >= 0 else {}

            dados = {
                'id': aluno_anterior.get('id') or uuid.uuid4().hex[:12],
                'nome': nome_input.value.strip(),
                'turma': turma_input.value.strip(),
                'nascimento': (nascimento_input.value or '').strip(),
                'diagnostico': (diagnostico_input.value or '').strip(),
                'necessidades': (necessidades_input.value or '').strip(),
                'observacoes': (obs_input.value or '').strip(),
            }

            if editing_index['value'] >= 0:
                alunos[editing_index['value']] = dados
                responsaveis = load_data('pais.json', [])
                alterou_responsaveis = False
                for responsavel in responsaveis:
                    if responsavel.get('aluno_id') == dados['id'] or (
                        not responsavel.get('aluno_id')
                        and normalizar(responsavel.get('aluno')) == normalizar(aluno_anterior.get('nome'))
                    ):
                        responsavel['aluno_id'] = dados['id']
                        responsavel['aluno'] = dados['nome']
                        alterou_responsaveis = True
                if alterou_responsaveis:
                    save_data('pais.json', responsaveis)
                ui.notify('Dados do aluno atualizados.', type='positive')
            else:
                alunos.append(dados)
                ui.notify('Aluno cadastrado com sucesso.', type='positive')

            save_data('alunos.json', alunos)
            dialog.close()
            atualizar_opcoes_turma()
            atualizar_resumo()
            atualizar_lista()

        def confirmar_exclusao(aluno):
            if not pode_gerir:
                ui.notify('Seu cargo não permite excluir alunos.', type='warning')
                return
            responsaveis = load_data('pais.json', [])
            total_responsaveis = sum(1 for responsavel in responsaveis if item_vinculado_ao_aluno(responsavel, aluno))
            with ui.dialog() as confirm_dialog, ui.card().classes('app-card w-full max-w-sm p-6'):
                with ui.column().classes('w-full items-center text-center gap-3'):
                    ui.icon('warning', color='red', size='3rem')
                    ui.label('Excluir aluno').classes('text-2xl font-bold')
                    ui.label(f'Deseja remover "{aluno["nome"]}" do acompanhamento?').classes('student-muted text-sm')
                    if total_responsaveis:
                        ui.label(f'{total_responsaveis} responsável(is) vinculado(s) também serão excluídos.').classes('text-red-600 text-xs font-black')
                    with ui.row().classes('w-full justify-center gap-3 pt-3'):
                        ui.button('Cancelar', on_click=confirm_dialog.close).props('flat color=slate')
                        ui.button('Excluir', icon='delete', on_click=lambda: apagar_aluno(aluno, confirm_dialog)).props('unelevated color=red')
            confirm_dialog.open()

        def apagar_aluno(aluno, confirm_dialog):
            alunos.remove(aluno)
            save_data('alunos.json', alunos)
            responsaveis = load_data('pais.json', [])
            restantes = [responsavel for responsavel in responsaveis if not item_vinculado_ao_aluno(responsavel, aluno)]
            removidos = len(responsaveis) - len(restantes)
            if removidos:
                save_data('pais.json', restantes)
            mensagem = f'Aluno removido. {removidos} responsável(is) vinculado(s) excluído(s).' if removidos else 'Aluno removido.'
            ui.notify(mensagem, type='warning')
            confirm_dialog.close()
            atualizar_opcoes_turma()
            atualizar_resumo()
            atualizar_lista()

        with ui.dialog() as dialog, ui.card().classes('app-card w-full max-w-4xl p-0 overflow-hidden'):
            with ui.row().classes('w-full items-center justify-between gap-4 p-6 student-card-top'):
                with ui.column().classes('gap-1'):
                    dialog_title = ui.label('Novo aluno').classes('text-2xl font-bold')
                    dialog_subtitle = ui.label('').classes('student-muted text-sm')
                ui.button(icon='close', on_click=dialog.close).props('flat round').classes('student-muted')

            with ui.scroll_area().classes('w-full max-h-[68vh]'):
                with ui.column().classes('w-full gap-5 p-6'):
                    with ui.grid(columns=2).classes('w-full gap-4'):
                        nome_input = ui.input('Nome completo *').props('outlined').classes('col-span-2')
                        turma_input = ui.input('Turma *').props('outlined').classes('w-full')
                        nascimento_input = ui.input('Nascimento').props('outlined').classes('w-full')

                    diagnostico_input = ui.input('Diagnóstico / condição').props('outlined').classes('w-full')
                    necessidades_input = ui.textarea('Necessidades específicas').props('outlined autogrow').classes('w-full')
                    obs_input = ui.textarea('Observações gerais').props('outlined autogrow').classes('w-full')

            with ui.row().classes('w-full justify-end gap-3 p-6 student-card-footer'):
                ui.button('Cancelar', on_click=dialog.close).props('flat color=slate')
                ui.button('Salvar aluno', icon='check', on_click=salvar_aluno).props('unelevated color=primary')

        with ui.column().classes('students-page w-full gap-5'):
            with ui.row().classes('app-card students-intro w-full items-center justify-between gap-5 p-5'):
                with ui.column().classes('gap-1'):
                    ui.label('☀️ Acompanhamento escolar').classes('student-muted text-sm font-black uppercase')
                    ui.label('Cada aluno com suas pistas de cuidado').classes('text-3xl font-black leading-tight')
                    ui.label('Informações importantes em cards coloridos, claros e fáceis de consultar.').classes('student-muted text-sm')
                if pode_gerir:
                    ui.button('Novo aluno ✨', icon='add', on_click=lambda: abrir_modal()).props('unelevated color=primary')

            with ui.row().classes('app-toolbar w-full items-center justify-between gap-4 p-4'):
                with ui.row().classes('flex-1 items-center gap-3 flex-wrap'):
                    pesquisa_input = ui.input(placeholder='Buscar por nome, turma, diagnóstico ou observações').props('outlined dense').classes('w-full md:max-w-md flex-1')
                    with pesquisa_input.add_slot('prepend'):
                        ui.icon('search').classes('student-muted')
                    turma_filter = ui.select(get_turmas(), value='Todas', label='Turma').props('outlined dense').classes('w-full sm:w-44')
                    acompanhamento_filter = ui.select(get_acompanhamento_options(), value='Todos', label='Acompanhamento').props('outlined dense').classes('w-full sm:w-52')
            container_lista = ui.grid(columns=1).classes('w-full gap-5 sm:grid-cols-2 xl:grid-cols-3 items-stretch')

        def atualizar_lista():
            container_lista.clear()
            filtrados = alunos_filtrados()

            with container_lista:
                for index, aluno in filtrados:
                    nome = _texto(aluno.get('nome'), 'Aluno')
                    inicial = nome[0].upper()
                    turma = _texto(aluno.get('turma'), 'Sem turma')
                    nascimento = _texto(aluno.get('nascimento'))
                    diagnostico = _texto(aluno.get('diagnostico'), 'Sem diagnóstico registrado')
                    necessidades = _texto(aluno.get('necessidades'), 'Sem necessidades específicas registradas')

                    with ui.card().classes('student-card w-full p-0 overflow-hidden flex flex-col'):
                        with ui.row().classes('student-card-top w-full items-start justify-between gap-3 p-5'):
                            with ui.row().classes('items-center gap-4 min-w-0'):
                                ui.avatar(inicial).classes('w-14 h-14 text-xl font-bold brand-badge')
                                with ui.column().classes('gap-1 min-w-0'):
                                    ui.label(nome).classes('student-name text-lg font-bold leading-tight line-clamp-1')
                                    with ui.row().classes('items-center gap-2'):
                                        ui.label('🏫').classes('text-sm')
                                        ui.label(turma).classes('student-pill text-xs font-black px-2 py-1')
                            with ui.row().classes('gap-1 shrink-0'):
                                if pode_gerir:
                                    ui.button(icon='edit', on_click=lambda i=index, a=aluno: abrir_modal(a, i)).props('flat round size=sm').classes('student-muted').tooltip('Editar')
                                    ui.button(icon='delete', on_click=lambda a=aluno: confirmar_exclusao(a)).props('flat round size=sm').classes('student-muted').tooltip('Excluir')

                        with ui.column().classes('w-full gap-4 p-5 flex-grow'):
                            with ui.row().classes('items-center gap-2'):
                                ui.label('📅').classes('text-lg')
                                ui.label(nascimento).classes('student-muted text-sm')

                            with ui.column().classes('gap-1'):
                                ui.label('💬 Diagnóstico').classes('student-muted text-[11px] font-bold uppercase')
                                ui.label(diagnostico).classes('student-strong text-sm font-semibold line-clamp-2')

                            with ui.column().classes('student-note gap-2 p-3 rounded-lg'):
                                with ui.row().classes('items-center gap-2'):
                                    ui.label('💛').classes('text-sm')
                                    ui.label('Necessidades').classes('student-strong text-xs font-bold')
                                ui.label(necessidades).classes('student-muted text-xs leading-relaxed line-clamp-3')

                        with ui.row().classes('student-card-footer w-full justify-between items-center px-5 py-4'):
                            ui.label('📁 Prontuário do aluno').classes('student-muted text-xs font-semibold')
                            ui.button('Abrir prontuário', icon='folder_open', on_click=lambda i=index: ui.navigate.to(f'/alunos/{i}/prontuario')).props('flat color=primary no-caps')

                if not filtrados:
                    with ui.column().classes('app-card col-span-full items-center justify-center gap-3 py-16 text-center'):
                        ui.icon('manage_search', size='4rem').classes('student-muted')
                        ui.label('Nenhum aluno encontrado 🌱').classes('text-xl font-bold')
                        ui.label('Ajuste os filtros ou cadastre um novo aluno.').classes('student-muted text-sm')
                        if pode_gerir:
                            ui.button('Novo aluno ✨', icon='add', on_click=lambda: abrir_modal()).props('unelevated color=primary')

        pesquisa_input.on_value_change(lambda _: (atualizar_resumo(), atualizar_lista()))
        turma_filter.on_value_change(lambda _: (atualizar_resumo(), atualizar_lista()))
        acompanhamento_filter.on_value_change(lambda _: (atualizar_resumo(), atualizar_lista()))
        atualizar_resumo()
        atualizar_lista()
