# 6. Checklist de entrega

## Arquivos entregues

- [x] código-fonte;
- [x] dependências;
- [x] Dockerfile;
- [x] docker-compose.yml;
- [x] recursos visuais;
- [x] modelos de certificado;
- [x] manuais de coordenação e avaliador;
- [x] manual técnico de implantação;
- [x] documentação de implantação Docker/OCI;
- [x] documentação de segurança;
- [x] documentação de backup e restauração;
- [x] checklist de implantação.

## Responsabilidades do responsável pela implantação antes da publicação

- [ ] criar/configurar a VM OCI;
- [ ] instalar Docker e Docker Compose;
- [ ] configurar armazenamento persistente;
- [ ] configurar VCN, NSG/Security List e firewall;
- [ ] restringir SSH;
- [ ] configurar DNS;
- [ ] configurar Nginx/reverse proxy;
- [ ] configurar HTTPS;
- [ ] garantir que 8501 não esteja pública;
- [ ] configurar backup externo;
- [ ] testar restauração;
- [ ] definir monitoramento e logs;
- [ ] validar política institucional de segurança;
- [ ] executar homologação funcional;
- [ ] definir procedimento de atualização e rollback;
- [ ] alterar a senha inicial do master.

## Observação

A versão entregue utiliza autenticação local da aplicação. SSO/MFA institucional não está implementado e, caso seja necessário, deverá ser tratado como integração adicional.
