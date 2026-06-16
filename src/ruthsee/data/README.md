# Dados locais

O arquivo principal do sistema agora e `ruthsee.db` (SQLite).

Os arquivos `.json` desta pasta ficaram apenas como dados legados/semente para a primeira migracao. Depois que `ruthsee.db` existe, o sistema passa a ler e salvar no banco.

Antes de apagar os JSONs, confirme que:

- o sistema abre normalmente;
- os alunos, pais, usuarios e registros aparecem no site;
- existe um backup recente baixado pelo painel de administracao.

Por seguranca, nao envie `ruthsee.db` para GitHub ou grupos de mensagem, pois ele contem dados escolares.
