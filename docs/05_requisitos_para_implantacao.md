# 5. Requisitos e decisões para implantação

## Ambiente recomendado

- [ ] VM Linux na OCI;
- [ ] arquitetura ARM64/AArch64, preferencialmente Ampere A1 no Always Free;
- [ ] Docker Engine instalado;
- [ ] Docker Compose Plugin instalado;
- [ ] armazenamento persistente para banco, PDFs, assinaturas e backups;
- [ ] VCN e subnet configuradas;
- [ ] Security List/NSG configurados;
- [ ] SSH restrito aos administradores autorizados;
- [ ] DNS definido;
- [ ] HTTPS/TLS configurado;
- [ ] Nginx ou reverse proxy configurado;
- [ ] porta 8501 não exposta publicamente.

## Aplicação

- [ ] imagem Docker construída com sucesso;
- [ ] container iniciado com `docker compose up -d`;
- [ ] logs sem erros críticos;
- [ ] resposta local em `127.0.0.1:8501`;
- [ ] banco em `data/avaliacao.db`;
- [ ] PDFs em `resumos/`;
- [ ] assinaturas em `assets/assinaturas/`;
- [ ] backup externo configurado.

## Autenticação

A versão entregue utiliza contas locais da plataforma. Não há SSO institucional implementado.

- [ ] senha inicial do master alterada;
- [ ] contas administrativas individuais definidas;
- [ ] política institucional para contas locais validada;
- [ ] eventual SSO/MFA institucional avaliado separadamente.

## Homologação

- [ ] login e logout;
- [ ] troca de senha;
- [ ] permissões dos perfis;
- [ ] cadastro/importação de trabalhos;
- [ ] upload de PDF;
- [ ] distribuição;
- [ ] avaliação;
- [ ] discrepâncias;
- [ ] resultados;
- [ ] certificados;
- [ ] backup;
- [ ] restauração;
- [ ] HTTPS;
- [ ] reinicialização da VM;
- [ ] recuperação automática do container.
