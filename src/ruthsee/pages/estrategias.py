from nicegui import ui

from database import load_data, save_data
from layout import frame
from permissions import has_permission, require_permission


def _valor_filtro(valor, padrao='Todos'):
    if isinstance(valor, dict):
        return str(valor.get('label') or valor.get('value') or padrao)
    return str(valor or padrao)


def render():
    with frame('Biblioteca de Estratégias'):
        if not require_permission('view_estrategias'):
            return

        estrategias = load_data('estrategias.json', [])
        pode_gerir = has_permission('manage_estrategias')

        categorias = [
            '💬 Comunicação',
            '🗓️ Rotina',
            '🌦️ Manejo de crises',
            '🎧 Sensibilidade sensorial',
            '🤝 Inclusão escolar',
            '🧑‍🤝‍🧑 Interação social',
            '📚 Atividades pedagógicas',
            '⭐ Reforço positivo',
        ]

        editing_index = {'value': -1}

        def normalizar_categoria(categoria):
            if categoria in categorias:
                return categoria
            sem_emoji = {
                'Comunicação': '💬 Comunicação',
                'Rotina': '🗓️ Rotina',
                'Manejo de crises': '🌦️ Manejo de crises',
                'Sensibilidade': '🎧 Sensibilidade sensorial',
                'Sensibilidade sensorial': '🎧 Sensibilidade sensorial',
                'Inclusão escolar': '🤝 Inclusão escolar',
                'Interação social': '🧑‍🤝‍🧑 Interação social',
                'Atividades pedagógicas': '📚 Atividades pedagógicas',
                'Reforço positivo': '⭐ Reforço positivo',
            }
            return sem_emoji.get(categoria, categorias[0])

        def get_categoria_filter_options():
            return ['Todas'] + categorias

        def get_detalhe_options():
            return ['Todos', 'Com detalhes', 'Sem detalhes']

        def estrategia_tem_detalhes(estrategia):
            return bool(
                (estrategia.get('quando_usar') or '').strip()
                or (estrategia.get('quando_evitar') or '').strip()
                or (estrategia.get('observacoes') or '').strip()
            )

        def abrir_modal(estrategia=None, index=-1):
            if not pode_gerir:
                ui.notify('Seu cargo não permite alterar estratégias.', type='warning')
                return
            editing_index['value'] = index
            if estrategia:
                titulo_input.value = estrategia.get('titulo', '')
                categoria_input.value = normalizar_categoria(estrategia.get('categoria', categorias[0]))
                conteudo_input.value = estrategia.get('conteudo', '')
                quando_usar_input.value = estrategia.get('quando_usar', '')
                quando_evitar_input.value = estrategia.get('quando_evitar', '')
                obs_input.value = estrategia.get('observacoes', '')
                dialog_title.set_text('Editar estratégia 💡')
            else:
                titulo_input.value = ''
                categoria_input.value = categorias[0]
                conteudo_input.value = ''
                quando_usar_input.value = ''
                quando_evitar_input.value = ''
                obs_input.value = ''
                dialog_title.set_text('Nova estratégia ✨')
            dialog.open()

        def salvar_estrategia():
            if not pode_gerir:
                ui.notify('Seu cargo não permite salvar estratégias.', type='warning')
                return
            if not titulo_input.value:
                ui.notify('O título é obrigatório. 😊', type='warning')
                return

            dados = {
                'titulo': titulo_input.value.strip(),
                'categoria': categoria_input.value,
                'conteudo': (conteudo_input.value or '').strip(),
                'quando_usar': (quando_usar_input.value or '').strip(),
                'quando_evitar': (quando_evitar_input.value or '').strip(),
                'observacoes': (obs_input.value or '').strip(),
            }

            if editing_index['value'] >= 0:
                estrategias[editing_index['value']] = dados
                ui.notify('Estratégia atualizada com sucesso! ⭐', type='positive')
            else:
                estrategias.append(dados)
                ui.notify('Estratégia cadastrada com sucesso! ⭐', type='positive')

            save_data('estrategias.json', estrategias)
            dialog.close()
            atualizar_lista()

        def confirmar_exclusao(estrategia):
            if not pode_gerir:
                ui.notify('Seu cargo não permite excluir estratégias.', type='warning')
                return
            with ui.dialog() as confirm_dialog, ui.card().classes('app-card w-full max-w-md p-6'):
                ui.label('Excluir estratégia').classes('text-xl font-black text-red-600 mb-3')
                ui.label(f'Deseja apagar "{estrategia["titulo"]}"?').classes('app-muted text-sm')
                ui.label('Essa ação não pode ser desfeita.').classes('app-muted text-xs mb-4')
                with ui.row().classes('w-full justify-end gap-2'):
                    ui.button('Cancelar', on_click=confirm_dialog.close).props('flat')
                    ui.button('Excluir', icon='delete', on_click=lambda: apagar_estrategia(estrategia, confirm_dialog)).props('unelevated color=red')
            confirm_dialog.open()

        def apagar_estrategia(estrategia, confirm_dialog):
            estrategias.remove(estrategia)
            save_data('estrategias.json', estrategias)
            ui.notify('Estratégia removida.', type='warning')
            confirm_dialog.close()
            atualizar_lista()

        with ui.dialog() as dialog, ui.card().classes('app-card w-full max-w-4xl p-0 overflow-hidden'):
            with ui.row().classes('w-full items-center justify-between gap-4 p-6 soft-violet'):
                dialog_title = ui.label('Nova estratégia ✨').classes('text-2xl font-black')
                ui.button(icon='close', on_click=dialog.close).props('flat round').classes('app-muted')

            with ui.scroll_area().classes('w-full max-h-[68vh]'):
                with ui.column().classes('w-full gap-4 p-6'):
                    with ui.grid(columns=2).classes('w-full gap-4'):
                        titulo_input = ui.input('Título *').props('outlined').classes('col-span-2 md:col-span-1')
                        categoria_input = ui.select(categorias, label='Categoria').props('outlined').classes('w-full')

                    conteudo_input = ui.textarea('Como aplicar a estratégia').props('outlined autogrow').classes('w-full')
                    with ui.grid(columns=2).classes('w-full gap-4'):
                        quando_usar_input = ui.textarea('Quando utilizar').props('outlined autogrow').classes('w-full')
                        quando_evitar_input = ui.textarea('Quando evitar').props('outlined autogrow').classes('w-full')
                    obs_input = ui.textarea('Observações adicionais').props('outlined autogrow').classes('w-full')

            with ui.row().classes('w-full justify-end gap-3 p-6 soft-blue'):
                ui.button('Cancelar', on_click=dialog.close).props('flat')
                ui.button('Salvar estratégia', icon='check', on_click=salvar_estrategia).props('unelevated color=primary')

        with ui.column().classes('w-full gap-5'):
            with ui.row().classes('app-card-colorful w-full items-center justify-between gap-5 p-6'):
                with ui.column().classes('gap-2'):
                    ui.label('💡 Biblioteca viva').classes('app-muted text-sm font-black uppercase')
                    ui.label('Estratégias para acolher, comunicar e ensinar').classes('text-3xl font-black leading-tight')
                    ui.label('Ideias práticas para ajudar a equipe a responder com mais segurança e carinho.').classes('app-muted text-sm')
                if pode_gerir:
                    ui.button('Nova estratégia ✨', icon='add', on_click=lambda: abrir_modal()).props('unelevated color=primary')

            with ui.row().classes('app-toolbar w-full items-center justify-between gap-4 p-4'):
                with ui.row().classes('flex-1 items-center gap-3 flex-wrap'):
                    busca_input = ui.input(placeholder='Buscar por título, categoria ou conteúdo').props('outlined dense').classes('w-full md:max-w-md flex-1')
                    with busca_input.add_slot('prepend'):
                        ui.icon('search').classes('app-muted')
                    categoria_filter = ui.select(get_categoria_filter_options(), value='Todas', label='Categoria').props('outlined dense').classes('w-full sm:w-56')
                    detalhe_filter = ui.select(get_detalhe_options(), value='Todos', label='Detalhes').props('outlined dense').classes('w-full sm:w-44')
            container_lista = ui.grid(columns=1).classes('w-full gap-5 md:grid-cols-2 xl:grid-cols-3')

        def atualizar_lista():
            container_lista.clear()
            termo = (busca_input.value or '').strip().lower()
            categoria_selecionada = _valor_filtro(categoria_filter.value, 'Todas')
            detalhe_selecionado = _valor_filtro(detalhe_filter.value)
            filtradas = []

            for index, estrategia in enumerate(estrategias):
                texto_busca = ' '.join([
                    estrategia.get('titulo', ''),
                    estrategia.get('categoria', ''),
                    estrategia.get('conteudo', ''),
                    estrategia.get('quando_usar', ''),
                ]).lower()
                if termo and termo not in texto_busca:
                    continue
                if categoria_selecionada != 'Todas' and normalizar_categoria(estrategia.get('categoria', '')) != categoria_selecionada:
                    continue

                tem_detalhes = estrategia_tem_detalhes(estrategia)
                if detalhe_selecionado == 'Com detalhes' and not tem_detalhes:
                    continue
                if detalhe_selecionado == 'Sem detalhes' and tem_detalhes:
                    continue
                filtradas.append((index, estrategia))

            with container_lista:
                for index, estrategia in filtradas:
                    conteudo = estrategia.get('conteudo', '') or 'Sem descrição cadastrada.'
                    if len(conteudo) > 140:
                        conteudo = conteudo[:140] + '...'

                    with ui.card().classes('app-card w-full p-5 flex flex-col h-full'):
                        with ui.row().classes('w-full justify-between items-start gap-3 mb-3'):
                            ui.label(normalizar_categoria(estrategia.get('categoria', 'Geral'))).classes('student-pill text-xs font-black px-3 py-1')
                            if pode_gerir:
                                with ui.row().classes('gap-1'):
                                    ui.button(icon='edit', on_click=lambda i=index, est=estrategia: abrir_modal(est, i)).props('flat color=primary size=sm round padding=xs').tooltip('Editar')
                                    ui.button(icon='delete', on_click=lambda est=estrategia: confirmar_exclusao(est)).props('flat color=red size=sm round padding=xs').tooltip('Remover')

                        ui.label(estrategia.get('titulo', 'Sem título')).classes('text-xl font-black mb-2 line-clamp-2')
                        ui.label(conteudo).classes('app-muted text-sm leading-relaxed flex-grow mb-4')

                        with ui.expansion('✨ Ver detalhes', icon='info').classes('w-full text-sm'):
                            ui.label('✅ Quando utilizar').classes('font-black tone-green mt-2')
                            ui.label(estrategia.get('quando_usar', '-') or '-').classes('app-muted mb-2')
                            ui.label('🛑 Quando evitar').classes('font-black text-red-600')
                            ui.label(estrategia.get('quando_evitar', '-') or '-').classes('app-muted mb-2')
                            if estrategia.get('observacoes'):
                                ui.label('📝 Observações').classes('font-black tone-blue')
                                ui.label(estrategia.get('observacoes')).classes('app-muted mb-2')

                if not filtradas:
                    with ui.column().classes('app-card col-span-full items-center justify-center gap-3 py-16 text-center'):
                        ui.label('🔎').classes('text-5xl')
                        ui.label('Nenhuma estratégia encontrada').classes('text-xl font-black')
                        ui.label('Tente outra busca ou cadastre uma nova ideia.').classes('app-muted text-sm')
                        if pode_gerir:
                            ui.button('Nova estratégia ✨', icon='add', on_click=lambda: abrir_modal()).props('unelevated color=primary')

        busca_input.on_value_change(lambda _: atualizar_lista())
        categoria_filter.on_value_change(lambda _: atualizar_lista())
        detalhe_filter.on_value_change(lambda _: atualizar_lista())
        atualizar_lista()
