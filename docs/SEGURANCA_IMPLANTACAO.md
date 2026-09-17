# Segurança - Implantação

## Escopo

A plataforma possui controles de segurança no nível da aplicação, mas não foi submetida a pentest, auditoria formal ou certificação de segurança.

## Controles presentes na aplicação

* autenticação local;
* perfis de acesso (master, coordenação e avaliador);
* controle de acesso às funcionalidades por perfil;
* senhas novas armazenadas com PBKDF2-HMAC-SHA256 e salt aleatório;
* troca obrigatória da senha inicial quando aplicável;
* consultas parametrizadas ao SQLite;
* SQLite não publicado diretamente para a Internet;
* registros de auditoria administrativos;
* mecanismo de backup e restauração;
* proteção adicional para a operação de reinicialização, exclusiva do master e protegida por senha.

## Controles de infraestrutura esperados

Esses controles podem ser configurados pelo terceiro responsável pela implantação. Quando algum requisito depender de política, credencial, domínio, certificado ou serviço institucional da UFRR, o responsável deverá alinhar essa etapa com a UFRR/TI.

A responsável pela implantação deve configurar e validar:

* HTTPS/TLS;
* firewall/NSG/Security List;
* SSH restrito;
* MFA para contas administrativas do OCI;
* atualizações de segurança do Ubuntu e Docker;
* execução do container sem root;
* porta 8501 não exposta publicamente;
* backups externos;
* monitoramento e logs;
* gestão de certificados;
* controle de acesso administrativo;
* procedimento de resposta e recuperação.

## Validação recomendada antes da produção

1. validar portas expostas externamente;
2. verificar que 8501 não é acessível diretamente da Internet;
3. testar HTTPS;
4. testar perfis e permissões;
5. testar recuperação de backup;
6. verificar logs;
7. verificar atualização do container;
8. realizar avaliação de segurança/pentest conforme a política institucional.

