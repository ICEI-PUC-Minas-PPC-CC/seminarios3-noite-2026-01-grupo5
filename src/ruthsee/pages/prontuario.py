import datetime
from urllib.parse import quote

from nicegui import ui

from database import load_data, save_data
from layout import frame
from permissions import require_permission
from student_links import garantir_ids_alunos, item_vinculado_ao_aluno


def _texto(valor, padrao='Não informado'):
    valor = str(valor or '').strip()
    return valor if valor else padrao


def _telefone_limpo(valor):
    return ''.join(ch for ch in str(valor or '') if ch.isdigit())


def _normalizar(valor):
    return str(valor or '').strip().lower()


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


def _agenda_relacionada(item, nome, turma):
    aluno_item = _normalizar(item.get('aluno') or 'Geral')
    turma_item = _normalizar(item.get('turma') or 'Geral')
    nome_aluno = _normalizar(nome)
    nome_turma = _normalizar(turma)

    if aluno_item and aluno_item != 'geral':
        return aluno_item == nome_aluno
    if turma_item and turma_item != 'geral':
        return turma_item == nome_turma
    return True


def _whatsapp_url(numero, aluno_nome):
    numero_limpo = _telefone_limpo(numero)
    if not numero_limpo:
        return ''
    numero_final = numero_limpo if numero_limpo.startswith('55') else f'55{numero_limpo}'
    mensagem = quote(f'Olá! Aqui é da Ruth See Escola. Gostaria de conversar sobre {aluno_nome}.')
    return f'https://wa.me/{numero_final}?text={mensagem}'


def _estrategias_sugeridas(aluno, estrategias):
    texto_aluno = _normalizar(' '.join([
        aluno.get('diagnostico', ''),
        aluno.get('necessidades', ''),
        aluno.get('observacoes', ''),
    ]))

    palavras_chave = {
        'sensorial': ['sensorial', 'sensibilidade', 'barulho', 'som', 'toque', 'luz'],
        'comunicação': ['comunicação', 'fala', 'linguagem', 'comunicar'],
        'rotina': ['rotina', 'previsibilidade', 'agenda', 'transição'],
        'crise': ['crise', 'manejo', 'sobrecarga', 'agitação'],
        'social': ['social', 'interação', 'grupo', 'colega'],
    }

    selecionadas = []
    for estrategia in estrategias:
        texto_estrategia = _normalizar(' '.join([
            estrategia.get('titulo', ''),
            estrategia.get('categoria', ''),
            estrategia.get('conteudo', ''),
            estrategia.get('desc', ''),
            estrategia.get('quando_usar', ''),
        ]))

        if any(
            any(palavra in texto_aluno for palavra in palavras)
            and any(palavra in texto_estrategia for palavra in palavras)
            for palavras in palavras_chave.values()
        ):
            selecionadas.append(estrategia)

    return selecionadas[:4] or estrategias[:4]


