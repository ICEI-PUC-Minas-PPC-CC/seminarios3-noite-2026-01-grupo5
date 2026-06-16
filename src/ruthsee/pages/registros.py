import datetime

from nicegui import app, ui

from database import load_data, save_data
from layout import frame
from permissions import has_permission, require_permission


def _texto(valor, padrao='Não informado'):
    valor = str(valor or '').strip()
    return valor if valor else padrao


def _valor_filtro(valor, padrao='Todos'):
    if isinstance(valor, dict):
        return str(valor.get('label') or valor.get('value') or padrao)
    return str(valor or padrao)


def _normalizar(valor):
    return str(valor or '').strip().lower()


def _classe_intensidade(valor):
    texto = _normalizar(valor)
    if 'intenso' in texto or 'crise' in texto:
        return 'timeline-danger'
    if 'moderado' in texto:
        return 'timeline-amber'
    if 'positivo' in texto:
        return 'timeline-green'
    if 'leve' in texto:
        return 'timeline-blue'
    return 'timeline-teal'


def render():
    with frame('Registros de Acompanhamento'):
        if not require_permission('view_registros'):
            return

        registros = load_data('registros.json', [])
        alunos = load_data('alunos.json', [])
        editing_index = {'value': -1}
        pode_gerir = has_permission('manage_registros')

        tipos = [
            'Observação',
            'Estratégia aplicada',
            'Evolução positiva',
            'Crise/Sobrecarga',
            'Comunicação com família',
            'Reunião/Alinhamento',
        ]
        intensidades = ['Leve', 'Moderado', 'Intenso', 'Positivo', 'Neutro']

        ui.add_css('''
            .timeline-shell {
                overflow: hidden;
            }

            .student-record-card {
                overflow: hidden;
                transition: border-color 160ms ease, transform 160ms ease;
            }

            .student-record-card:hover {
                border-color: var(--app-primary);
                transform: translateY(-1px);
            }

            .student-record-head {
                background: var(--app-surface-muted) !important;
                border-bottom: 1px solid var(--app-border);
            }

            .student-record-count {
                background: var(--app-surface) !important;
                border: 1px solid var(--app-border);
                border-radius: 999px;
                font-size: 0.72rem;
                font-weight: 900;
                padding: 0.34rem 0.62rem;
            }

            .timeline-entry {
                position: relative;
            }

            .timeline-date {
                width: 6.25rem;
                color: var(--app-muted) !important;
                font-size: 0.74rem;
                font-weight: 900;
                line-height: 1.15;
                text-align: right;
                text-transform: uppercase;
            }

            .timeline-rail {
                width: 1.25rem;
                align-items: center;
                align-self: stretch;
            }

            .timeline-dot {
                width: 0.95rem;
                height: 0.95rem;
                border-radius: 999px;
                border: 3px solid var(--app-surface);
                box-shadow: 0 0 0 1px var(--app-border);
                flex: 0 0 auto;
            }

            .timeline-entry:not(:last-child) .timeline-rail::after {
                content: '';
                width: 2px;
                flex: 1;
                margin-top: 0.35rem;
                background: var(--app-border);
            }

            .timeline-content {
                background: var(--app-surface-muted) !important;
                border: 1px solid var(--app-border);
                border-radius: 8px;
            }

            .timeline-content:hover {
                border-color: var(--app-primary);
            }

            .timeline-danger { background: var(--app-danger); }
            .timeline-amber { background: var(--app-amber); }
            .timeline-green { background: var(--app-green); }
            .timeline-blue { background: var(--app-primary); }
            .timeline-teal { background: var(--app-teal); }

            @media (max-width: 640px) {
                .timeline-date {
                    width: 4.6rem;
                    font-size: 0.68rem;
                }
            }
        ''')

        def get_alunos_options(extra_aluno=''):
            nomes = {aluno.get('nome', '').strip() for aluno in alunos if aluno.get('nome', '').strip()}
            if extra_aluno:
                nomes.add(extra_aluno.strip())
            return sorted(nomes)

        def get_alunos_filter_options():
            return ['Todos'] + get_alunos_options()

        def indice_aluno(nome):
            for index, aluno in enumerate(alunos):
                if aluno.get('nome') == nome:
                    return index
            return None

        def atualizar_opcoes_filtros():
            valor_atual = _valor_filtro(aluno_filter.value)
            opcoes = get_alunos_filter_options()
            aluno_filter.options = opcoes
            aluno_filter.value = valor_atual if valor_atual in opcoes else 'Todos'
            aluno_filter.update()

        def registros_filtrados():
            termo = (pesquisa_input.value or '').strip().lower()
            aluno_selecionado = _valor_filtro(aluno_filter.value)
            tipo_selecionado = _valor_filtro(tipo_filter.value)
            intensidade_selecionada = _valor_filtro(intensidade_filter.value)
            filtrados = []

            for index, registro in enumerate(registros):
                texto_busca = ' '.join([
                    registro.get('aluno', ''),
                    registro.get('tipo', ''),
                    registro.get('intensidade', ''),
                    registro.get('descricao', ''),
                    registro.get('acao', ''),
                    registro.get('proximo_passo', ''),
                    registro.get('autor', ''),
                    registro.get('data', ''),
                ]).lower()

                if termo and termo not in texto_busca:
                    continue
                if aluno_selecionado != 'Todos' and registro.get('aluno') != aluno_selecionado:
                    continue
                if tipo_selecionado != 'Todos' and registro.get('tipo') != tipo_selecionado:
                    continue
                if intensidade_selecionada != 'Todos' and registro.get('intensidade') != intensidade_selecionada:
                    continue

                filtrados.append((index, registro))

            return filtrados

        def abrir_modal(registro=None, index=-1):
            if not pode_gerir:
                ui.notify('Seu cargo não permite alterar registros.', type='warning')
                return
            editing_index['value'] = index
            aluno_atual = registro.get('aluno', '') if registro else ''

            aluno_input.options = get_alunos_options(aluno_atual)
            aluno_input.value = aluno_atual or (aluno_input.options[0] if aluno_input.options else None)
            aluno_input.update()
            data_input.value = registro.get('data', '') if registro else datetime.datetime.now().strftime('%d/%m/%Y')
            tipo_input.value = registro.get('tipo', tipos[0]) if registro else tipos[0]
            intensidade_input.value = registro.get('intensidade', 'Neutro') if registro else 'Neutro'
            descricao_input.value = registro.get('descricao', '') if registro else ''
            acao_input.value = registro.get('acao', '') if registro else ''
            proximo_passo_input.value = registro.get('proximo_passo', '') if registro else ''

            dialog_title.set_text('Editar registro' if registro else 'Novo registro')
            dialog.open()

        def salvar_registro():
            if not pode_gerir:
                ui.notify('Seu cargo não permite salvar registros.', type='warning')
                return
            aluno_selecionado = _valor_filtro(aluno_input.value, '')
            tipo_selecionado = _valor_filtro(tipo_input.value, tipos[0])
            intensidade_selecionada = _valor_filtro(intensidade_input.value, 'Neutro')

            if not aluno_selecionado or not descricao_input.value:
                ui.notify('Aluno e descrição são obrigatórios.', type='warning')
                return

            dados = {
                'aluno': aluno_selecionado,
                'data': (data_input.value or '').strip() or datetime.datetime.now().strftime('%d/%m/%Y'),
                'tipo': tipo_selecionado,
                'intensidade': intensidade_selecionada,
                'descricao': (descricao_input.value or '').strip(),
                'acao': (acao_input.value or '').strip(),
                'proximo_passo': (proximo_passo_input.value or '').strip(),
                'autor': app.storage.user.get('nome', 'Equipe'),
            }

            if editing_index['value'] >= 0:
                registros[editing_index['value']] = dados
                ui.notify('Registro atualizado.', type='positive')
            else:
                registros.append(dados)
                ui.notify('Registro salvo no acompanhamento.', type='positive')

            save_data('registros.json', registros)
            dialog.close()
            atualizar_opcoes_filtros()
            atualizar_lista()

        def confirmar_exclusao(registro):
            if not pode_gerir:
                ui.notify('Seu cargo não permite excluir registros.', type='warning')
                return
            with ui.dialog() as confirm_dialog, ui.card().classes('app-card w-full max-w-md p-6'):
                ui.label('Excluir registro').classes('text-xl font-black text-red-600 mb-3')
                ui.label(f'Deseja apagar o registro de "{registro.get("aluno", "aluno")}"?').classes('app-muted text-sm')
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Cancelar', on_click=confirm_dialog.close).props('flat')
                    ui.button('Excluir', icon='delete', on_click=lambda: apagar_registro(registro, confirm_dialog)).props('unelevated color=red')
            confirm_dialog.open()

        def apagar_registro(registro, confirm_dialog):
            registros.remove(registro)
            save_data('registros.json', registros)
            ui.notify('Registro removido.', type='warning')
            confirm_dialog.close()
            atualizar_lista()

        with ui.dialog() as dialog, ui.card().classes('app-card w-full max-w-4xl p-0 overflow-hidden'):
            with ui.row().classes('w-full items-center justify-between gap-4 p-6 soft-amber'):
                with ui.column().classes('gap-1'):
                    dialog_title = ui.label('Novo registro').classes('text-2xl font-black')
                    ui.label('Registre fatos importantes da rotina com clareza e cuidado.').classes('app-muted text-sm')
                ui.button(icon='close', on_click=dialog.close).props('flat round').classes('app-muted')

            with ui.scroll_area().classes('w-full max-h-[68vh]'):
                with ui.column().classes('w-full gap-4 p-6'):
                    with ui.grid(columns=2).classes('w-full gap-4'):
                        aluno_input = ui.select(get_alunos_options(), label='Aluno *').props('outlined').classes('w-full')
                        data_input = ui.input('Data').props('outlined').classes('w-full')
                        tipo_input = ui.select(tipos, value=tipos[0], label='Tipo').props('outlined').classes('w-full')
                        intensidade_input = ui.select(intensidades, value='Neutro', label='Intensidade').props('outlined').classes('w-full')
                    descricao_input = ui.textarea('Descrição do ocorrido / evolução *').props('outlined autogrow').classes('w-full')
                    acao_input = ui.textarea('Ação tomada pela equipe').props('outlined autogrow').classes('w-full')
                    proximo_passo_input = ui.textarea('Próximo passo / combinado').props('outlined autogrow').classes('w-full')

            with ui.row().classes('w-full justify-end gap-3 p-6 soft-blue'):
                ui.button('Cancelar', on_click=dialog.close).props('flat')
                ui.button('Salvar registro', icon='check', on_click=salvar_registro).props('unelevated color=primary')

        with ui.column().classes('w-full gap-5'):
            with ui.row().classes('app-card-colorful w-full items-center justify-between gap-5 p-6'):
                with ui.column().classes('gap-2'):
                    ui.label('📝 Diário de acompanhamento').classes('app-muted text-sm font-black uppercase')
                    ui.label('Registros importantes da rotina').classes('text-3xl font-black leading-tight')
                    ui.label('Acompanhe evolução, sinais de sobrecarga, estratégias aplicadas e combinados com a família.').classes('app-muted text-sm')
                if pode_gerir:
                    ui.button('Novo registro', icon='note_add', on_click=lambda: abrir_modal()).props('unelevated color=primary')

            with ui.row().classes('app-toolbar w-full items-center justify-between gap-4 p-4'):
                with ui.row().classes('flex-1 items-center gap-3 flex-wrap'):
                    pesquisa_input = ui.input(placeholder='Buscar por aluno, descrição, ação ou autor').props('outlined dense').classes('w-full md:max-w-md flex-1')
                    with pesquisa_input.add_slot('prepend'):
                        ui.icon('search').classes('app-muted')
                    aluno_filter = ui.select(get_alunos_filter_options(), value='Todos', label='Aluno').props('outlined dense').classes('w-full sm:w-52')
                    tipo_filter = ui.select(['Todos'] + tipos, value='Todos', label='Tipo').props('outlined dense').classes('w-full sm:w-52')
                    intensidade_filter = ui.select(['Todos'] + intensidades, value='Todos', label='Intensidade').props('outlined dense').classes('w-full sm:w-44')
            container_lista = ui.column().classes('w-full gap-5')

        def atualizar_lista():
            container_lista.clear()
            filtrados = registros_filtrados()

            with container_lista:
                if not alunos:
                    with ui.column().classes('app-card col-span-full items-center justify-center gap-3 py-16 text-center'):
                        ui.label('☀️').classes('text-5xl')
                        ui.label('Cadastre um aluno primeiro').classes('text-xl font-black')
                        ui.label('Os registros precisam estar vinculados a um aluno.').classes('app-muted text-sm')
                        ui.button('Abrir alunos', icon='groups', on_click=lambda: ui.navigate.to('/alunos')).props('unelevated color=primary')
                    return

                if not filtrados:
                    with ui.column().classes('app-card col-span-full items-center justify-center gap-3 py-16 text-center'):
                        ui.label('📝').classes('text-5xl')
                        ui.label('Nenhum registro encontrado').classes('text-xl font-black')
                        ui.label('Ajuste os filtros ou crie um novo acompanhamento.').classes('app-muted text-sm')
                        if pode_gerir:
                            ui.button('Novo registro', icon='note_add', on_click=lambda: abrir_modal()).props('unelevated color=primary')
                    return

                grupos = {}
                for index, registro in reversed(filtrados):
                    aluno_nome = _texto(registro.get('aluno'), 'Aluno')
                    chave = _normalizar(aluno_nome)
                    if chave not in grupos:
                        grupos[chave] = {
                            'nome': aluno_nome,
                            'aluno_index': indice_aluno(aluno_nome),
                            'registros': [],
                        }
                    grupos[chave]['registros'].append((index, registro))

                with ui.column().classes('w-full gap-5'):
                    for grupo in grupos.values():
                        nome_aluno = grupo['nome']
                        registros_aluno = grupo['registros']
                        aluno_index = grupo['aluno_index']
                        inicial = nome_aluno[0].upper() if nome_aluno else 'A'
                        ultima_data = _texto(registros_aluno[0][1].get('data'), 'Sem data')

                        with ui.card().classes('app-card student-record-card w-full p-0'):
                            with ui.row().classes('student-record-head w-full items-center justify-between gap-4 p-5'):
                                with ui.row().classes('items-center gap-4 min-w-0'):
                                    ui.avatar(inicial).classes('brand-badge text-white font-black w-12 h-12 text-lg')
                                    with ui.column().classes('gap-1 min-w-0'):
                                        ui.label(nome_aluno).classes('text-2xl font-black leading-tight line-clamp-1')
                                        ui.label(f'Último registro: {ultima_data}').classes('app-muted text-xs font-bold')
                                with ui.row().classes('items-center gap-2 shrink-0'):
                                    ui.label(f'{len(registros_aluno)} registro(s)').classes('student-record-count')
                                    if aluno_index is not None:
                                        ui.button(icon='folder_open', on_click=lambda i=aluno_index: ui.navigate.to(f'/alunos/{i}/prontuario')).props('flat color=primary round').tooltip('Abrir prontuário')

                            with ui.column().classes('timeline-shell w-full gap-0 p-5 pb-2'):
                                for index, registro in registros_aluno:
                                    intensidade = _texto(registro.get('intensidade'), 'Neutro')
                                    dot_class = _classe_intensidade(intensidade)

                                    with ui.row().classes('timeline-entry w-full items-stretch gap-3'):
                                        ui.label(_texto(registro.get('data'), 'Sem data')).classes('timeline-date pt-3 shrink-0')
                                        with ui.column().classes('timeline-rail pt-3'):
                                            ui.element('span').classes(f'timeline-dot {dot_class}')

                                        with ui.column().classes('timeline-content flex-1 gap-3 p-4 mb-4 min-w-0'):
                                            with ui.row().classes('w-full items-start justify-between gap-3'):
                                                with ui.column().classes('gap-1 min-w-0'):
                                                    with ui.row().classes('items-center gap-2 flex-wrap'):
                                                        ui.label(registro.get('tipo', 'Registro')).classes('app-pill text-xs font-black px-3 py-1')
                                                        ui.label(intensidade).classes('app-pill text-xs font-black px-3 py-1')
                                                    ui.label(f"Registrado por {registro.get('autor', 'Equipe')}").classes('app-muted text-xs font-bold')
                                                if pode_gerir:
                                                    with ui.row().classes('gap-1 shrink-0'):
                                                        ui.button(icon='edit', on_click=lambda i=index, r=registro: abrir_modal(r, i)).props('flat color=primary round size=sm').tooltip('Editar')
                                                        ui.button(icon='delete', on_click=lambda r=registro: confirmar_exclusao(r)).props('flat color=red round size=sm').tooltip('Excluir')

                                            ui.label(_texto(registro.get('descricao'), 'Sem descrição')).classes('app-muted text-sm leading-relaxed')

                                            if registro.get('acao') or registro.get('proximo_passo'):
                                                with ui.grid(columns=1).classes('w-full gap-3 md:grid-cols-2'):
                                                    if registro.get('acao'):
                                                        with ui.column().classes('gap-1'):
                                                            ui.label('Ação tomada').classes('text-xs font-black')
                                                            ui.label(registro.get('acao')).classes('app-muted text-sm leading-relaxed')
                                                    if registro.get('proximo_passo'):
                                                        with ui.column().classes('gap-1'):
                                                            ui.label('Próximo passo').classes('text-xs font-black')
                                                            ui.label(registro.get('proximo_passo')).classes('app-muted text-sm leading-relaxed')

        pesquisa_input.on_value_change(lambda _: atualizar_lista())
        aluno_filter.on_value_change(lambda _: atualizar_lista())
        tipo_filter.on_value_change(lambda _: atualizar_lista())
        intensidade_filter.on_value_change(lambda _: atualizar_lista())
        atualizar_lista()
