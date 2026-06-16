import datetime
import json

from nicegui import app, ui

from database import get_database_path, load_data, save_data
from layout import frame
from permissions import PERMISSION_LABELS, ROLE_PERMISSIONS, has_permission, require_permission


BACKUP_DEFAULTS = {
    'agenda.json': [],
    'alunos.json': [],
    'turmas.json': [],
    'pais.json': [],
    'registros.json': [],
    'estrategias.json': [],
    'comunicados.json': [],
    'despesas.json': [],
    'usuarios.json': [],
    'config.json': {'modo_escuro': False},
}

BACKUP_INFO = [
    ('agenda.json', '🗓️ Agenda', 'Rotina diária, horários e responsáveis.'),
    ('alunos.json', '☀️ Alunos', 'Cadastros e observações importantes.'),
    ('turmas.json', '🏷️ Turmas', 'Organização de salas, períodos e professores.'),
    ('pais.json', '☎️ Famílias', 'Contatos dos responsáveis e canais de comunicação.'),
    ('registros.json', '📝 Registros', 'Acompanhamentos, ações e próximos passos.'),
    ('estrategias.json', '💡 Estratégias', 'Biblioteca pedagógica da equipe.'),
    ('comunicados.json', '📣 Comunicados', 'Avisos internos publicados pela gestão.'),
    ('despesas.json', '💰 Despesas', 'Controle financeiro simples da administração.'),
    ('usuarios.json', '👥 Usuários', 'Perfis e permissões do sistema.'),
    ('config.json', '⚙️ Configurações', 'Preferências gerais do sistema.'),
]


def _valor_filtro(valor, padrao='Todos'):
    if isinstance(valor, dict):
        return str(valor.get('label') or valor.get('value') or padrao)
    return str(valor or padrao)


def _opcoes_autores(items):
    autores = {item.get('autor', '').strip() for item in items if item.get('autor', '').strip()}
    return ['Todos'] + sorted(autores)


def _opcoes_datas(items):
    datas = {item.get('data', '').strip() for item in items if item.get('data', '').strip()}
    return ['Todas'] + sorted(datas, reverse=True)