def render(aluno_index):
    with frame('Prontuário do Aluno'):
        if not require_permission('view_alunos'):
            return

        alunos = load_data('alunos.json', [])
        if garantir_ids_alunos(alunos):
            save_data('alunos.json', alunos)

        responsaveis = load_data('pais.json', [])
        registros = load_data('registros.json', [])
        estrategias = load_data('estrategias.json', [])
        agenda = load_data('agenda.json', [])

        try:
            index = int(aluno_index)
        except (TypeError, ValueError):
            index = -1

        if index < 0 or index >= len(alunos):
            with ui.column().classes('app-card w-full items-center justify-center gap-3 py-16 text-center'):
                ui.label('🔎').classes('text-5xl')
                ui.label('Aluno não encontrado').classes('text-2xl font-black')
                ui.label('Volte para a lista de alunos e abra o prontuário novamente.').classes('app-muted text-sm')
                ui.button('Voltar para alunos', icon='arrow_back', on_click=lambda: ui.navigate.to('/alunos')).props('unelevated color=primary')
            return

        aluno = alunos[index]
        nome = _texto(aluno.get('nome'), 'Aluno')
        turma = _texto(aluno.get('turma'), 'Sem turma')
        nascimento = _texto(aluno.get('nascimento'))
        diagnostico = _texto(aluno.get('diagnostico'), 'Sem diagnóstico registrado')
        necessidades = _texto(aluno.get('necessidades'), 'Sem necessidades específicas registradas')
        observacoes = _texto(aluno.get('observacoes'), 'Sem observações cadastradas')
        inicial = nome[0].upper()

        responsaveis_aluno = [
            item for item in responsaveis
            if item_vinculado_ao_aluno(item, aluno)
        ]
        estrategias_aluno = _estrategias_sugeridas(aluno, estrategias)
        registros_aluno = [
            item for item in registros
            if _normalizar(item.get('aluno')) == _normalizar(nome)
        ]
        hoje = _hoje()
        agenda_hoje = sorted(
            [
                item for item in agenda
                if item.get('data') == hoje and _agenda_relacionada(item, nome, turma)
            ],
            key=lambda item: (item.get('hora_inicio', ''), item.get('hora_fim', '')),
        )
        ultimo_registro = registros_aluno[-1] if registros_aluno else None
        tem_diagnostico = bool(str(aluno.get('diagnostico') or '').strip())
        tem_necessidades = bool(str(aluno.get('necessidades') or '').strip())

        plano_apoio = [
            ('Comunicação', 'Usar frases curtas, objetivas e confirmar se a orientação foi compreendida.', '💬', 'soft-blue'),
            ('Previsibilidade', 'Antecipar mudanças de rotina e marcar transições importantes na agenda visual.', '🗓️', 'soft-amber'),
            ('Regulação', 'Observar sinais de cansaço, barulho excessivo ou necessidade de pausa sensorial.', '💛', 'soft-teal'),
        ]
        if tem_necessidades:
            plano_apoio.insert(1, ('Ajustes individuais', necessidades, '🤲', 'soft-green'))

        ui.add_css('''
            .record-hero {
                background: var(--app-happy) !important;
                overflow: hidden;
            }

            .record-mini {
                min-height: 6.25rem;
            }

            .record-mini-icon {
                width: 2.25rem;
                height: 2.25rem;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1rem;
            }

            .record-mini-value {
                color: var(--app-text) !important;
                font-size: 1.45rem;
                font-weight: 900;
                line-height: 1;
            }

            .record-mini-title {
                color: var(--app-muted) !important;
                font-size: 0.72rem;
                font-weight: 900;
                line-height: 1.15;
                text-transform: uppercase;
            }

            .record-panel {
                min-height: 100%;
            }

            .record-section-title {
                color: var(--app-text) !important;
                font-size: 1.25rem;
                font-weight: 900;
                line-height: 1.2;
            }

            .record-line,
            .record-contact,
            .record-care-step,
            .record-agenda-item,
            .record-timeline-card,
            .record-strategy,
            .record-action {
                background: var(--app-surface-muted) !important;
                border: 1px solid var(--app-border);
                border-radius: 8px;
            }

            .record-care-step {
                border-left: 4px solid var(--app-primary);
            }

            .record-agenda-item,
            .record-action {
                transition: transform 160ms ease, border-color 160ms ease;
            }

            .record-agenda-item:hover,
            .record-action:hover {
                transform: translateY(-1px);
                border-color: var(--app-primary);
            }

            .record-time {
                min-width: 5rem;
                color: var(--app-primary-strong) !important;
                font-size: 0.92rem;
                font-weight: 900;
                line-height: 1.1;
            }

            .record-status {
                border: 1px solid var(--app-border);
                border-radius: 999px;
                font-size: 0.68rem;
                font-weight: 900;
                line-height: 1;
                padding: 0.34rem 0.55rem;
                white-space: nowrap;
            }

            .record-timeline-date {
                width: 5.4rem;
                color: var(--app-primary-strong) !important;
                font-size: 0.75rem;
                font-weight: 900;
                line-height: 1.2;
                text-align: right;
            }

            .record-timeline-rail {
                width: 1.15rem;
                align-items: center;
                align-self: stretch;
            }

            .record-timeline-dot {
                width: 0.8rem;
                height: 0.8rem;
                border-radius: 999px;
                background: var(--app-primary);
                border: 3px solid var(--app-surface);
                box-shadow: 0 0 0 1px var(--app-border);
                flex: 0 0 auto;
            }

            .record-timeline-entry:not(:last-child) .record-timeline-rail::after {
                content: '';
                width: 2px;
                flex: 1;
                margin-top: 0.3rem;
                background: var(--app-border);
            }

            .record-empty {
                border: 1px dashed var(--app-border);
                border-radius: 8px;
                background: color-mix(in srgb, var(--app-surface-muted) 72%, transparent) !important;
            }

            @media (max-width: 640px) {
                .record-time,
                .record-timeline-date {
                    min-width: 4rem;
                    width: 4rem;
                    font-size: 0.72rem;
                }
            }
        ''')

        with ui.column().classes('w-full gap-5'):
            with ui.row().classes('app-card-colorful record-hero w-full items-center justify-between gap-5 p-6'):
                with ui.row().classes('items-center gap-5 min-w-0'):
                    ui.avatar(inicial).classes('brand-badge text-white font-black w-20 h-20 text-3xl shrink-0')
                    with ui.column().classes('gap-2 min-w-0'):
                        ui.label('📁 Prontuário escolar individual').classes('app-muted text-xs font-black uppercase')
                        ui.label(nome).classes('text-4xl font-black leading-tight line-clamp-1')
                        with ui.row().classes('items-center gap-2 flex-wrap'):
                            ui.label(f'🏫 {turma}').classes('app-pill text-sm font-black px-3 py-1')
                            ui.label(f'📅 {nascimento}').classes('app-pill text-sm font-black px-3 py-1')
                            ui.label(f'🗓️ {len(agenda_hoje)} atividade(s) hoje').classes('app-pill text-sm font-black px-3 py-1')

                with ui.row().classes('gap-2 flex-wrap justify-end'):
                    ui.button('Voltar', icon='arrow_back', on_click=lambda: ui.navigate.to('/alunos')).props('flat color=primary no-caps')
                    ui.button('Imprimir', icon='print', on_click=lambda i=index: ui.navigate.to(f'/alunos/{i}/impressao')).props('flat color=secondary no-caps')
                    ui.button('Editar', icon='edit', on_click=lambda: ui.navigate.to('/alunos')).props('unelevated color=primary no-caps')

            with ui.grid(columns=1).classes('w-full gap-4 md:grid-cols-2 xl:grid-cols-4'):
                def indicador(titulo, valor, descricao, emoji, cor):
                    with ui.card().classes('app-card record-mini w-full p-4'):
                        with ui.column().classes('w-full h-full justify-between gap-3'):
                            with ui.row().classes('w-full items-start justify-between gap-3'):
                                ui.label(titulo).classes('record-mini-title')
                                ui.label(emoji).classes(f'record-mini-icon {cor}')
                            ui.label(valor).classes('record-mini-value')
                            ui.label(descricao).classes('app-muted text-xs font-bold leading-snug')

                indicador('Família', str(len(responsaveis_aluno)), 'responsável(is) vinculado(s)', '☎️', 'soft-teal')
                indicador('Agenda hoje', str(len(agenda_hoje)), f'rotina de {hoje}', '🗓️', 'soft-amber')
                indicador('Registros', str(len(registros_aluno)), _texto(ultimo_registro.get('data') if ultimo_registro else '', 'sem histórico'), '📝', 'soft-coral')
                indicador('Apoio', 'Sim' if tem_diagnostico or tem_necessidades else 'Aberto', 'perfil de acompanhamento', '🧩', 'soft-blue')

            with ui.grid(columns=1).classes('w-full gap-5 lg:grid-cols-3'):
                with ui.card().classes('app-card record-panel w-full p-5 lg:col-span-2'):
                    with ui.row().classes('w-full items-start justify-between gap-4 mb-4'):
                        with ui.column().classes('gap-1'):
                            ui.label('🧩 Perfil e plano de apoio').classes('record-section-title')
                            ui.label('Informações essenciais para orientar acolhimento, rotina e comunicação.').classes('app-muted text-sm')

                    with ui.grid(columns=1).classes('w-full gap-3 md:grid-cols-2'):
                        with ui.column().classes('record-line gap-1 p-4'):
                            ui.label('Diagnóstico / condição informada').classes('app-muted text-xs font-black uppercase')
                            ui.label(diagnostico).classes('font-black leading-relaxed')
                        with ui.column().classes('record-line gap-1 p-4'):
                            ui.label('Nascimento').classes('app-muted text-xs font-black uppercase')
                            ui.label(nascimento).classes('font-black')

                    with ui.column().classes('record-line gap-2 p-4 mt-3'):
                        ui.label('Necessidades específicas').classes('app-muted text-xs font-black uppercase')
                        ui.label(necessidades).classes('app-muted text-sm leading-relaxed')
                    with ui.column().classes('record-line gap-2 p-4 mt-3'):
                        ui.label('Observações gerais').classes('app-muted text-xs font-black uppercase')
                        ui.label(observacoes).classes('app-muted text-sm leading-relaxed')

                    ui.separator().classes('my-5')
                    ui.label('Plano rápido para a equipe').classes('font-black mb-3')
                    with ui.grid(columns=1).classes('w-full gap-3 md:grid-cols-2'):
                        for titulo, texto, emoji, cor in plano_apoio[:4]:
                            with ui.column().classes('record-care-step gap-2 p-4'):
                                with ui.row().classes('items-center gap-2'):
                                    ui.label(emoji).classes(f'record-mini-icon {cor}')
                                    ui.label(titulo).classes('font-black')
                                ui.label(texto).classes('app-muted text-sm leading-relaxed line-clamp-4')

                with ui.card().classes('app-card record-panel w-full p-5'):
                    with ui.row().classes('w-full items-start justify-between gap-3 mb-4'):
                        with ui.column().classes('gap-1'):
                            ui.label('☎️ Família e contato').classes('record-section-title')
                            ui.label('Acesso rápido para comunicação escola-família.').classes('app-muted text-sm')
                        ui.button(icon='person_add', on_click=lambda: ui.navigate.to('/pais')).props('flat round color=secondary').tooltip('Cadastrar responsável')

                    if not responsaveis_aluno:
                        with ui.column().classes('record-empty items-center text-center gap-3 py-9 px-4'):
                            ui.label('📭').classes('text-5xl')
                            ui.label('Nenhum responsável vinculado').classes('font-black')
                            ui.label('Cadastre pelo menos um contato para emergências, combinados e devolutivas.').classes('app-muted text-sm')
                            ui.button('Cadastrar contato', icon='person_add', on_click=lambda: ui.navigate.to('/pais')).props('unelevated color=secondary no-caps')
                    else:
                        with ui.column().classes('w-full gap-3'):
                            for responsavel in responsaveis_aluno:
                                nome_resp = _texto(responsavel.get('nome'), 'Responsável')
                                parentesco = _texto(responsavel.get('parentesco'), 'Responsável')
                                telefone = _texto(responsavel.get('telefone'))
                                whatsapp = responsavel.get('whatsapp') or responsavel.get('telefone')
                                email = _texto(responsavel.get('email'))
                                whatsapp_url = _whatsapp_url(whatsapp, nome)

                                with ui.column().classes('record-contact gap-2 p-4'):
                                    ui.label(parentesco).classes('app-pill text-xs font-black px-3 py-1 w-fit')
                                    ui.label(nome_resp).classes('font-black text-lg leading-tight')
                                    ui.label(f'☎️ {telefone}').classes('app-muted text-sm')
                                    ui.label(f'✉️ {email}').classes('app-muted text-sm')
                                    with ui.row().classes('gap-2 flex-wrap pt-1'):
                                        if whatsapp_url:
                                            ui.link('WhatsApp', whatsapp_url, new_tab=True).classes('q-btn q-btn-item non-selectable no-outline q-btn--flat q-btn--rectangle text-primary font-bold px-3 py-2')
                                        if responsavel.get('email'):
                                            ui.link('E-mail', f"mailto:{responsavel.get('email')}", new_tab=True).classes('q-btn q-btn-item non-selectable no-outline q-btn--flat q-btn--rectangle text-primary font-bold px-3 py-2')

            with ui.grid(columns=1).classes('w-full gap-5 lg:grid-cols-2'):
                with ui.card().classes('app-card record-panel w-full p-5'):
                    with ui.row().classes('w-full items-start justify-between gap-4 mb-4'):
                        with ui.column().classes('gap-1'):
                            ui.label('🗓️ Rotina de hoje').classes('record-section-title')
                            ui.label(f'Atividades relacionadas ao aluno em {hoje}.').classes('app-muted text-sm')
                        ui.button('Abrir agenda', icon='event_note', on_click=lambda: ui.navigate.to('/agenda')).props('flat color=primary no-caps')

                    if not agenda_hoje:
                        with ui.column().classes('record-empty items-center text-center gap-3 py-9 px-4'):
                            ui.label('🧭').classes('text-5xl')
                            ui.label('Sem rotina vinculada hoje').classes('font-black')
                            ui.label('Cadastre atividades gerais, da turma ou específicas do aluno na agenda.').classes('app-muted text-sm')
                            ui.button('Planejar rotina', icon='add', on_click=lambda: ui.navigate.to('/agenda')).props('unelevated color=primary no-caps')
                    else:
                        with ui.column().classes('w-full gap-3'):
                            for item in agenda_hoje[:6]:
                                hora = _texto(item.get('hora_inicio'), '--:--')
                                fim = item.get('hora_fim', '').strip()
                                status = _texto(item.get('status'), 'Planejado')
                                linha = ui.row().classes('record-agenda-item w-full items-center gap-4 p-4')
                                linha.on('click', lambda: ui.navigate.to('/agenda'))
                                with linha:
                                    ui.label(f'{hora}{f" - {fim}" if fim else ""}').classes('record-time shrink-0')
                                    with ui.column().classes('gap-1 flex-1 min-w-0'):
                                        with ui.row().classes('items-center gap-2 flex-wrap'):
                                            ui.label(_texto(item.get('tipo'), 'Atividade')).classes('app-pill text-xs font-black px-3 py-1')
                                            ui.label(status).classes(f'record-status {_status_class(status)}')
                                        ui.label(_texto(item.get('titulo'), 'Atividade')).classes('font-black leading-tight')
                                        ui.label(f"{_texto(item.get('turma'), 'Geral')} · {_texto(item.get('aluno'), 'Geral')} · {_texto(item.get('responsavel'), 'Equipe')}").classes('app-muted text-xs font-bold')

                with ui.card().classes('app-card record-panel w-full p-5'):
                    with ui.row().classes('w-full items-start justify-between gap-4 mb-4'):
                        with ui.column().classes('gap-1'):
                            ui.label('📝 Linha do tempo').classes('record-section-title')
                            ui.label('Registros recentes de acompanhamento do aluno.').classes('app-muted text-sm')
                        ui.button('Novo registro', icon='note_add', on_click=lambda: ui.navigate.to('/registros')).props('flat color=primary no-caps')

                    if not registros_aluno:
                        with ui.column().classes('record-empty items-center text-center gap-3 py-9 px-4'):
                            ui.label('📝').classes('text-5xl')
                            ui.label('Nenhum registro ainda').classes('font-black')
                            ui.label('Quando a equipe registrar evoluções, observações ou próximos passos, eles aparecerão aqui.').classes('app-muted text-sm')
                            ui.button('Criar registro', icon='note_add', on_click=lambda: ui.navigate.to('/registros')).props('unelevated color=primary no-caps')
                    else:
                        with ui.column().classes('w-full gap-0'):
                            for registro in reversed(registros_aluno[-5:]):
                                with ui.row().classes('record-timeline-entry w-full items-stretch gap-3'):
                                    ui.label(_texto(registro.get('data'), 'Sem data')).classes('record-timeline-date pt-3 shrink-0')
                                    with ui.column().classes('record-timeline-rail pt-3'):
                                        ui.element('span').classes('record-timeline-dot')

                                    with ui.column().classes('record-timeline-card flex-1 gap-3 p-4 mb-4 min-w-0'):
                                        with ui.row().classes('items-center gap-2 flex-wrap'):
                                            ui.label(_texto(registro.get('tipo'), 'Registro')).classes('app-pill text-xs font-black px-3 py-1')
                                            ui.label(_texto(registro.get('intensidade'), 'Neutro')).classes('app-pill text-xs font-black px-3 py-1')
                                        ui.label(_texto(registro.get('descricao'), 'Sem descrição')).classes('app-muted text-sm leading-relaxed')
                                        if registro.get('acao') or registro.get('proximo_passo'):
                                            with ui.grid(columns=1).classes('w-full gap-3 md:grid-cols-2'):
                                                if registro.get('acao'):
                                                    with ui.column().classes('gap-1'):
                                                        ui.label('Ação tomada').classes('text-xs font-black uppercase')
                                                        ui.label(registro.get('acao')).classes('app-muted text-sm leading-relaxed')
                                                if registro.get('proximo_passo'):
                                                    with ui.column().classes('gap-1'):
                                                        ui.label('Próximo passo').classes('text-xs font-black uppercase')
                                                        ui.label(registro.get('proximo_passo')).classes('app-muted text-sm leading-relaxed')
                                        ui.label(f"Registrado por {registro.get('autor', 'Equipe')}").classes('app-muted text-xs font-bold')

            with ui.grid(columns=1).classes('w-full gap-5 lg:grid-cols-3'):
                with ui.card().classes('app-card record-panel w-full p-5 lg:col-span-2'):
                    with ui.row().classes('w-full items-start justify-between gap-4 mb-4'):
                        with ui.column().classes('gap-1'):
                            ui.label('💡 Estratégias sugeridas').classes('record-section-title')
                            ui.label('Ideias práticas para apoiar a rotina do aluno sem sobrecarregar a equipe.').classes('app-muted text-sm')
                        ui.button('Biblioteca', icon='auto_awesome', on_click=lambda: ui.navigate.to('/estrategias')).props('flat color=primary no-caps')

                    if not estrategias_aluno:
                        with ui.column().classes('record-empty items-center text-center gap-3 py-9 px-4'):
                            ui.label('💡').classes('text-5xl')
                            ui.label('Nenhuma estratégia cadastrada ainda').classes('font-black')
                            ui.label('Adicione estratégias para que o prontuário sugira apoios mais úteis.').classes('app-muted text-sm')
                    else:
                        with ui.grid(columns=1).classes('w-full gap-3 md:grid-cols-2'):
                            for estrategia in estrategias_aluno:
                                titulo = _texto(estrategia.get('titulo'), 'Estratégia')
                                categoria = _texto(estrategia.get('categoria'), 'Geral')
                                conteudo = _texto(estrategia.get('conteudo') or estrategia.get('desc'), 'Sem descrição cadastrada.')
                                with ui.column().classes('record-strategy gap-2 p-4'):
                                    ui.label(categoria).classes('app-pill text-xs font-black px-3 py-1 w-fit')
                                    ui.label(titulo).classes('font-black text-lg leading-tight')
                                    ui.label(conteudo).classes('app-muted text-sm leading-relaxed line-clamp-4')

                with ui.card().classes('app-card record-panel w-full p-5'):
                    ui.label('📌 Ações rápidas').classes('record-section-title mb-4')
                    with ui.column().classes('w-full gap-3'):
                        def acao(label, icon, rota, cor='primary'):
                            linha = ui.row().classes('record-action w-full items-center justify-between gap-3 p-4 cursor-pointer')
                            linha.on('click', lambda r=rota: ui.navigate.to(r))
                            with linha:
                                with ui.row().classes('items-center gap-3 min-w-0'):
                                    ui.icon(icon, size='sm').classes(f'text-{cor}')
                                    ui.label(label).classes('font-black leading-tight')
                                ui.icon('arrow_forward', size='xs').classes('app-muted')

                        acao('Registrar acompanhamento', 'edit_note', '/registros')
                        acao('Planejar rotina do dia', 'event_note', '/agenda')
                        acao('Ver responsáveis', 'contact_phone', '/pais', 'secondary')
                        acao('Imprimir ficha PDF', 'print', f'/alunos/{index}/impressao', 'secondary')
                        acao('Voltar para alunos', 'groups', '/alunos')
