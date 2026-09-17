# Backup e restauração - Docker

## O que deve ser preservado

```text
data/avaliacao.db
resumos/
assets/assinaturas/
backups/
```

O banco SQLite sozinho não contém os PDFs dos trabalhos nem as imagens das assinaturas.

## Backup operacional recomendado

Antes de atualização, migração ou reinicialização anual, preservar os diretórios persistentes.

Exemplo:

```bash
cd /opt/avaliacao-ufrr
sudo tar -czf /opt/backup/avaliacao-ufrr-$(date +%Y%m%d-%H%M%S).tar.gz data resumos assets/assinaturas backups
```

O diretório `/opt/backup` deve estar em armazenamento protegido e, idealmente, ser replicado para outro local.

## Restauração

1. parar o serviço;
2. preservar uma cópia do estado atual;
3. restaurar `data/`, `resumos/` e `assets/assinaturas/`;
4. iniciar o container;
5. verificar login, trabalhos, PDFs e certificados.

```bash
docker compose down
# restaurar os diretórios a partir do backup
docker compose up -d
```

## Reinicialização anual

A função de reinicialização da aplicação cria um backup do banco antes de limpar os dados. Isso não substitui o backup externo dos PDFs e assinaturas.