def render():
    with frame('Administração do Sistema'):
        if not require_permission('view_admin'):
            return

        comunicados = load_data('comunicados.json', [])
        despesas = load_data('despesas.json', [])
        pode_comunicados = has_permission('manage_comunicados')
        pode_despesas = has_permission('manage_despesas')
        pode_backup = has_permission('manage_backup')
        pode_lgpd = has_permission('manage_lgpd')

        ui.add_css('''
            .admin-data-row {
                background: var(--app-surface-muted) !important;
                border-radius: 8px;
            }

            .admin-backup-note {
                border: 1px solid color-mix(in srgb, var(--app-amber) 28%, transparent);
            }

            .admin-security-card {
                background: var(--app-surface-muted) !important;
                border: 1px solid var(--app-border);
                border-radius: 8px;
            }
        ''')

        def baixar_backup_completo():
            if not pode_backup:
                ui.notify('Seu cargo não permite baixar backups.', type='warning')
                return

            agora = datetime.datetime.now()
            backup = {
                'sistema': 'Ruth See Escola',
                'tipo': 'backup-dados',
                'gerado_em': agora.strftime('%d/%m/%Y %H:%M'),
                'arquivos': {
                    filename: load_data(filename, default)
                    for filename, default in BACKUP_DEFAULTS.items()
                },
            }
            conteudo = json.dumps(backup, ensure_ascii=False, indent=4)
            nome_arquivo = f"ruth-see-backup-{agora.strftime('%Y-%m-%d-%H%M')}.json"
            ui.download.content(conteudo, nome_arquivo, 'application/json')

        async def restaurar_backup(event):
            if not pode_backup:
                ui.notify('Seu cargo não permite restaurar backups.', type='warning')
                return

            if not confirmar_restore.value:
                ui.notify('Marque a confirmação antes de restaurar um backup.', type='warning')
                return

            try:
                backup = await event.file.json()
            except Exception:
                ui.notify('Não consegui ler o arquivo. Envie um backup JSON válido.', type='negative')
                return

            arquivos = backup.get('arquivos') if isinstance(backup, dict) else None
            if not isinstance(arquivos, dict):
                ui.notify('Este arquivo não parece ser um backup da Ruth See Escola.', type='negative')
                return

            restaurados = []
            for filename, default in BACKUP_DEFAULTS.items():
                if filename not in arquivos:
                    continue

                conteudo = arquivos[filename]
                tipo_esperado = list if isinstance(default, list) else dict
                if not isinstance(conteudo, tipo_esperado):
                    ui.notify(f'O arquivo {filename} está em um formato inválido.', type='negative')
                    return
                restaurados.append((filename, conteudo))

            if not restaurados:
                ui.notify('O backup não contém arquivos reconhecidos para restaurar.', type='warning')
                return

            for filename, conteudo in restaurados:
                save_data(filename, conteudo)

            confirmar_restore.value = False
            confirmar_restore.update()
            restore_status.set_text(f'{len(restaurados)} arquivo(s) restaurado(s). A página será atualizada.')
            ui.notify('Backup restaurado com sucesso.', type='positive')
            ui.timer(1.0, lambda: ui.navigate.reload(), once=True)

        def salvar_comunicado():
            if not pode_comunicados:
                ui.notify('Seu cargo não permite publicar comunicados.', type='warning')
                return

            if not titulo_input.value or not mensagem_input.value:
                ui.notify('Preencha o título e a mensagem. 😊', type='warning')
                return

            novo_aviso = {
                'titulo': titulo_input.value.strip(),
                'mensagem': mensagem_input.value.strip(),
                'data': datetime.datetime.now().strftime('%d/%m/%Y'),
                'autor': app.storage.user.get('nome', 'Administração').split(' ')[0],
            }

            comunicados.append(novo_aviso)
            save_data('comunicados.json', comunicados)
            ui.notify('Comunicado publicado com sucesso! 📣', type='positive')

            titulo_input.value = ''
            mensagem_input.value = ''
            atualizar_opcoes_comunicados()
            atualizar_lista_comunicados()

        def confirmar_exclusao_comunicado(aviso):
            if not pode_comunicados:
                ui.notify('Seu cargo não permite excluir comunicados.', type='warning')
                return

            with ui.dialog() as confirm_dialog, ui.card().classes('app-card w-full max-w-md p-6'):
                ui.label('Excluir comunicado').classes('text-xl font-black text-red-600 mb-3')
                ui.label(f'Deseja apagar "{aviso["titulo"]}"?').classes('app-muted text-sm')
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Cancelar', on_click=confirm_dialog.close).props('flat')
                    ui.button('Excluir', icon='delete', on_click=lambda: apagar_comunicado(aviso, confirm_dialog)).props('unelevated color=red')
            confirm_dialog.open()

        def apagar_comunicado(aviso, confirm_dialog):
            comunicados.remove(aviso)
            save_data('comunicados.json', comunicados)
            ui.notify('Comunicado removido.', type='warning')
            confirm_dialog.close()
            atualizar_opcoes_comunicados()
            atualizar_lista_comunicados()

        def salvar_despesa():
            if not pode_despesas:
                ui.notify('Seu cargo não permite gerenciar despesas.', type='warning')
                return

            if not desc_despesa_input.value or not valor_despesa_input.value:
                ui.notify('Preencha a descrição e o valor.', type='warning')
                return

            try:
                valor_float = float(str(valor_despesa_input.value).replace(',', '.'))
            except ValueError:
                ui.notify('Digite um valor numérico válido.', type='warning')
                return

            nova_despesa = {
                'descricao': desc_despesa_input.value.strip(),
                'valor': valor_float,
                'data': datetime.datetime.now().strftime('%d/%m/%Y'),
                'autor': app.storage.user.get('nome', 'Administração').split(' ')[0],
            }

            despesas.append(nova_despesa)
            save_data('despesas.json', despesas)
            ui.notify('Despesa registrada com sucesso! 💰', type='positive')

            desc_despesa_input.value = ''
            valor_despesa_input.value = ''
            atualizar_opcoes_despesas()
            atualizar_lista_despesas()

        def confirmar_exclusao_despesa(despesa):
            if not pode_despesas:
                ui.notify('Seu cargo não permite excluir despesas.', type='warning')
                return

            with ui.dialog() as confirm_dialog, ui.card().classes('app-card w-full max-w-md p-6'):
                ui.label('Excluir despesa').classes('text-xl font-black text-red-600 mb-3')
                ui.label(f'Deseja apagar "{despesa["descricao"]}"?').classes('app-muted text-sm')
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Cancelar', on_click=confirm_dialog.close).props('flat')
                    ui.button('Excluir', icon='delete', on_click=lambda: apagar_despesa(despesa, confirm_dialog)).props('unelevated color=red')
            confirm_dialog.open()

        def apagar_despesa(despesa, confirm_dialog):
            despesas.remove(despesa)
            save_data('despesas.json', despesas)
            ui.notify('Despesa removida.', type='warning')
            confirm_dialog.close()
            atualizar_opcoes_despesas()
            atualizar_lista_despesas()

        with ui.column().classes('w-full gap-5'):
            with ui.row().classes('app-card-colorful w-full items-center justify-between gap-5 p-6'):
                with ui.column().classes('gap-2'):
                    ui.label('📣 Coordenação').classes('app-muted text-sm font-black uppercase')
                    ui.label('Avisos e organização da escola').classes('text-3xl font-black')
                    ui.label('Publique comunicados e acompanhe registros financeiros simples.').classes('app-muted text-sm')
                ui.label('🧭').classes('text-5xl')

            with ui.tabs().classes('w-full') as tabs:
                tab_comunicados = ui.tab('📣 Comunicados', icon='campaign')
                tab_despesas = ui.tab('💰 Despesas', icon='account_balance_wallet') if pode_despesas else None
                tab_backup = ui.tab('💾 Backup', icon='backup') if pode_backup else None
                tab_lgpd = ui.tab('🛡️ LGPD', icon='shield') if pode_lgpd else None

            with ui.tab_panels(tabs, value=tab_comunicados).classes('w-full bg-transparent p-0'):
                with ui.tab_panel(tab_comunicados).classes('p-0'):
                    with ui.card().classes('app-card w-full p-5 mb-5'):
                        ui.label('📌 Publicar novo comunicado').classes('text-xl font-black mb-4')
                        titulo_input = ui.input('Título do comunicado *').props('outlined').classes('w-full mb-4')
                        mensagem_input = ui.textarea('Mensagem *').props('outlined autogrow').classes('w-full mb-4')
                        with ui.row().classes('w-full justify-end'):
                            ui.button('Publicar comunicado ✨', icon='send', on_click=salvar_comunicado).props('unelevated color=primary')

                    ui.label('Comunicados ativos').classes('text-xl font-black mb-3')
                    with ui.row().classes('app-toolbar w-full justify-between items-center gap-4 p-4 mb-4'):
                        with ui.row().classes('flex-1 items-center gap-3 flex-wrap'):
                            busca_comunicado_input = ui.input(placeholder='Buscar por título, mensagem ou autor').props('outlined dense').classes('w-full md:max-w-md flex-1')
                            with busca_comunicado_input.add_slot('prepend'):
                                ui.icon('search').classes('app-muted')
                            autor_comunicado_filter = ui.select(_opcoes_autores(comunicados), value='Todos', label='Autor').props('outlined dense').classes('w-full sm:w-48')
                            data_comunicado_filter = ui.select(_opcoes_datas(comunicados), value='Todas', label='Data').props('outlined dense').classes('w-full sm:w-40')

                    container_comunicados = ui.column().classes('w-full gap-3')

                    def atualizar_opcoes_comunicados():
                        filtros = [
                            (autor_comunicado_filter, _opcoes_autores(comunicados), 'Todos'),
                            (data_comunicado_filter, _opcoes_datas(comunicados), 'Todas'),
                        ]
                        for filtro, opcoes, padrao in filtros:
                            valor_atual = _valor_filtro(filtro.value, padrao)
                            filtro.options = opcoes
                            filtro.value = valor_atual if valor_atual in opcoes else padrao
                            filtro.update()

                    def atualizar_lista_comunicados():
                        termo = (busca_comunicado_input.value or '').strip().lower()
                        autor_selecionado = _valor_filtro(autor_comunicado_filter.value)
                        data_selecionada = _valor_filtro(data_comunicado_filter.value, 'Todas')
                        filtrados = []

                        for comunicado in comunicados:
                            texto_busca = ' '.join([
                                comunicado.get('titulo', ''),
                                comunicado.get('mensagem', ''),
                                comunicado.get('autor', ''),
                                comunicado.get('data', ''),
                            ]).lower()
                            if termo and termo not in texto_busca:
                                continue
                            if autor_selecionado != 'Todos' and comunicado.get('autor') != autor_selecionado:
                                continue
                            if data_selecionada != 'Todas' and comunicado.get('data') != data_selecionada:
                                continue
                            filtrados.append(comunicado)

                        container_comunicados.clear()
                        with container_comunicados:
                            if not filtrados:
                                with ui.column().classes('app-card w-full items-center justify-center gap-3 py-12 text-center'):
                                    ui.label('📭').classes('text-5xl')
                                    ui.label('Nenhum comunicado encontrado').classes('text-xl font-black')
                                    ui.label('Ajuste os filtros ou publique um novo aviso.').classes('app-muted text-sm')

                            for comunicado in reversed(filtrados):
                                with ui.card().classes('app-card w-full p-4'):
                                    with ui.row().classes('w-full justify-between items-start gap-4'):
                                        with ui.column().classes('gap-1 flex-1'):
                                            ui.label(comunicado.get('titulo', '')).classes('font-black text-lg')
                                            ui.label(f"Publicado em {comunicado.get('data', '')} por {comunicado.get('autor', '')}").classes('app-muted text-xs font-bold')
                                            ui.label(comunicado.get('mensagem', '')).classes('app-muted text-sm leading-relaxed mt-2')
                                        ui.button(icon='delete', on_click=lambda c=comunicado: confirmar_exclusao_comunicado(c)).props('flat color=red round size=sm').tooltip('Remover')

                    busca_comunicado_input.on_value_change(lambda _: atualizar_lista_comunicados())
                    autor_comunicado_filter.on_value_change(lambda _: atualizar_lista_comunicados())
                    data_comunicado_filter.on_value_change(lambda _: atualizar_lista_comunicados())
                    atualizar_lista_comunicados()

                if tab_despesas:
                    with ui.tab_panel(tab_despesas).classes('p-0'):
                        with ui.card().classes('app-card w-full p-5 mb-5'):
                            ui.label('💰 Registrar nova despesa').classes('text-xl font-black mb-4')
                            with ui.grid(columns=2).classes('w-full gap-4'):
                                desc_despesa_input = ui.input('Descrição da despesa *').props('outlined').classes('w-full')
                                valor_despesa_input = ui.input('Valor (R$) *').props('outlined type=number step=0.01').classes('w-full')
                            with ui.row().classes('w-full justify-end mt-4'):
                                ui.button('Registrar despesa ✨', icon='add_circle', on_click=salvar_despesa).props('unelevated color=positive')

                        ui.label('Histórico de despesas').classes('text-xl font-black mb-3')
                        with ui.row().classes('app-toolbar w-full justify-between items-center gap-4 p-4 mb-4'):
                            with ui.row().classes('flex-1 items-center gap-3 flex-wrap'):
                                busca_despesa_input = ui.input(placeholder='Buscar por descrição, autor ou data').props('outlined dense').classes('w-full md:max-w-md flex-1')
                                with busca_despesa_input.add_slot('prepend'):
                                    ui.icon('search').classes('app-muted')
                                autor_despesa_filter = ui.select(_opcoes_autores(despesas), value='Todos', label='Autor').props('outlined dense').classes('w-full sm:w-48')
                                data_despesa_filter = ui.select(_opcoes_datas(despesas), value='Todas', label='Data').props('outlined dense').classes('w-full sm:w-40')
                                valor_despesa_filter = ui.select(['Todos', 'Até R$ 100', 'Acima de R$ 100', 'Acima de R$ 500'], value='Todos', label='Valor').props('outlined dense').classes('w-full sm:w-44')

                        container_despesas = ui.column().classes('w-full gap-3')

                        def atualizar_opcoes_despesas():
                            filtros = [
                                (autor_despesa_filter, _opcoes_autores(despesas), 'Todos'),
                                (data_despesa_filter, _opcoes_datas(despesas), 'Todas'),
                            ]
                            for filtro, opcoes, padrao in filtros:
                                valor_atual = _valor_filtro(filtro.value, padrao)
                                filtro.options = opcoes
                                filtro.value = valor_atual if valor_atual in opcoes else padrao
                                filtro.update()

                        def atualizar_lista_despesas():
                            termo = (busca_despesa_input.value or '').strip().lower()
                            autor_selecionado = _valor_filtro(autor_despesa_filter.value)
                            data_selecionada = _valor_filtro(data_despesa_filter.value, 'Todas')
                            valor_selecionado = _valor_filtro(valor_despesa_filter.value)
                            filtradas = []

                            for despesa in despesas:
                                texto_busca = ' '.join([
                                    despesa.get('descricao', ''),
                                    despesa.get('autor', ''),
                                    despesa.get('data', ''),
                                ]).lower()
                                valor = float(despesa.get('valor', 0) or 0)

                                if termo and termo not in texto_busca:
                                    continue
                                if autor_selecionado != 'Todos' and despesa.get('autor') != autor_selecionado:
                                    continue
                                if data_selecionada != 'Todas' and despesa.get('data') != data_selecionada:
                                    continue
                                if valor_selecionado == 'Até R$ 100' and valor > 100:
                                    continue
                                if valor_selecionado == 'Acima de R$ 100' and valor <= 100:
                                    continue
                                if valor_selecionado == 'Acima de R$ 500' and valor <= 500:
                                    continue
                                filtradas.append(despesa)

                            container_despesas.clear()
                            with container_despesas:
                                if not filtradas:
                                    with ui.column().classes('app-card w-full items-center justify-center gap-3 py-12 text-center'):
                                        ui.label('🧾').classes('text-5xl')
                                        ui.label('Nenhuma despesa encontrada').classes('text-xl font-black')
                                        ui.label('Ajuste os filtros ou registre uma nova despesa.').classes('app-muted text-sm')

                                for despesa in reversed(filtradas):
                                    valor_formatado = f"R$ {float(despesa.get('valor', 0)):.2f}".replace('.', ',')
                                    with ui.card().classes('app-card w-full p-4 flex-row justify-between items-center'):
                                        with ui.column().classes('gap-0'):
                                            ui.label(despesa.get('descricao', '')).classes('font-black text-lg')
                                            ui.label(f"Registrado em {despesa.get('data', '')} por {despesa.get('autor', '')}").classes('app-muted text-xs font-bold')

                                        with ui.row().classes('items-center gap-4'):
                                            ui.label(valor_formatado).classes('text-xl font-black tone-green')
                                            ui.button(icon='delete', on_click=lambda d=despesa: confirmar_exclusao_despesa(d)).props('flat color=red round size=sm').tooltip('Remover')

                        busca_despesa_input.on_value_change(lambda _: atualizar_lista_despesas())
                        autor_despesa_filter.on_value_change(lambda _: atualizar_lista_despesas())
                        data_despesa_filter.on_value_change(lambda _: atualizar_lista_despesas())
                        valor_despesa_filter.on_value_change(lambda _: atualizar_lista_despesas())
                        atualizar_lista_despesas()

                if tab_backup:
                    with ui.tab_panel(tab_backup).classes('p-0'):
                        with ui.grid(columns=1).classes('w-full gap-5 lg:grid-cols-3'):
                            with ui.card().classes('app-card w-full p-5 lg:col-span-2'):
                                with ui.row().classes('w-full items-start justify-between gap-4 mb-4'):
                                    with ui.column().classes('gap-1'):
                                        ui.label('💾 Segurança dos dados').classes('text-xl font-black')
                                        ui.label('Guarde uma cópia exportada do banco local da escola.').classes('app-muted text-sm')
                                    ui.button('Baixar backup completo', icon='download', on_click=baixar_backup_completo).props('unelevated color=primary')

                                with ui.column().classes('w-full gap-2'):
                                    ui.label(f'Banco ativo: {get_database_path().name}').classes('app-muted text-xs font-bold mb-2')
                                    for filename, titulo, descricao in BACKUP_INFO:
                                        dados = load_data(filename, BACKUP_DEFAULTS[filename])
                                        quantidade = len(dados) if isinstance(dados, list) else len(dados.keys())
                                        with ui.row().classes('admin-data-row w-full items-center justify-between gap-3 p-3'):
                                            with ui.column().classes('gap-0 min-w-0'):
                                                ui.label(titulo).classes('font-black')
                                                ui.label(descricao).classes('app-muted text-xs leading-relaxed')
                                            with ui.column().classes('items-end gap-0 shrink-0'):
                                                ui.label(filename).classes('app-muted text-[10px] font-bold uppercase')
                                                ui.label(str(quantidade)).classes('text-lg font-black')

                            with ui.card().classes('app-card w-full p-5'):
                                ui.label('Restaurar backup').classes('text-xl font-black mb-2')
                                ui.label('Use apenas arquivos baixados por este sistema. A restauração substitui os dados atuais.').classes('app-muted text-sm leading-relaxed mb-4')
                                confirmar_restore = ui.checkbox('Confirmo que quero substituir os dados atuais').classes('mb-3')
                                restore_status = ui.label('').classes('app-muted text-xs font-bold mb-3')
                                ui.upload(
                                    label='Selecionar backup JSON',
                                    on_upload=restaurar_backup,
                                    auto_upload=True,
                                    max_file_size=5 * 1024 * 1024,
                                ).props('accept=.json color=primary').classes('w-full')

                                with ui.column().classes('admin-backup-note soft-amber w-full gap-1 p-3 rounded-lg mt-4'):
                                    ui.label('✨ Dica prática').classes('font-black text-sm')
                                    ui.label('Baixe um backup antes de grandes alterações, apresentações ou troca de computador.').classes('app-muted text-xs leading-relaxed')

                if tab_lgpd:
                    with ui.tab_panel(tab_lgpd).classes('p-0'):
                        with ui.column().classes('w-full gap-5'):
                            with ui.grid(columns=1).classes('w-full gap-5 lg:grid-cols-3'):
                                with ui.card().classes('app-card w-full p-5 lg:col-span-2'):
                                    ui.label('🛡️ LGPD e segurança interna').classes('text-xl font-black mb-2')
                                    ui.label('Base prática para trabalhar com dados sensíveis de alunos, responsáveis e equipe escolar.').classes('app-muted text-sm leading-relaxed mb-4')
                                    controles = [
                                        ('Acesso mínimo por cargo', 'Cada perfil enxerga apenas as páginas e ações compatíveis com sua função.'),
                                        ('Login sem prévia de perfil', 'O sistema não mostra foto, nome ou cargo antes da senha ser confirmada.'),
                                        ('Senhas protegidas', 'Novas senhas são salvas com hash; senhas antigas são migradas no próximo login.'),
                                        ('Famílias vinculadas ao aluno', 'Ao excluir um aluno, contatos familiares vinculados também são removidos.'),
                                        ('Backups restritos', 'Download e restauração ficam disponíveis apenas para administração autorizada.'),
                                        ('Administrador padrão', 'Troque a senha padrão por variável de ambiente antes de usar o sistema em rede.'),
                                    ]
                                    with ui.grid(columns=1).classes('w-full gap-3 md:grid-cols-2'):
                                        for titulo, descricao in controles:
                                            with ui.column().classes('admin-security-card gap-1 p-4'):
                                                ui.label(titulo).classes('font-black')
                                                ui.label(descricao).classes('app-muted text-xs leading-relaxed')

                                with ui.card().classes('app-card w-full p-5'):
                                    ui.label('Conduta da equipe').classes('text-xl font-black mb-2')
                                    ui.label('Use os dados somente para acompanhamento pedagógico, comunicação escolar e segurança da rotina. Não compartilhe fichas, telefones, diagnósticos ou registros fora dos canais autorizados pela escola.').classes('app-muted text-sm leading-relaxed')

                            with ui.card().classes('app-card w-full p-5'):
                                ui.label('🔐 Matriz de permissões').classes('text-xl font-black mb-1')
                                ui.label('Resumo do que cada cargo consegue visualizar ou gerenciar no sistema.').classes('app-muted text-sm mb-4')
                                with ui.grid(columns=1).classes('w-full gap-3 lg:grid-cols-4'):
                                    for cargo, permissoes in ROLE_PERMISSIONS.items():
                                        with ui.column().classes('admin-security-card w-full gap-2 p-4'):
                                            ui.label(cargo).classes('font-black')
                                            ui.label(f'{len(permissoes)} permissões ativas').classes('app-muted text-xs font-bold uppercase')
                                            with ui.row().classes('gap-1 flex-wrap'):
                                                for permissao, label in PERMISSION_LABELS.items():
                                                    if permissao in permissoes:
                                                        ui.label(label).classes('app-pill text-[10px] font-bold px-2 py-1')

                            with ui.card().classes('app-card w-full p-5'):
                                ui.label('Aviso interno de privacidade').classes('text-xl font-black mb-2')
                                ui.label('Este sistema foi organizado para uma escola de pequeno porte, com dados armazenados localmente em banco SQLite. A escola deve manter responsáveis informados sobre o uso pedagógico dos dados, limitar acessos, revisar backups e excluir informações que não forem mais necessárias.').classes('app-muted text-sm leading-relaxed')
                                ui.label('Esta tela apoia a adequação operacional à LGPD, mas não substitui uma revisão jurídica formal da instituição.').classes('app-muted text-xs font-bold mt-3')
