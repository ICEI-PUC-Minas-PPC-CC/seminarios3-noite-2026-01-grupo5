import csv
import io

from nicegui import ui

from database import load_data
from layout import frame
from permissions import require_permission


def _texto(valor, padrao='Não informado'):
    valor = str(valor or '').strip()
    return valor if valor else padrao


def _normalizar(valor):
    return str(valor or '').strip().lower()


def _csv_download(nome_arquivo, cabecalhos, linhas):
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=';')
    writer.writerow(cabecalhos)
    writer.writerows(linhas)
    ui.download.content(buffer.getvalue(), nome_arquivo, 'text/csv')


def render():
    with frame('Relatórios'):
        if not require_permission('view_relatorios'):
            return

        agenda = load_data('agenda.json', [])
        alunos = load_data('alunos.json', [])
        turmas = load_data('turmas.json', [])
        responsaveis = load_data('pais.json', [])
        registros = load_data('registros.json', [])
        estrategias = load_data('estrategias.json', [])

        alunos_com_responsavel = {_normalizar(item.get('aluno')) for item in responsaveis if item.get('aluno')}
        alunos_sem_responsavel = [
            aluno for aluno in alunos
            if _normalizar(aluno.get('nome')) not in alunos_com_responsavel
        ]
        alunos_com_atencao = [
            aluno for aluno in alunos
            if aluno.get('diagnostico') or aluno.get('necessidades')
        ]
        total_turmas = len({
            *(turma.get('nome', '').strip() for turma in turmas if turma.get('nome', '').strip()),
            *(aluno.get('turma', '').strip() for aluno in alunos if aluno.get('turma', '').strip()),
        })

        ui.add_css('''
            .report-row {
                background: var(--app-surface-muted) !important;
                border-radius: 8px;
            }

            .report-table-header {
                color: var(--app-muted) !important;
                font-size: 0.72rem;
                font-weight: 900;
                text-transform: uppercase;
            }
        ''')

        def baixar_alunos():
            _csv_download(
                'ruth-see-alunos.csv',
                ['Nome', 'Turma', 'Nascimento', 'Diagnóstico', 'Necessidades', 'Observações'],
                [
                    [
                        aluno.get('nome', ''),
                        aluno.get('turma', ''),
                        aluno.get('nascimento', ''),
                        aluno.get('diagnostico', ''),
                        aluno.get('necessidades', ''),
                        aluno.get('observacoes', ''),
                    ]
                    for aluno in alunos
                ],
            )

        def baixar_responsaveis():
            _csv_download(
                'ruth-see-responsaveis.csv',
                ['Responsável', 'Aluno', 'Parentesco', 'Telefone', 'WhatsApp', 'E-mail', 'Observações'],
                [
                    [
                        item.get('nome', ''),
                        item.get('aluno', ''),
                        item.get('parentesco', ''),
                        item.get('telefone', ''),
                        item.get('whatsapp', ''),
                        item.get('email', ''),
                        item.get('observacoes', ''),
                    ]
                    for item in responsaveis
                ],
            )

        def baixar_registros():
            _csv_download(
                'ruth-see-registros.csv',
                ['Aluno', 'Data', 'Tipo', 'Intensidade', 'Descrição', 'Ação tomada', 'Próximo passo', 'Autor'],
                [
                    [
                        item.get('aluno', ''),
                        item.get('data', ''),
                        item.get('tipo', ''),
                        item.get('intensidade', ''),
                        item.get('descricao', ''),
                        item.get('acao', ''),
                        item.get('proximo_passo', ''),
                        item.get('autor', ''),
                    ]
                    for item in registros
                ],
            )

        with ui.column().classes('w-full gap-5'):
            with ui.row().classes('app-card-colorful w-full items-center justify-between gap-5 p-6'):
                with ui.column().classes('gap-2'):
                    ui.label('📊 Relatórios da escola').classes('app-muted text-sm font-black uppercase')
                    ui.label('Resumo para acompanhamento e organização').classes('text-3xl font-black leading-tight')
                    ui.label('Consulte dados importantes e baixe arquivos CSV para guardar ou abrir em planilhas.').classes('app-muted text-sm')
                ui.label('📈').classes('text-5xl')

            with ui.grid(columns=1).classes('w-full gap-5 lg:grid-cols-3'):
                with ui.card().classes('app-card w-full p-5 lg:col-span-2'):
                    ui.label('Resumo geral').classes('text-xl font-black mb-4')
                    with ui.column().classes('w-full gap-2'):
                        dados_resumo = [
                            ('Alunos cadastrados', len(alunos)),
                            ('Atividades na agenda', len(agenda)),
                            ('Turmas acompanhadas', total_turmas),
                            ('Alunos com atenção registrada', len(alunos_com_atencao)),
                            ('Responsáveis cadastrados', len(responsaveis)),
                            ('Registros de acompanhamento', len(registros)),
                            ('Estratégias cadastradas', len(estrategias)),
                        ]
                        for titulo, valor in dados_resumo:
                            with ui.row().classes('report-row w-full items-center justify-between gap-3 p-3'):
                                ui.label(titulo).classes('font-bold')
                                ui.label(str(valor)).classes('text-xl font-black')

                with ui.card().classes('app-card w-full p-5'):
                    ui.label('Exportações').classes('text-xl font-black mb-4')
                    with ui.column().classes('w-full gap-3'):
                        ui.button('Baixar alunos CSV', icon='download', on_click=baixar_alunos).classes('w-full justify-start').props('flat color=primary no-caps')
                        ui.button('Baixar responsáveis CSV', icon='download', on_click=baixar_responsaveis).classes('w-full justify-start').props('flat color=secondary no-caps')
                        ui.button('Baixar registros CSV', icon='download', on_click=baixar_registros).classes('w-full justify-start').props('flat color=primary no-caps')
                        ui.button('Gerar ficha PDF', icon='print', on_click=lambda: ui.navigate.to('/impressao')).classes('w-full justify-start').props('flat color=secondary no-caps')

            with ui.grid(columns=1).classes('w-full gap-5 lg:grid-cols-2'):
                with ui.card().classes('app-card w-full p-5'):
                    ui.label('Alunos sem responsável vinculado').classes('text-xl font-black mb-4')
                    if not alunos_sem_responsavel:
                        ui.label('Todos os alunos cadastrados têm responsável vinculado.').classes('app-muted text-sm')
                    else:
                        with ui.column().classes('w-full gap-2'):
                            for aluno in alunos_sem_responsavel:
                                with ui.row().classes('report-row w-full items-center justify-between gap-3 p-3'):
                                    with ui.column().classes('gap-0'):
                                        ui.label(_texto(aluno.get('nome'), 'Aluno')).classes('font-black')
                                        ui.label(_texto(aluno.get('turma'), 'Sem turma')).classes('app-muted text-xs font-bold')
                                    ui.button('Abrir pais', icon='contact_phone', on_click=lambda: ui.navigate.to('/pais')).props('flat color=secondary no-caps')

                with ui.card().classes('app-card w-full p-5'):
                    ui.label('Registros recentes').classes('text-xl font-black mb-4')
                    if not registros:
                        ui.label('Nenhum registro de acompanhamento foi criado ainda.').classes('app-muted text-sm')
                    else:
                        with ui.column().classes('w-full gap-2'):
                            for registro in reversed(registros[-5:]):
                                with ui.column().classes('report-row w-full gap-1 p-3'):
                                    with ui.row().classes('items-center gap-2 flex-wrap'):
                                        ui.label(_texto(registro.get('aluno'), 'Aluno')).classes('font-black')
                                        ui.label(_texto(registro.get('tipo'), 'Registro')).classes('app-pill text-xs font-black px-3 py-1')
                                    ui.label(_texto(registro.get('descricao'), 'Sem descrição')).classes('app-muted text-sm leading-relaxed line-clamp-2')
                                    ui.label(f"{registro.get('data', '')} · {registro.get('autor', 'Equipe')}").classes('app-muted text-xs font-bold')
