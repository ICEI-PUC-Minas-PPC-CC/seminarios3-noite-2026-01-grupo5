import datetime

from nicegui import app, ui

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


def _hoje():
    return datetime.datetime.now().strftime('%d/%m/%Y')


def _status_class(status):
    mapa = {
        'Planejado': 'soft-blue',
        'Em andamento': 'soft-amber',
        'Concluído': 'soft-green',
        'Atenção': 'soft-coral',
        'Reprogramado': 'soft-violet',
    }
    return mapa.get(status, 'soft-teal')


def _campo_data(label, value='', dense=False):
    props = 'outlined mask=##/##/####'
    if dense:
        props += ' dense'

    campo = ui.input(label, value=value).props(props).classes('w-full')
    with campo.add_slot('append'):
        calendario_icon = ui.icon('event').classes('app-muted cursor-pointer')
        with ui.menu().props('no-parent-event') as menu_calendario:
            ui.date(mask='DD/MM/YYYY').bind_value(campo)
            with ui.row().classes('w-full justify-end p-2'):
                ui.button('Fechar', on_click=menu_calendario.close).props('flat dense no-caps')
        calendario_icon.on('click', menu_calendario.open)
    return campo


def render():
    with frame('Agenda / Rotina do Dia'):
        if not require_permission('view_agenda'):
            return

        agenda = load_data('agenda.json', [])
        alunos = load_data('alunos.json', [])
        turmas = load_data('turmas.json', [])
        editing_index = {'value': -1}
        pode_gerir = has_permission('manage_agenda')

        tipos = [
            'Entrada',
            'Atividade pedagógica',
            'Lanche',
            'Pausa sensorial',
            'Recreação',
            'Atendimento / apoio',
            'Comunicação com família',
            'Reunião',
            'Saída',
        ]
        status_opcoes = ['Planejado', 'Em andamento', 'Concluído', 'Atenção', 'Reprogramado']

        ui.add_css('''
            .agenda-day {
                background: var(--app-happy) !important;
            }

            .agenda-activity {
                transition: border-color 160ms ease, transform 160ms ease;
            }

            .agenda-activity:hover {
                border-color: var(--app-primary);
                transform: translateY(-1px);
            }

            .agenda-time {
                width: 5.25rem;
                color: var(--app-primary-strong) !important;
                font-size: 1rem;
                font-weight: 900;
                line-height: 1;
                text-align: right;
            }

            .agenda-rail {
                width: 1.25rem;
                align-items: center;
                align-self: stretch;
            }

            .agenda-dot {
                width: 0.95rem;
                height: 0.95rem;
                border-radius: 999px;
                background: var(--app-primary);
                border: 3px solid var(--app-surface);
                box-shadow: 0 0 0 1px var(--app-border);
                flex: 0 0 auto;
            }

            .agenda-entry:not(:last-child) .agenda-rail::after {
                content: '';
                width: 2px;
                flex: 1;
                margin-top: 0.35rem;
                background: var(--app-border);
            }

            .agenda-note {
                background: var(--app-surface-muted) !important;
                border: 1px solid var(--app-border);
                border-radius: 8px;
            }

            .agenda-status {
                border: 1px solid var(--app-border);
                border-radius: 999px;
                font-size: 0.72rem;
                font-weight: 900;
                padding: 0.34rem 0.62rem;
            }

            .agenda-date-picker .q-field__append {
                padding-right: 0.25rem;
            }

            @media (max-width: 640px) {
                .agenda-time {
                    width: 4rem;
                    font-size: 0.82rem;
                }
            }
        ''')

        def nomes_alunos():
            return sorted({aluno.get('nome', '').strip() for aluno in alunos if aluno.get('nome', '').strip()})

        def nomes_turmas():
            nomes = {turma.get('nome', '').strip() for turma in turmas if turma.get('nome', '').strip()}
            nomes.update(aluno.get('turma', '').strip() for aluno in alunos if aluno.get('turma', '').strip())
            return sorted(nomes, key=str.lower)

        def opcoes_alunos():
            return ['Geral'] + nomes_alunos()

        def opcoes_turmas():
            return ['Geral'] + nomes_turmas()

        def agenda_filtrada():
            termo = (pesquisa_input.value or '').strip().lower()
            data = (data_filter.value or '').strip()
            turma = _valor_filtro(turma_filter.value)
            aluno = _valor_filtro(aluno_filter.value)
            status = _valor_filtro(status_filter.value)
            filtrados = []

            for index, item in enumerate(agenda):
                texto_busca = ' '.join([
                    item.get('titulo', ''),
                    item.get('tipo', ''),
                    item.get('turma', ''),
                    item.get('aluno', ''),
                    item.get('responsavel', ''),
                    item.get('status', ''),
                    item.get('observacoes', ''),
                    item.get('apoio_visual', ''),
                ]).lower()

                if data and item.get('data') != data:
                    continue
                if termo and termo not in texto_busca:
                    continue
                if turma != 'Todos' and item.get('turma') != turma:
                    continue
                if aluno != 'Todos' and item.get('aluno') != aluno:
                    continue
                if status != 'Todos' and item.get('status') != status:
                    continue

                filtrados.append((index, item))

            return sorted(filtrados, key=lambda registro: (registro[1].get('hora_inicio', ''), registro[1].get('hora_fim', '')))

        def atualizar_opcoes():
            filtros = [
                (turma_input, opcoes_turmas(), 'Geral'),
                (aluno_input, opcoes_alunos(), 'Geral'),
                (turma_filter, ['Todos'] + nomes_turmas(), 'Todos'),
                (aluno_filter, ['Todos'] + nomes_alunos(), 'Todos'),
            ]
            for filtro, opcoes, padrao in filtros:
                valor_atual = _valor_filtro(filtro.value, padrao)
                filtro.options = opcoes
                filtro.value = valor_atual if valor_atual in opcoes else padrao
                filtro.update()

        def abrir_modal(item=None, index=-1):
            if not pode_gerir:
                ui.notify('Seu cargo não permite alterar a agenda.', type='warning')
                return
            editing_index['value'] = index
            data_input.value = item.get('data', data_filter.value or _hoje()) if item else (data_filter.value or _hoje())
            inicio_input.value = item.get('hora_inicio', '') if item else ''
            fim_input.value = item.get('hora_fim', '') if item else ''
            titulo_input.value = item.get('titulo', '') if item else ''
            tipo_input.value = item.get('tipo', tipos[0]) if item else tipos[0]
            turma_input.value = item.get('turma', 'Geral') if item else 'Geral'
            aluno_input.value = item.get('aluno', 'Geral') if item else 'Geral'
            responsavel_input.value = item.get('responsavel', '') if item else ''
            status_input.value = item.get('status', 'Planejado') if item else 'Planejado'
            apoio_visual_input.value = item.get('apoio_visual', '') if item else ''
            observacoes_input.value = item.get('observacoes', '') if item else ''
            dialog_title.set_text('Editar atividade' if item else 'Nova atividade')
            dialog.open()

        def salvar_item():
            if not pode_gerir:
                ui.notify('Seu cargo não permite salvar atividades na agenda.', type='warning')
                return
            if not titulo_input.value or not data_input.value or not inicio_input.value:
                ui.notify('Informe data, horário inicial e título da atividade.', type='warning')
                return

            dados = {
                'data': (data_input.value or '').strip(),
                'hora_inicio': (inicio_input.value or '').strip(),
                'hora_fim': (fim_input.value or '').strip(),
                'titulo': (titulo_input.value or '').strip(),
                'tipo': _valor_filtro(tipo_input.value, tipos[0]),
                'turma': _valor_filtro(turma_input.value, 'Geral'),
                'aluno': _valor_filtro(aluno_input.value, 'Geral'),
                'responsavel': (responsavel_input.value or '').strip(),
                'status': _valor_filtro(status_input.value, 'Planejado'),
                'apoio_visual': (apoio_visual_input.value or '').strip(),
                'observacoes': (observacoes_input.value or '').strip(),
                'autor': app.storage.user.get('nome', 'Equipe'),
            }

            if editing_index['value'] >= 0:
                agenda[editing_index['value']] = dados
                ui.notify('Atividade atualizada.', type='positive')
            else:
                agenda.append(dados)
                ui.notify('Atividade adicionada à rotina.', type='positive')

            save_data('agenda.json', agenda)
            data_filter.value = dados['data']
            dialog.close()
            atualizar_lista()

        def confirmar_exclusao(item):
            if not pode_gerir:
                ui.notify('Seu cargo não permite excluir atividades da agenda.', type='warning')
                return
            with ui.dialog() as confirm_dialog, ui.card().classes('app-card w-full max-w-md p-6'):
                ui.label('Remover atividade').classes('text-xl font-black text-red-600 mb-3')
                ui.label(f'Deseja remover "{item.get("titulo", "atividade")}" da rotina?').classes('app-muted text-sm')
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Cancelar', on_click=confirm_dialog.close).props('flat')
                    ui.button('Remover', icon='delete', on_click=lambda: apagar_item(item, confirm_dialog)).props('unelevated color=red')
            confirm_dialog.open()

        def apagar_item(item, confirm_dialog):
            agenda.remove(item)
            save_data('agenda.json', agenda)
            ui.notify('Atividade removida.', type='warning')
            confirm_dialog.close()
            atualizar_lista()

        def mudar_dia(delta):
            try:
                data = datetime.datetime.strptime(data_filter.value, '%d/%m/%Y')
            except (TypeError, ValueError):
                data = datetime.datetime.now()
            data_filter.value = (data + datetime.timedelta(days=delta)).strftime('%d/%m/%Y')
            atualizar_lista()

        def ir_para_hoje():
            data_filter.value = _hoje()
            atualizar_lista()

        with ui.dialog() as dialog, ui.card().classes('app-card w-full max-w-5xl p-0 overflow-hidden'):
            with ui.row().classes('w-full items-center justify-between gap-4 p-6 soft-blue'):
                with ui.column().classes('gap-1'):
                    dialog_title = ui.label('Nova atividade').classes('text-2xl font-black')
                    ui.label('Monte uma rotina previsível, clara e fácil de acompanhar pela equipe.').classes('app-muted text-sm')
                ui.button(icon='close', on_click=dialog.close).props('flat round').classes('app-muted')

            with ui.scroll_area().classes('w-full max-h-[70vh]'):
                with ui.column().classes('w-full gap-4 p-6'):
                    with ui.grid(columns=2).classes('w-full gap-4'):
                        data_input = _campo_data('Data *').classes('agenda-date-picker')
                        tipo_input = ui.select(tipos, value=tipos[0], label='Tipo').props('outlined').classes('w-full')
                        inicio_input = ui.input('Início *').props('outlined mask=##:##').classes('w-full')
                        fim_input = ui.input('Fim').props('outlined mask=##:##').classes('w-full')
                    titulo_input = ui.input('Título da atividade *').props('outlined').classes('w-full')
                    with ui.grid(columns=2).classes('w-full gap-4'):
                        turma_input = ui.select(opcoes_turmas(), value='Geral', label='Turma').props('outlined').classes('w-full')
                        aluno_input = ui.select(opcoes_alunos(), value='Geral', label='Aluno').props('outlined').classes('w-full')
                        responsavel_input = ui.input('Responsável / profissional').props('outlined').classes('w-full')
                        status_input = ui.select(status_opcoes, value='Planejado', label='Status').props('outlined').classes('w-full')
                    apoio_visual_input = ui.input('Apoio visual / material de previsibilidade').props('outlined').classes('w-full')
                    observacoes_input = ui.textarea('Observações e combinados').props('outlined autogrow').classes('w-full')

            with ui.row().classes('w-full justify-end gap-3 p-6 soft-teal'):
                ui.button('Cancelar', on_click=dialog.close).props('flat')
                ui.button('Salvar atividade', icon='check', on_click=salvar_item).props('unelevated color=primary')

        with ui.column().classes('w-full gap-5'):
            with ui.row().classes('app-card-colorful agenda-day w-full items-center justify-between gap-5 p-6'):
                with ui.column().classes('gap-2'):
                    ui.label('🗓️ Rotina visual da escola').classes('app-muted text-sm font-black uppercase')
                    ui.label('Agenda / Rotina do dia').classes('text-3xl font-black leading-tight')
                    ui.label('Organize horários, transições, apoios visuais e responsáveis para uma rotina previsível.').classes('app-muted text-sm')
                if pode_gerir:
                    ui.button('Nova atividade', icon='add', on_click=lambda: abrir_modal()).props('unelevated color=primary')

            with ui.row().classes('app-toolbar w-full items-center justify-between gap-4 p-4'):
                with ui.row().classes('flex-1 items-center gap-3 flex-wrap'):
                    ui.button(icon='chevron_left', on_click=lambda: mudar_dia(-1)).props('flat round').tooltip('Dia anterior')
                    data_filter = _campo_data('Data', value=_hoje(), dense=True).classes('agenda-date-picker w-full sm:w-40')
                    ui.button(icon='today', on_click=ir_para_hoje).props('flat round').tooltip('Hoje')
                    ui.button(icon='chevron_right', on_click=lambda: mudar_dia(1)).props('flat round').tooltip('Próximo dia')
                    pesquisa_input = ui.input(placeholder='Buscar por atividade, aluno, turma, responsável ou apoio').props('outlined dense').classes('w-full md:max-w-md flex-1')
                    with pesquisa_input.add_slot('prepend'):
                        ui.icon('search').classes('app-muted')
                    turma_filter = ui.select(['Todos'] + nomes_turmas(), value='Todos', label='Turma').props('outlined dense').classes('w-full sm:w-44')
                    aluno_filter = ui.select(['Todos'] + nomes_alunos(), value='Todos', label='Aluno').props('outlined dense').classes('w-full sm:w-52')
                    status_filter = ui.select(['Todos'] + status_opcoes, value='Todos', label='Status').props('outlined dense').classes('w-full sm:w-44')

            container_lista = ui.column().classes('w-full gap-5')

        def atualizar_lista():
            container_lista.clear()
            filtrados = agenda_filtrada()

            with container_lista:
                with ui.row().classes('w-full items-center justify-between gap-4'):
                    with ui.column().classes('gap-0'):
                        ui.label(f'Rotina de {data_filter.value or _hoje()}').classes('text-xl font-black')
                        ui.label(f'{len(filtrados)} atividade(s) encontrada(s)').classes('app-muted text-sm')
                    if pode_gerir:
                        ui.button('Adicionar atividade', icon='add', on_click=lambda: abrir_modal()).props('flat color=primary no-caps')

                if not filtrados:
                    with ui.column().classes('app-card w-full items-center justify-center gap-3 py-16 text-center'):
                        ui.label('🗓️').classes('text-5xl')
                        ui.label('Nenhuma atividade nesta rotina').classes('text-xl font-black')
                        ui.label('Cadastre horários para criar uma rotina visual clara para a equipe.').classes('app-muted text-sm')
                        if pode_gerir:
                            ui.button('Nova atividade', icon='add', on_click=lambda: abrir_modal()).props('unelevated color=primary')
                    return

                with ui.card().classes('app-card w-full p-5'):
                    with ui.column().classes('w-full gap-0'):
                        for index, item in filtrados:
                            hora = _texto(item.get('hora_inicio'), '--:--')
                            fim = item.get('hora_fim', '').strip()
                            status = _texto(item.get('status'), 'Planejado')
                            status_class = _status_class(status)

                            with ui.row().classes('agenda-entry w-full items-stretch gap-3'):
                                ui.label(f'{hora}{f" - {fim}" if fim else ""}').classes('agenda-time pt-4 shrink-0')
                                with ui.column().classes('agenda-rail pt-4'):
                                    ui.element('span').classes('agenda-dot')

                                with ui.card().classes('app-card agenda-activity flex-1 p-4 mb-4 min-w-0'):
                                    with ui.row().classes('w-full items-start justify-between gap-3'):
                                        with ui.column().classes('gap-1 min-w-0'):
                                            with ui.row().classes('items-center gap-2 flex-wrap'):
                                                ui.label(item.get('tipo', 'Atividade')).classes('app-pill text-xs font-black px-3 py-1')
                                                ui.label(status).classes(f'agenda-status {status_class}')
                                            ui.label(_texto(item.get('titulo'), 'Atividade')).classes('text-xl font-black leading-tight')
                                            ui.label(f"{_texto(item.get('turma'), 'Geral')} · {_texto(item.get('aluno'), 'Geral')}").classes('app-muted text-xs font-bold')
                                        if pode_gerir:
                                            with ui.row().classes('gap-1 shrink-0'):
                                                ui.button(icon='edit', on_click=lambda i=index, a=item: abrir_modal(a, i)).props('flat color=primary round size=sm').tooltip('Editar')
                                                ui.button(icon='delete', on_click=lambda a=item: confirmar_exclusao(a)).props('flat color=red round size=sm').tooltip('Remover')

                                    with ui.grid(columns=1).classes('w-full gap-3 md:grid-cols-2 mt-3'):
                                        with ui.column().classes('agenda-note gap-1 p-3'):
                                            ui.label('Responsável').classes('app-muted text-xs font-black uppercase')
                                            ui.label(_texto(item.get('responsavel'), 'Equipe')).classes('font-bold')
                                        with ui.column().classes('agenda-note gap-1 p-3'):
                                            ui.label('Apoio visual').classes('app-muted text-xs font-black uppercase')
                                            ui.label(_texto(item.get('apoio_visual'), 'Não informado')).classes('font-bold')

                                    if item.get('observacoes'):
                                        with ui.column().classes('agenda-note w-full gap-1 p-3 mt-3'):
                                            ui.label('Observações').classes('app-muted text-xs font-black uppercase')
                                            ui.label(item.get('observacoes')).classes('app-muted text-sm leading-relaxed')

        data_filter.on_value_change(lambda _: atualizar_lista())
        pesquisa_input.on_value_change(lambda _: atualizar_lista())
        turma_filter.on_value_change(lambda _: atualizar_lista())
        aluno_filter.on_value_change(lambda _: atualizar_lista())
        status_filter.on_value_change(lambda _: atualizar_lista())
        atualizar_opcoes()
        atualizar_lista()
