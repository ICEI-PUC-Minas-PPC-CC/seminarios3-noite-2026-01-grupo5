import datetime

from nicegui import ui

from database import load_data
from layout import frame
from permissions import require_permission


def _texto(valor, padrao='Não informado'):
    valor = str(valor or '').strip()
    return valor if valor else padrao


def _normalizar(valor):
    return str(valor or '').strip().lower()


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


def render(aluno_index=None):
    with frame('Impressão/PDF'):
        if not require_permission('view_impressao'):
            return

        alunos = load_data('alunos.json', [])

        ui.add_css('''
            .print-sheet {
                width: min(100%, 210mm);
                min-height: 297mm;
                margin: 0 auto 2rem;
                padding: 15mm !important;
                overflow: hidden;
            }

            .medical-header {
                border: 1px solid var(--app-border);
                border-radius: 8px;
                overflow: hidden;
            }

            .medical-header-band {
                background: var(--app-brand) !important;
                color: white !important;
                min-height: 0.45rem;
            }

            .medical-logo-box {
                width: 4.6rem;
                height: 4.6rem;
                border: 1px solid var(--app-border);
                border-radius: 8px;
                background: #ffffff !important;
            }

            .medical-doc-code {
                background: var(--app-surface-muted) !important;
                border: 1px solid var(--app-border);
                border-radius: 8px;
                font-size: 0.68rem;
                font-weight: 900;
                letter-spacing: 0;
                padding: 0.34rem 0.54rem;
                text-transform: uppercase;
            }

            .medical-title {
                color: var(--app-text) !important;
                font-size: 1.45rem;
                font-weight: 900;
                line-height: 1.08;
            }

            .medical-subtitle {
                color: var(--app-muted) !important;
                font-size: 0.76rem;
                font-weight: 800;
                line-height: 1.25;
                text-transform: uppercase;
            }

            .medical-section {
                border: 1px solid var(--app-border);
                border-radius: 8px;
                break-inside: avoid;
                overflow: hidden;
            }

            .medical-section-title {
                background: var(--app-surface-muted) !important;
                color: var(--app-text) !important;
                border-bottom: 1px solid var(--app-border);
                font-size: 0.78rem;
                font-weight: 900;
                letter-spacing: 0;
                padding: 0.55rem 0.75rem;
                text-transform: uppercase;
            }

            .medical-field {
                border: 1px solid var(--app-border);
                margin: -1px 0 0 -1px;
                min-height: 3.25rem;
                padding: 0.65rem 0.75rem;
            }

            .medical-field-label {
                color: var(--app-muted) !important;
                font-size: 0.66rem;
                font-weight: 900;
                line-height: 1.15;
                text-transform: uppercase;
            }

            .medical-field-value {
                color: var(--app-text) !important;
                font-size: 0.9rem;
                font-weight: 800;
                line-height: 1.25;
            }

            .medical-textbox {
                min-height: 4.25rem;
                padding: 0.75rem;
            }

            .medical-list-row {
                border-bottom: 1px solid var(--app-border);
                padding: 0.68rem 0.75rem;
            }

            .medical-list-row:last-child {
                border-bottom: 0;
            }

            .medical-timeline-date {
                background: var(--app-surface-muted) !important;
                border: 1px solid var(--app-border);
                border-radius: 8px;
                min-width: 5.5rem;
                padding: 0.45rem 0.5rem;
                text-align: center;
            }

            .medical-signature-line {
                border-top: 1px solid var(--app-border);
                min-height: 3.75rem;
            }

            .medical-signatures {
                margin-top: 1.5rem;
            }

            .medical-footer-note {
                display: block;
                margin-top: 1.25rem;
            }

            .print-muted {
                color: var(--app-muted) !important;
            }

            @media print {
                @page {
                    size: A4;
                    margin: 8mm;
                }

                html, body {
                    width: 210mm !important;
                    min-height: 297mm !important;
                    margin: 0 !important;
                    padding: 0 !important;
                }

                body, .q-layout, .q-page-container, .q-page {
                    background: #ffffff !important;
                    color: #111827 !important;
                    margin: 0 !important;
                    padding: 0 !important;
                    min-height: 0 !important;
                    width: 100% !important;
                    overflow: visible !important;
                }

                .app-header, .app-drawer, .q-drawer, .q-header,
                .print-controls, .emoji-badge, .app-page-title {
                    display: none !important;
                }

                body * {
                    visibility: hidden !important;
                }

                .print-only-root, .print-only-root * {
                    visibility: visible !important;
                }

                .q-page-container {
                    padding: 0 !important;
                }

                .mt-16, .py-6, .px-5, .gap-6, .max-w-7xl, .mx-auto {
                    margin: 0 !important;
                    padding: 0 !important;
                    gap: 0 !important;
                    max-width: none !important;
                }

                .q-page-container > div,
                .q-page-container .nicegui-content,
                body > div,
                main {
                    margin: 0 !important;
                    padding: 0 !important;
                    max-width: none !important;
                    width: 100% !important;
                }

                .print-only-root {
                    display: block !important;
                    position: absolute !important;
                    top: 0 !important;
                    left: 0 !important;
                    right: 0 !important;
                    margin: 0 auto !important;
                    padding: 0 !important;
                    width: 100% !important;
                    max-width: none !important;
                    transform: none !important;
                }

                .print-sheet, .medical-section, .medical-header, .app-card {
                    background: #ffffff !important;
                    color: #111827 !important;
                    box-shadow: none !important;
                    border-color: #9ca3af !important;
                }

                .print-sheet {
                    width: 100% !important;
                    max-width: 198mm !important;
                    min-height: auto !important;
                    max-height: 281mm !important;
                    margin: 0 auto !important;
                    padding: 0 !important;
                    border: none !important;
                    overflow: hidden !important;
                    page-break-after: avoid !important;
                    break-after: avoid !important;
                    font-size: 10px !important;
                }

                .medical-header-band {
                    background: #1f4f8f !important;
                    print-color-adjust: exact;
                    -webkit-print-color-adjust: exact;
                }

                .medical-section-title, .medical-doc-code, .medical-timeline-date {
                    background: #eef2f7 !important;
                    border-color: #9ca3af !important;
                    print-color-adjust: exact;
                    -webkit-print-color-adjust: exact;
                }

                .medical-field, .medical-list-row, .medical-signature-line {
                    border-color: #9ca3af !important;
                }

                .medical-header {
                    margin-bottom: 1.8mm !important;
                }

                .medical-header .p-4 {
                    padding: 1.8mm !important;
                }

                .medical-logo-box {
                    width: 13mm !important;
                    height: 13mm !important;
                }

                .medical-logo-box img {
                    width: 11mm !important;
                    height: 11mm !important;
                }

                .medical-title {
                    font-size: 13px !important;
                }

                .medical-subtitle {
                    font-size: 7px !important;
                }

                .medical-section {
                    margin-bottom: 1.8mm !important;
                    break-inside: avoid !important;
                    page-break-inside: avoid !important;
                }

                .medical-section-title {
                    font-size: 8px !important;
                    padding: 1.2mm 1.8mm !important;
                }

                .medical-field {
                    min-height: 10mm !important;
                    padding: 1.3mm 1.8mm !important;
                }

                .medical-field-label {
                    font-size: 7px !important;
                }

                .medical-field-value {
                    font-size: 10px !important;
                    line-height: 1.15 !important;
                }

                .medical-textbox {
                    min-height: 10mm !important;
                    padding: 1.5mm 1.8mm !important;
                }

                .medical-list-row {
                    padding: 1.3mm 1.8mm !important;
                }

                .medical-timeline-date {
                    min-width: 18mm !important;
                    padding: 1mm !important;
                }

                .medical-signature-line {
                    min-height: 8mm !important;
                }

                .medical-signatures {
                    gap: 6mm !important;
                    margin-top: 2mm !important;
                }

                .medical-footer-note {
                    margin-top: 1mm !important;
                }

                .print-muted, .app-muted {
                    color: #4b5563 !important;
                }

                .app-pill {
                    color: #111827 !important;
                    border-color: #d9dde5 !important;
                    background: #f7f8fb !important;
                }

                button, .q-btn {
                    display: none !important;
                }
            }
        ''')

        def opcoes_alunos():
            return {
                index: _texto(aluno.get('nome'), f'Aluno {index + 1}')
                for index, aluno in enumerate(alunos)
            }

        def selecionar_inicial():
            try:
                index = int(aluno_index) if aluno_index is not None else -1
            except (TypeError, ValueError):
                index = -1

            if 0 <= index < len(alunos):
                return index
            return 0 if alunos else None

        def renderizar_ficha():
            container_ficha.clear()

            with container_ficha:
                if not alunos:
                    with ui.column().classes('app-card w-full items-center justify-center gap-3 py-16 text-center'):
                        ui.label('📄').classes('text-5xl')
                        ui.label('Nenhum aluno cadastrado').classes('text-xl font-black')
                        ui.label('Cadastre alunos antes de gerar fichas para impressão.').classes('print-muted text-sm')
                        ui.button('Abrir alunos', icon='groups', on_click=lambda: ui.navigate.to('/alunos')).props('unelevated color=primary')
                    return

                try:
                    aluno_index_atual = int(aluno_select.value)
                except (TypeError, ValueError):
                    return

                alunos_atualizados = load_data('alunos.json', [])
                responsaveis_atualizados = load_data('pais.json', [])
                registros_atualizados = load_data('registros.json', [])
                estrategias_atualizadas = load_data('estrategias.json', [])

                if aluno_index_atual < 0 or aluno_index_atual >= len(alunos_atualizados):
                    return

                aluno = alunos_atualizados[aluno_index_atual]

                nome = _texto(aluno.get('nome'), 'Aluno')
                turma = _texto(aluno.get('turma'), 'Sem turma')
                nascimento = _texto(aluno.get('nascimento'))
                diagnostico = _texto(aluno.get('diagnostico'), 'Sem diagnóstico registrado')
                necessidades = _texto(aluno.get('necessidades'), 'Sem necessidades específicas registradas')
                observacoes = _texto(aluno.get('observacoes'), 'Sem observações cadastradas')
                data_geracao = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')

                responsaveis_aluno = [
                    item for item in responsaveis_atualizados
                    if _normalizar(item.get('aluno')) == _normalizar(nome)
                ]
                registros_aluno = [
                    item for item in registros_atualizados
                    if _normalizar(item.get('aluno')) == _normalizar(nome)
                ]
                estrategias_aluno = _estrategias_sugeridas(aluno, estrategias_atualizadas)[:3]

                with ui.card().classes('app-card print-sheet w-full'):
                    with ui.column().classes('medical-header w-full mb-4'):
                        ui.element('div').classes('medical-header-band w-full')
                        with ui.row().classes('w-full items-center justify-between gap-4 p-4'):
                            with ui.row().classes('items-center gap-4 min-w-0'):
                                with ui.column().classes('medical-logo-box items-center justify-center shrink-0'):
                                    ui.image('/assets/ruth-see-logo.png').classes('w-16 h-16 object-contain')
                                with ui.column().classes('gap-1 min-w-0'):
                                    ui.label('Ruth See Escola').classes('medical-title')
                                    ui.label('Prontuário escolar individual').classes('medical-subtitle')
                                    ui.label('Documento interno de acompanhamento pedagógico e comunicação com a família').classes('print-muted text-xs leading-relaxed')
                            with ui.column().classes('items-end gap-2 shrink-0'):
                                ui.label(f'RS-{aluno_index_atual + 1:04d}').classes('medical-doc-code')
                                ui.label(f'Emitido em {data_geracao}').classes('print-muted text-xs font-bold')

                    with ui.column().classes('medical-section w-full mb-4'):
                        ui.label('Identificação do aluno').classes('medical-section-title')
                        with ui.grid(columns=2).classes('w-full gap-0 md:grid-cols-4'):
                            for titulo, valor in [
                                ('Nome completo', nome),
                                ('Turma', turma),
                                ('Nascimento', nascimento),
                                ('Responsáveis vinculados', str(len(responsaveis_aluno))),
                            ]:
                                with ui.column().classes('medical-field gap-1'):
                                    ui.label(titulo).classes('medical-field-label')
                                    ui.label(valor).classes('medical-field-value')

                    with ui.column().classes('medical-section w-full mb-4'):
                        ui.label('Perfil de acompanhamento').classes('medical-section-title')
                        with ui.grid(columns=1).classes('w-full gap-0 md:grid-cols-2'):
                            for titulo, valor in [
                                ('Diagnóstico / condição informada', diagnostico),
                                ('Necessidades específicas', necessidades),
                            ]:
                                with ui.column().classes('medical-field gap-1'):
                                    ui.label(titulo).classes('medical-field-label')
                                    ui.label(valor).classes('medical-field-value')
                        with ui.column().classes('medical-textbox gap-2'):
                            ui.label('Observações gerais').classes('medical-field-label')
                            ui.label(observacoes).classes('print-muted text-sm leading-relaxed')

                    with ui.grid(columns=1).classes('w-full gap-4 md:grid-cols-2 mb-4'):
                        with ui.column().classes('medical-section w-full'):
                            ui.label('Responsáveis e contatos').classes('medical-section-title')
                            if not responsaveis_aluno:
                                with ui.column().classes('medical-list-row'):
                                    ui.label('Nenhum responsável vinculado ao aluno.').classes('print-muted text-sm')
                            else:
                                for responsavel in responsaveis_aluno:
                                    with ui.column().classes('medical-list-row gap-1'):
                                        ui.label(f"{_texto(responsavel.get('parentesco'), 'Responsável')} - {_texto(responsavel.get('nome'), 'Nome não informado')}").classes('font-black text-sm')
                                        ui.label(f"Telefone: {_texto(responsavel.get('telefone'))} | WhatsApp: {_texto(responsavel.get('whatsapp'))}").classes('print-muted text-xs leading-relaxed')
                                        ui.label(f"E-mail: {_texto(responsavel.get('email'))}").classes('print-muted text-xs leading-relaxed')
                                        if responsavel.get('observacoes'):
                                            ui.label(responsavel.get('observacoes')).classes('print-muted text-xs leading-relaxed')

                        with ui.column().classes('medical-section w-full'):
                            ui.label('Estratégias recomendadas').classes('medical-section-title')
                            if not estrategias_aluno:
                                with ui.column().classes('medical-list-row'):
                                    ui.label('Nenhuma estratégia cadastrada ainda.').classes('print-muted text-sm')
                            else:
                                for estrategia in estrategias_aluno:
                                    with ui.column().classes('medical-list-row gap-1'):
                                        ui.label(_texto(estrategia.get('titulo'), 'Estratégia')).classes('font-black text-sm')
                                        ui.label(_texto(estrategia.get('categoria'), 'Geral')).classes('medical-field-label')
                                        ui.label(_texto(estrategia.get('conteudo') or estrategia.get('desc'), 'Sem descrição cadastrada.')).classes('print-muted text-xs leading-relaxed')

                    with ui.column().classes('medical-section w-full mb-4'):
                        ui.label('Evolução / registros recentes').classes('medical-section-title')
                        if not registros_aluno:
                            with ui.column().classes('medical-list-row'):
                                ui.label('Nenhum registro de acompanhamento cadastrado.').classes('print-muted text-sm')
                        else:
                            for registro in reversed(registros_aluno[-3:]):
                                with ui.row().classes('medical-list-row w-full items-start gap-3'):
                                    with ui.column().classes('medical-timeline-date gap-1 shrink-0'):
                                        ui.label(_texto(registro.get('data'), 'Sem data')).classes('font-black text-xs')
                                        ui.label(_texto(registro.get('intensidade'), 'Neutro')).classes('print-muted text-[10px] font-black uppercase')
                                    with ui.column().classes('gap-1 flex-1 min-w-0'):
                                        ui.label(f"{_texto(registro.get('tipo'), 'Registro')} - {_texto(registro.get('autor'), 'Equipe')}").classes('font-black text-sm')
                                        ui.label(_texto(registro.get('descricao'), 'Sem descrição')).classes('print-muted text-sm leading-relaxed')
                                        if registro.get('acao'):
                                            ui.label(f"Ação tomada: {registro.get('acao')}").classes('print-muted text-xs leading-relaxed')
                                        if registro.get('proximo_passo'):
                                            ui.label(f"Próximo passo: {registro.get('proximo_passo')}").classes('print-muted text-xs leading-relaxed')

                    with ui.grid(columns=1).classes('medical-signatures w-full gap-8 md:grid-cols-2 mt-10'):
                        with ui.column().classes('medical-signature-line justify-end gap-1 pt-2'):
                            ui.label('Responsável pela emissão').classes('print-muted text-xs font-black uppercase')
                        with ui.column().classes('medical-signature-line justify-end gap-1 pt-2'):
                            ui.label('Coordenação / equipe escolar').classes('print-muted text-xs font-black uppercase')

                    ui.label('Documento confidencial para uso interno da Ruth See Escola.').classes('medical-footer-note print-muted text-[10px] font-bold mt-6')

                    if aluno_index_atual is not None:
                        with ui.row().classes('print-controls w-full justify-end mt-5'):
                            ui.button(
                                'Abrir prontuário',
                                icon='folder_open',
                                on_click=lambda i=aluno_index_atual: ui.navigate.to(f'/alunos/{i}/prontuario'),
                            ).props('flat color=primary no-caps')

        with ui.column().classes('w-full gap-5'):
            with ui.row().classes('app-card-colorful print-controls w-full items-center justify-between gap-5 p-6'):
                with ui.column().classes('gap-2'):
                    ui.label('🖨️ Impressão e PDF').classes('app-muted text-sm font-black uppercase')
                    ui.label('Ficha pronta para reunião ou arquivo').classes('text-3xl font-black leading-tight')
                    ui.label('Selecione um aluno, revise a ficha e use imprimir para salvar em PDF.').classes('app-muted text-sm')
                ui.button('Imprimir / salvar PDF', icon='print', on_click=lambda: ui.run_javascript('window.print()')).props('unelevated color=primary')

            with ui.row().classes('app-toolbar print-controls w-full items-center justify-between gap-4 p-4'):
                with ui.row().classes('flex-1 items-center gap-3 flex-wrap'):
                    aluno_select = ui.select(opcoes_alunos(), value=selecionar_inicial(), label='Aluno').props('outlined dense').classes('w-full md:max-w-md flex-1')
                    ui.button('Atualizar ficha', icon='refresh', on_click=renderizar_ficha).props('flat color=primary no-caps')
                    ui.button('Relatórios', icon='analytics', on_click=lambda: ui.navigate.to('/relatorios')).props('flat color=secondary no-caps')

            container_ficha = ui.column().classes('print-only-root w-full items-center')

        aluno_select.on_value_change(lambda _: renderizar_ficha())
        renderizar_ficha()
