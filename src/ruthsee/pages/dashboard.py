import datetime

from nicegui import app, ui

from database import load_data
from layout import frame
from permissions import has_permission, require_permission


def _to_float(value):
    try:
        return float(str(value).replace(',', '.'))
    except (TypeError, ValueError):
        return 0.0


def _texto(valor, padrao='Não informado'):
    valor = str(valor or '').strip()
    return valor if valor else padrao


def _status_class(status):
    mapa = {
        'Planejado': 'soft-blue',
        'Em andamento': 'soft-amber',
        'Concluído': 'soft-green',
        'Atenção': 'soft-coral',
        'Reprogramado': 'soft-violet',
    }
    return mapa.get(status, 'soft-teal')


def render():
    with frame('Dashboard'):
        if not require_permission('view_dashboard'):
            return

        alunos_data = load_data('alunos.json', [])
        agenda_data = load_data('agenda.json', [])
        pais_data = load_data('pais.json', [])
        turmas_data = load_data('turmas.json', [])
        comunicados_data = load_data('comunicados.json', [])
        registros_data = load_data('registros.json', [])
        estrategias_data = load_data('estrategias.json', [])
        pode_publicar = has_permission('manage_comunicados')
        pode_ver_agenda = has_permission('view_agenda')
        pode_gerir_agenda = has_permission('manage_agenda')
        pode_ver_alunos = has_permission('view_alunos')
        pode_ver_turmas = has_permission('view_turmas')
        pode_ver_pais = has_permission('view_pais')
        pode_ver_registros = has_permission('view_registros')
        pode_ver_impressao = has_permission('view_impressao')
        pode_ver_estrategias = has_permission('view_estrategias')
        pode_ver_admin = has_permission('view_admin')

        total_alunos = len(alunos_data)
        hoje = datetime.datetime.now().strftime('%d/%m/%Y')
        agenda_hoje = sorted(
            [item for item in agenda_data if item.get('data') == hoje],
            key=lambda item: (item.get('hora_inicio', ''), item.get('hora_fim', '')),
        )
        total_agenda_hoje = len(agenda_hoje)
        total_pais = len(pais_data)
        total_turmas = len({
            *(turma.get('nome', '').strip() for turma in turmas_data if turma.get('nome', '').strip()),
            *(aluno.get('turma', '').strip() for aluno in alunos_data if aluno.get('turma', '').strip()),
        })
        total_registros = len(registros_data)
        total_estrategias = len(estrategias_data)
        total_com_atencao = sum(1 for aluno in alunos_data if aluno.get('diagnostico') or aluno.get('necessidades'))

        ui.add_css('''
            .dashboard-focus {
                background: var(--app-happy) !important;
            }

            .dashboard-shortcut {
                min-height: 124px;
                cursor: pointer;
                transition: transform 160ms ease, border-color 160ms ease;
            }

            .dashboard-summary {
                width: 8.75rem;
                height: 5.35rem;
            }

            .dashboard-agenda-row {
                background: var(--app-surface-muted) !important;
                border: 1px solid var(--app-border);
                border-radius: 8px;
                cursor: pointer;
                transition: transform 160ms ease, border-color 160ms ease, background-color 160ms ease;
            }

            .dashboard-agenda-row:hover {
                transform: translateY(-1px);
                border-color: var(--app-primary);
                background: color-mix(in srgb, var(--app-primary) 9%, var(--app-surface)) !important;
            }

            .dashboard-agenda-time {
                min-width: 5.5rem;
                color: var(--app-primary-strong) !important;
                font-size: 0.95rem;
                font-weight: 900;
                line-height: 1.1;
            }

            .dashboard-agenda-status {
                border: 1px solid var(--app-border);
                border-radius: 999px;
                font-size: 0.7rem;
                font-weight: 900;
                line-height: 1;
                padding: 0.35rem 0.55rem;
                white-space: nowrap;
            }

            .dashboard-shortcut:hover {
                transform: translateY(-2px);
                border-color: var(--app-primary);
            }

            .shortcut-icon {
                width: 2.25rem;
                height: 2.25rem;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.05rem;
            }

            .shortcut-value {
                background: var(--app-surface-muted);
                border: 1px solid var(--app-border);
                border-radius: 999px;
                font-size: 0.78rem;
                font-weight: 900;
                line-height: 1;
                padding: 0.38rem 0.58rem;
            }

            .summary-number {
                color: var(--app-text) !important;
                font-size: 1.55rem;
                line-height: 1;
                font-weight: 900;
            }

            .summary-title {
                color: var(--app-muted) !important;
                font-size: 0.68rem;
                font-weight: 900;
                line-height: 1.15;
                text-transform: uppercase;
            }

            @media (max-width: 640px) {
                .dashboard-agenda-time {
                    min-width: 4.25rem;
                    font-size: 0.82rem;
                }
            }
        ''')

        with ui.card().classes('app-card-colorful dashboard-focus w-full p-6'):
            with ui.row().classes('w-full justify-between items-start gap-5 mb-4'):
                with ui.column().classes('gap-1'):
                    ui.label('📣 Comunicados internos').classes('text-2xl font-black')
                    ui.label('Avisos importantes da escola para toda a equipe.').classes('app-muted text-sm')
                if pode_publicar:
                    ui.button('Publicar comunicado', icon='campaign', on_click=lambda: ui.navigate.to('/admin')).props('unelevated color=primary')

            if not comunicados_data:
                with ui.column().classes('w-full items-center justify-center gap-3 py-10 text-center'):
                    ui.label('📭').classes('text-5xl')
                    ui.label('Nenhum comunicado no momento').classes('text-lg font-black')
                    ui.label('Quando a coordenação publicar avisos, eles aparecerão em destaque aqui.').classes('app-muted text-sm')
            else:
                with ui.column().classes('w-full gap-3'):
                    for comunicado in reversed(comunicados_data[-3:]):
                        with ui.row().classes('w-full gap-3 p-4 rounded-lg soft-blue'):
                            ui.label('📌').classes('text-2xl')
                            with ui.column().classes('gap-1 flex-1'):
                                ui.label(comunicado.get('titulo', 'Sem título')).classes('font-black text-lg')
                                ui.label(f"{comunicado.get('data', '')} · {comunicado.get('autor', '')}").classes('app-muted text-xs font-bold')
                                ui.label(comunicado.get('mensagem', '')).classes('app-muted text-sm leading-relaxed')

        with ui.card().classes('app-card w-full p-5'):
            with ui.row().classes('w-full items-start justify-between gap-4 mb-4'):
                with ui.column().classes('gap-1'):
                    ui.label('🗓️ Agenda de hoje').classes('text-xl font-black')
                    ui.label(f'Rotina prevista para {hoje}, com horários, turma, aluno e responsável.').classes('app-muted text-sm')
                ui.button('Abrir agenda', icon='event_note', on_click=lambda: ui.navigate.to('/agenda')).props('flat color=primary no-caps')

            if not agenda_hoje:
                with ui.column().classes('w-full items-center justify-center gap-3 py-8 text-center soft-amber rounded-lg'):
                    ui.label('🧭').classes('text-4xl')
                    ui.label('Nenhuma atividade programada para hoje').classes('font-black')
                    ui.label('Cadastre a rotina do dia para deixar a equipe alinhada desde o início.').classes('app-muted text-sm')
                    if pode_gerir_agenda:
                        ui.button('Criar atividade', icon='add', on_click=lambda: ui.navigate.to('/agenda')).props('unelevated color=primary no-caps')
            else:
                with ui.column().classes('w-full gap-3'):
                    for item in agenda_hoje[:4]:
                        hora = _texto(item.get('hora_inicio'), '--:--')
                        fim = item.get('hora_fim', '').strip()
                        status = _texto(item.get('status'), 'Planejado')
                        linha = ui.row().classes('dashboard-agenda-row w-full items-center gap-4 p-4')
                        linha.on('click', lambda: ui.navigate.to('/agenda'))
                        with linha:
                            ui.label(f'{hora}{f" - {fim}" if fim else ""}').classes('dashboard-agenda-time shrink-0')
                            with ui.column().classes('gap-1 flex-1 min-w-0'):
                                with ui.row().classes('items-center gap-2 flex-wrap'):
                                    ui.label(_texto(item.get('tipo'), 'Atividade')).classes('app-pill text-xs font-black px-3 py-1')
                                    ui.label(status).classes(f'dashboard-agenda-status {_status_class(status)}')
                                ui.label(_texto(item.get('titulo'), 'Atividade')).classes('font-black leading-tight')
                                ui.label(f"{_texto(item.get('turma'), 'Geral')} · {_texto(item.get('aluno'), 'Geral')} · {_texto(item.get('responsavel'), 'Equipe')}").classes('app-muted text-xs font-bold')
                            ui.icon('arrow_forward', size='sm').classes('app-muted shrink-0')

                    if len(agenda_hoje) > 4:
                        with ui.row().classes('w-full justify-between items-center gap-3 pt-1'):
                            ui.label(f'Mais {len(agenda_hoje) - 4} atividade(s) planejada(s) para hoje.').classes('app-muted text-sm font-bold')
                            ui.button('Ver rotina completa', icon='open_in_new', on_click=lambda: ui.navigate.to('/agenda')).props('flat color=primary no-caps')

        with ui.column().classes('w-full gap-3'):
            ui.label('Resumo da escola').classes('text-xl font-black')
            ui.label('Números principais para leitura rápida da rotina.').classes('app-muted text-sm')

            with ui.row().classes('w-full gap-4 flex-wrap'):
                def resumo(titulo, valor, emoji, cor):
                    with ui.card().classes('app-card dashboard-summary p-3'):
                        with ui.column().classes('w-full h-full justify-between gap-2'):
                            ui.label(titulo).classes('summary-title')
                            with ui.row().classes('w-full items-end justify-between gap-2'):
                                ui.label(valor).classes('summary-number')
                                ui.label(emoji).classes(f'shortcut-icon {cor}')

                if pode_ver_alunos:
                    resumo('Alunos', str(total_alunos), '☀️', 'soft-blue')
                if pode_ver_agenda:
                    resumo('Agenda hoje', str(total_agenda_hoje), '🗓️', 'soft-amber')
                if pode_ver_turmas:
                    resumo('Turmas', str(total_turmas), '🏷️', 'soft-green')
                if pode_ver_pais:
                    resumo('Famílias', str(total_pais), '☎️', 'soft-teal')
                if pode_ver_registros:
                    resumo('Registros', str(total_registros), '📝', 'soft-coral')
                if pode_ver_alunos:
                    resumo('Atenção registrada', str(total_com_atencao), '💛', 'soft-amber')
                if pode_ver_estrategias:
                    resumo('Estratégias', str(total_estrategias), '💡', 'soft-violet')

        with ui.column().classes('w-full gap-3'):
            ui.label('Atalhos do sistema').classes('text-xl font-black')
            ui.label('Clique em um card para abrir a área correspondente.').classes('app-muted text-sm')

            with ui.grid(columns=1).classes('w-full gap-5 lg:grid-cols-2'):
                if pode_ver_pais:
                    with ui.card().classes('app-card w-full p-5'):
                        ui.label('☎️ Comunicação com famílias').classes('text-xl font-black mb-2')
                        ui.label('Mantenha contatos de pais e responsáveis sempre à mão para recados, combinados e acolhimento.').classes('app-muted text-sm leading-relaxed mb-4')
                        ui.button('Abrir página de pais', icon='contact_phone', on_click=lambda: ui.navigate.to('/pais')).props('unelevated color=secondary')

            with ui.grid(columns=1).classes('w-full gap-4 md:grid-cols-2 lg:grid-cols-3'):
                def atalho(titulo, descricao, valor, emoji, cor, rota):
                    card = ui.card().classes('app-card dashboard-shortcut w-full p-4')
                    card.on('click', lambda r=rota: ui.navigate.to(r))
                    with card:
                        with ui.column().classes('w-full h-full justify-between gap-4'):
                            with ui.row().classes('w-full items-center justify-between gap-3'):
                                ui.label(emoji).classes(f'shortcut-icon {cor}')
                                ui.label(valor).classes('shortcut-value')
                            with ui.column().classes('gap-1'):
                                ui.label(titulo).classes('text-lg font-black leading-tight')
                                ui.label(descricao).classes('app-muted text-xs leading-relaxed')
                            with ui.row().classes('w-full justify-end'):
                                ui.icon('arrow_forward', size='xs').classes('app-muted')

                if pode_ver_alunos:
                    atalho('Alunos', 'Cadastro e prontuários individuais.', str(total_alunos), '☀️', 'soft-blue', '/alunos')
                if pode_ver_agenda:
                    atalho('Agenda', 'Rotina visual e horários do dia.', str(total_agenda_hoje), '🗓️', 'soft-amber', '/agenda')
                if pode_ver_turmas:
                    atalho('Turmas', 'Período, professor, sala e alunos.', str(total_turmas), '🏷️', 'soft-green', '/turmas')
                if pode_ver_pais:
                    atalho('Famílias', 'Contatos rápidos dos responsáveis.', str(total_pais), '☎️', 'soft-teal', '/pais')
                if pode_ver_registros:
                    atalho('Registros', 'Diário de acompanhamento escolar.', str(total_registros), '📝', 'soft-coral', '/registros')
                if pode_ver_alunos:
                    atalho('Acompanhamento', 'Alunos com atenção registrada.', str(total_com_atencao), '💛', 'soft-amber', '/alunos')
                if pode_ver_impressao:
                    atalho('Impressão/PDF', 'Fichas prontas para reunião.', 'PDF', '🖨️', 'soft-blue', '/impressao')
                if pode_ver_estrategias:
                    atalho('Estratégias', 'Biblioteca de apoio pedagógico.', str(total_estrategias), '💡', 'soft-violet', '/estrategias')
                if pode_ver_admin:
                    atalho('Administração', 'Comunicados e registros internos.', 'Gestão', '📣', 'soft-green', '/admin')

        with ui.grid(columns=1).classes('w-full gap-5 lg:grid-cols-2'):
            if pode_ver_estrategias:
                with ui.card().classes('app-card w-full p-5'):
                    ui.label('💡 Estratégias pedagógicas').classes('text-xl font-black mb-2')
                    ui.label('Consulte orientações práticas para rotina, comunicação, sensibilidade sensorial e reforço positivo.').classes('app-muted text-sm leading-relaxed mb-4')
                    ui.button('Abrir estratégias', icon='auto_awesome', on_click=lambda: ui.navigate.to('/estrategias')).props('unelevated color=primary')
