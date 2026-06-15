import uuid


def normalizar(valor):
    return str(valor or '').strip().lower()


def garantir_ids_alunos(alunos):
    alterado = False
    usados = {str(aluno.get('id', '')).strip() for aluno in alunos if aluno.get('id')}

    for aluno in alunos:
        if aluno.get('id'):
            continue

        novo_id = uuid.uuid4().hex[:12]
        while novo_id in usados:
            novo_id = uuid.uuid4().hex[:12]
        aluno['id'] = novo_id
        usados.add(novo_id)
        alterado = True

    return alterado


def rotulo_aluno(aluno):
    nome = str(aluno.get('nome') or 'Aluno').strip()
    turma = str(aluno.get('turma') or '').strip()
    return f'{nome} • {turma}' if turma else nome


def opcoes_alunos(alunos):
    return {
        aluno.get('id'): rotulo_aluno(aluno)
        for aluno in alunos
        if aluno.get('id') and str(aluno.get('nome') or '').strip()
    }


def aluno_por_id(alunos, aluno_id):
    for aluno in alunos:
        if aluno.get('id') == aluno_id:
            return aluno
    return None


def primeiro_aluno_por_nome(alunos, nome):
    nome_normalizado = normalizar(nome)
    for aluno in alunos:
        if normalizar(aluno.get('nome')) == nome_normalizado:
            return aluno
    return None


def id_aluno_por_nome(alunos, nome):
    aluno = primeiro_aluno_por_nome(alunos, nome)
    return aluno.get('id') if aluno else ''


def nome_aluno_vinculado(alunos, item):
    aluno = aluno_por_id(alunos, item.get('aluno_id'))
    if aluno:
        return str(aluno.get('nome') or item.get('aluno') or '').strip()
    return str(item.get('aluno') or '').strip()


def item_vinculado_ao_aluno(item, aluno):
    aluno_id = aluno.get('id')
    if aluno_id and item.get('aluno_id') == aluno_id:
        return True

    if item.get('aluno_id'):
        return False

    return normalizar(item.get('aluno')) == normalizar(aluno.get('nome'))
