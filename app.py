import streamlit as st
import sqlite3, hashlib, secrets, io, base64, hmac, shutil, os
from pathlib import Path
from datetime import datetime
import unicodedata
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title='Avaliação de Resumos - UFRR', page_icon='🎓', layout='wide')

st.markdown("""
<style>
:root { --navy:#0b3b60; --blue:#1268b3; --pale:#eef6fc; --line:#d9e5ef; --text:#17324d; --muted:#6b7f92; --green:#18a66a; --orange:#f5a623; }
.stApp { background:linear-gradient(135deg,#f4f8fb 0%,#edf4f9 100%); color:var(--text); }
[data-testid="stHeader"] { background:transparent; }
.block-container { padding:1.1rem 1.6rem 2rem; max-width:1550px; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#ffffff 0%,#edf5fa 100%); border-right:1px solid var(--line); }
[data-testid="stSidebar"] .stRadio label { padding:9px 12px; border-radius:8px; }
[data-testid="stSidebar"] .stRadio label:hover { background:#e1effb; }
h1,h2,h3 { color:var(--navy)!important; letter-spacing:-.3px; }
h1 { font-size:2rem!important; }
h2 { font-size:1.35rem!important; }
h3 { font-size:1.08rem!important; }
.topbar { background:rgba(255,255,255,.96); border:1px solid var(--line); border-radius:12px; padding:9px 18px; margin-bottom:20px; box-shadow:0 4px 16px rgba(11,59,96,.07); }
.brand-title { font-size:20px; font-weight:800; color:var(--navy); margin-top:5px; }
.brand-sub { font-size:12px; color:var(--muted); }
.section-title { font-size:18px; font-weight:800; color:var(--navy); margin:18px 0 9px; }
.kpi { background:white; border:1px solid var(--line); border-radius:12px; padding:15px 17px; min-height:105px; box-shadow:0 3px 12px rgba(11,59,96,.045); }
.kpi-label { color:#60758a; font-size:12px; font-weight:600; }
.kpi-value { color:var(--navy); font-size:29px; font-weight:800; line-height:1.3; }
.kpi-note { color:#7b8d9e; font-size:11px; }
.panel { background:white; border:1px solid var(--line); border-radius:12px; padding:15px 17px; box-shadow:0 3px 12px rgba(11,59,96,.04); }
.badge { display:inline-block; padding:4px 9px; border-radius:20px; font-size:11px; font-weight:700; }
.badge-blue { background:#e3f0ff; color:#1268b3; }
.badge-green { background:#e0f7ec; color:#118451; }
.badge-orange { background:#fff1d8; color:#ad6a00; }
.badge-gray { background:#edf1f5; color:#60758a; }
.login-card { background:rgba(255,255,255,.97); border:1px solid #d9e5ef; border-radius:14px; padding:24px 28px; box-shadow:0 8px 30px rgba(11,59,96,.12); }
div[data-testid="stMetric"] { background:white; border:1px solid var(--line); padding:10px 14px; border-radius:10px; }
.stButton>button[kind="primary"] { background:#0756a0; border-radius:8px; font-weight:700; }
.stDownloadButton>button { border-radius:8px; }

/* Refinamento visual v17 */
[data-testid="stSidebar"] { padding-top: 0.8rem; }
[data-testid="stSidebar"] > div:first-child { padding-top: 0.5rem; }
[data-testid="stSidebar"] .stRadio > div { gap: 5px; }
[data-testid="stSidebar"] .stRadio label { border:1px solid transparent; transition:all .15s ease; font-weight:600; color:#294b66; }
[data-testid="stSidebar"] .stRadio label[data-checked="true"] { background:#dcecf9; border-color:#b7d4ec; color:#0756a0; }
[data-testid="stSidebar"] hr { border-color:#d9e5ef; }
[data-testid="stDataFrame"] { border:1px solid #d9e5ef; border-radius:12px; overflow:hidden; }
[data-testid="stExpander"] { border:1px solid #d9e5ef; border-radius:12px; background:#fff; }
div[data-testid="stForm"] { background:#fff; border:1px solid #d9e5ef; border-radius:12px; padding:16px; }
.stTextInput input, .stTextArea textarea, .stNumberInput input, .stSelectbox div[data-baseweb="select"] { border-radius:8px; }
.stButton button, .stDownloadButton button { min-height:40px; }
.page-intro { background:linear-gradient(90deg,#ffffff 0%,#f4f9fd 100%); border-left:5px solid #1268b3; border-radius:10px; padding:14px 18px; margin:0 0 18px; }
.page-intro-title { color:#0b3b60; font-size:24px; font-weight:800; margin:0; }
.page-intro-text { color:#60758a; font-size:13px; margin-top:4px; }
.app-footer { margin-top:34px; padding:14px 8px 4px; border-top:1px solid #d9e5ef; text-align:center; color:#6b7f92; font-size:11px; line-height:1.55; }
.app-footer strong { color:#526b80; }

</style>
""", unsafe_allow_html=True)
BASE = Path(__file__).parent
DATA_DIR = BASE/'data'
DB = DATA_DIR/'avaliacao.db'
PDF_DIR = BASE/'resumos'
BACKUP_DIR = BASE/'backups'
SIGN_DIR = BASE/'assets'/'assinaturas'
TEMPLATE_BASE = BASE/'assets'/'certificado.pdf'
TEMPLATE_PREMIO = TEMPLATE_BASE
TEMPLATE_PARTICIPACAO = TEMPLATE_BASE
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGO = BASE/'assets'/'brasao_ufrr.png'
LOGIN_IMAGE = BASE/'assets'/'ufrr_foto_login_v24.jpg'
PDF_DIR.mkdir(exist_ok=True)
SIGN_DIR.mkdir(parents=True, exist_ok=True)

CRITERIOS = [
 ('Relevância do tema', .20),
 ('Clareza e adequação dos objetivos', .15),
 ('Adequação e clareza da metodologia', .20),
 ('Relevância dos resultados alcançados', .30),
 ('Uso da norma culta e adequação ao template', .15),
]
RECOMENDACOES = ['Aprovado sem correção', 'Aprovado com correção', 'Não aprovado']

def conn():
    # Conexão tolerante a concorrência do Streamlit/SQLite.
    # WAL permite leituras simultâneas e busy_timeout evita falhas transitórias.
    c=sqlite3.connect(DB, timeout=30, check_same_thread=False)
    c.row_factory=sqlite3.Row
    try:
        c.execute('PRAGMA journal_mode=WAL')
        c.execute('PRAGMA busy_timeout=30000')
        c.execute('PRAGMA foreign_keys=ON')
        c.execute('PRAGMA synchronous=NORMAL')
    except sqlite3.Error:
        pass
    return c

def pw(s):
    """Hash seguro para novas senhas. Mantém formato identificável para migração."""
    iterations = 240000
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', s.encode('utf-8'), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"

def verify_password(password, stored):
    """Valida PBKDF2 e também aceita hashes SHA-256 antigos para migração."""
    if not stored:
        return False
    if stored.startswith('pbkdf2_sha256$'):
        try:
            _, iterations, salt_hex, digest_hex = stored.split('$', 3)
            calc = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt_hex), int(iterations))
            return hmac.compare_digest(calc.hex(), digest_hex)
        except Exception:
            return False
    return hmac.compare_digest(stored, hashlib.sha256(password.encode('utf-8')).hexdigest())

def now(): return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def _init_db_once():
    c=conn(); cur=c.cursor()
    cur.executescript('''
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,email TEXT UNIQUE,nome TEXT,perfil TEXT,senha TEXT,ativo INTEGER DEFAULT 1,tipo_autenticacao TEXT DEFAULT 'local',deve_trocar_senha INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS trabalhos(id INTEGER PRIMARY KEY AUTOINCREMENT,codigo TEXT UNIQUE,nomes TEXT,area TEXT,titulo TEXT,resumo TEXT,arquivo TEXT,criado_em TEXT);
    CREATE TABLE IF NOT EXISTS atribuicoes(id INTEGER PRIMARY KEY AUTOINCREMENT,trabalho_id INTEGER,avaliador_id INTEGER,tipo TEXT DEFAULT 'principal',UNIQUE(trabalho_id,avaliador_id,tipo));
    CREATE TABLE IF NOT EXISTS avaliacoes(id INTEGER PRIMARY KEY AUTOINCREMENT,trabalho_id INTEGER,avaliador_id INTEGER,tipo TEXT DEFAULT 'principal',n1 REAL,n2 REAL,n3 REAL,n4 REAL,n5 REAL,nota REAL,comentario TEXT,recomendacao TEXT,enviada_em TEXT,UNIQUE(trabalho_id,avaliador_id,tipo));
    CREATE TABLE IF NOT EXISTS auditoria(id INTEGER PRIMARY KEY AUTOINCREMENT,usuario TEXT,acao TEXT,quando TEXT);
    CREATE TABLE IF NOT EXISTS certificado_config(id INTEGER PRIMARY KEY CHECK(id=1),prof1_nome TEXT DEFAULT '',prof1_cargo TEXT DEFAULT '',prof1_assinatura TEXT DEFAULT '',prof2_nome TEXT DEFAULT '',prof2_cargo TEXT DEFAULT '',prof2_assinatura TEXT DEFAULT '',prof3_nome TEXT DEFAULT '',prof3_cargo TEXT DEFAULT '',prof3_assinatura TEXT DEFAULT '',prof4_nome TEXT DEFAULT '',prof4_cargo TEXT DEFAULT '',prof4_assinatura TEXT DEFAULT '',data_inicio TEXT DEFAULT '',data_fim TEXT DEFAULT '',local TEXT DEFAULT 'Boa Vista/RR');
    ''')
    # Migração compatível com bancos anteriores.
    tcols=[r[1] for r in cur.execute('PRAGMA table_info(trabalhos)').fetchall()]
    if 'nomes' not in tcols: cur.execute("ALTER TABLE trabalhos ADD COLUMN nomes TEXT DEFAULT ''")
    cols=[r[1] for r in cur.execute('PRAGMA table_info(users)').fetchall()]
    if 'tipo_autenticacao' not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN tipo_autenticacao TEXT DEFAULT 'local'")
    if 'deve_trocar_senha' not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN deve_trocar_senha INTEGER DEFAULT 0")
    acols=[r[1] for r in cur.execute('PRAGMA table_info(avaliacoes)').fetchall()]
    if 'recomendacao' not in acols:
        cur.execute("ALTER TABLE avaliacoes ADD COLUMN recomendacao TEXT")
    # Inicialização: não criar avaliadores demonstrativos.
    # A conta master é configurada por variáveis de ambiente, evitando
    # publicar uma senha fixa no código-fonte.
    master_email = os.getenv('MASTER_EMAIL', 'admin@example.local').strip().lower()
    master_name = os.getenv('MASTER_NAME', 'Administrador local').strip()
    master_password = os.getenv('MASTER_INITIAL_PASSWORD', '')
    if not master_password:
        c.rollback(); c.close()
        raise RuntimeError('MASTER_INITIAL_PASSWORD não configurada. Crie um arquivo .env a partir de .env.example antes de iniciar a aplicação.')
    cur.execute("INSERT OR IGNORE INTO users(email,nome,perfil,senha,tipo_autenticacao,deve_trocar_senha) VALUES(?,?,?,?,?,0)",(master_email,master_name,'master',pw(master_password),'local'))
    # Não conceder acesso automaticamente a qualquer domínio institucional.
    # O usuário precisa estar previamente cadastrado na tabela users.
    c.commit(); c.close()

def init_db():
    # Em alguns ambientes o Streamlit mantém uma execução anterior por alguns instantes.
    # Tentar novamente evita o erro 'database is locked' sem exigir intervenção manual.
    import time
    last=None
    for tentativa in range(8):
        try:
            _init_db_once()
            return
        except sqlite3.OperationalError as e:
            last=e
            if 'locked' not in str(e).lower() or tentativa == 7:
                raise
            time.sleep(0.5*(tentativa+1))
    raise last

def q(sql,args=(),many=False):
    # Pequena política de retry para locks momentâneos do SQLite.
    import time
    ultimo=None
    for tentativa in range(6):
        c=None
        try:
            c=conn(); cur=c.cursor(); cur.execute(sql,args)
            rows=cur.fetchall() if sql.lstrip().upper().startswith('SELECT') else None
            c.commit(); c.close(); return rows
        except sqlite3.OperationalError as e:
            ultimo=e
            if c is not None:
                try: c.rollback(); c.close()
                except Exception: pass
            if 'locked' not in str(e).lower() or tentativa == 5:
                raise
            time.sleep(0.35*(tentativa+1))
    raise ultimo

def _write_retry(fn, attempts=6):
    import time
    last=None
    for i in range(attempts):
        try:
            return fn()
        except sqlite3.OperationalError as e:
            last=e
            if 'locked' not in str(e).lower() or i == attempts-1:
                raise
            time.sleep(0.35*(i+1))
    raise last

def log(user,action): q('INSERT INTO auditoria(usuario,acao,quando) VALUES(?,?,?)',(user,action,now()))

def df(sql,args=()):
    c=conn()
    try:
        return pd.read_sql_query(sql,c,params=args)
    finally:
        c.close()

def user_by_email(email):
    r=q('SELECT * FROM users WHERE lower(email)=lower(?) AND ativo=1',(email,)); return dict(r[0]) if r else None

def get_user(uid):
    r=q('SELECT * FROM users WHERE id=?',(uid,)); return dict(r[0]) if r else None

def header():
    st.markdown('<div class="topbar">', unsafe_allow_html=True)
    left, mid, right = st.columns([1.15, 5.2, 2.1], vertical_alignment='center')
    with left:
        if LOGO.exists(): st.image(str(LOGO), width=82)
    with mid:
        st.markdown('<div class="brand-title">Avaliação de Resumos Científicos</div><div class="brand-sub">Evento Científico UFRR · Ciência, diversidade e desenvolvimento para a Amazônia</div>', unsafe_allow_html=True)
    with right:
        u=st.session_state.user
        papel='Coordenação Master' if u['perfil']=='master' else ('Coordenação do Evento' if u['perfil']=='coord' else 'Avaliador')
        iniciais=''.join([x[0] for x in u['nome'].split()[:2]]).upper()
        st.markdown(f'<div style="display:flex;justify-content:flex-end;align-items:center;gap:10px"><div style="text-align:right"><b style="color:#123f63">{u["nome"]}</b><br><span class="brand-sub">{papel}</span></div><div style="background:#0b3b60;color:white;border-radius:50%;width:38px;height:38px;display:flex;align-items:center;justify-content:center;font-weight:800">{iniciais}</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def login():
    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)
    left,right=st.columns([1.15,1], gap='large', vertical_alignment='center')
    with left:
        if LOGIN_IMAGE.exists():
            st.image(str(LOGIN_IMAGE), width='stretch')
        else:
            if LOGO.exists(): st.image(str(LOGO), width=300)
            st.markdown('<h1 style="font-size:32px!important;margin-top:8px">Avaliação de Resumos</h1><div style="font-size:18px;color:#1268b3;font-weight:700">Evento Científico UFRR</div><p style="color:#60758a;font-size:15px;max-width:430px">Ciência, diversidade e desenvolvimento para a Amazônia.</p>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="login-card"><h2 style="margin-top:0">Acesso ao sistema</h2><p style="color:#60758a">Informe suas credenciais para continuar.</p>', unsafe_allow_html=True)
        email=st.text_input('E-mail', placeholder='seu.email@ufrr.br')
        senha=st.text_input('Senha',type='password', placeholder='Digite sua senha')
        if st.button('Entrar',type='primary',width='stretch'):
            u=user_by_email(email.strip())
            if u and verify_password(senha, u['senha']):
                # Migra automaticamente contas antigas armazenadas com SHA-256.
                if not str(u['senha']).startswith('pbkdf2_sha256$'):
                    q('UPDATE users SET senha=? WHERE id=?', (pw(senha), int(u['id'])))
                    u = get_user(int(u['id']))
                log(u['email'], 'Login realizado')
                st.session_state.user=u; st.rerun()
            else: st.error('E-mail ou senha inválidos.')
        st.markdown('</div>', unsafe_allow_html=True)

def sidebar(items):
    u=st.session_state.user
    if LOGO.exists(): st.sidebar.image(str(LOGO), width=78)
    st.sidebar.markdown('<div style="font-size:20px;font-weight:800;color:#0b3b60;padding:2px 0">Plataforma de Avaliação de Resumos - UFRR</div>', unsafe_allow_html=True)
    st.sidebar.markdown(f'<div style="color:#60758a;font-size:12px;margin-bottom:14px">{u["nome"]}</div>', unsafe_allow_html=True)
    current=st.session_state.get('menu_choice',items[0])
    if current not in items: current=items[0]
    st.sidebar.markdown('<div style="font-size:12px;font-weight:700;color:#60758a;margin-bottom:6px">MENU</div>', unsafe_allow_html=True)
    escolha=current
    for item in items:
        label=('✓ ' if current==item else '')+item
        if st.sidebar.button(label,key=f'menu_{item}',width='stretch'):
            if item=='Sair':
                log(u['email'], 'Logout realizado'); st.session_state.pop('user',None); st.session_state.pop('menu_choice',None); st.rerun()
            st.session_state.menu_choice=item; escolha=item; st.rerun()
    return escolha

def page_profile():
    u = st.session_state.user
    st.title('Meu perfil')
    
    st.caption('Atualize seus dados e, se necessário, altere sua senha. Todas as contas são administradas localmente nesta plataforma.')
    with st.form('perfil_form'):
        nome = st.text_input('Nome completo', value=u['nome'])
        email = st.text_input('E-mail', value=u['email'])
        senha_atual = ''
        nova = ''
        confirmar = ''
        if True:
            senha_atual = st.text_input('Senha atual', type='password')
            nova = st.text_input('Nova senha', type='password')
            confirmar = st.text_input('Confirmar nova senha', type='password')
        salvar = st.form_submit_button('Salvar alterações', type='primary')
    if salvar:
        if not nome.strip() or not email.strip():
            st.error('Nome e e-mail são obrigatórios.')
            return
        if not verify_password(senha_atual, u['senha']):
            st.error('Informe corretamente sua senha atual.')
            return
        if nova and (len(nova) < 8 or nova != confirmar):
            st.error('A nova senha deve ter pelo menos 8 caracteres e coincidir com a confirmação.')
            return
        try:
            if nova:
                q('UPDATE users SET nome=?,email=?,senha=?,deve_trocar_senha=0 WHERE id=?', (nome.strip(), email.strip().lower(), pw(nova), int(u['id'])))
            else:
                q('UPDATE users SET nome=?,email=? WHERE id=?', (nome.strip(), email.strip().lower(), int(u['id'])))
            st.session_state.user = get_user(int(u['id']))
            log(st.session_state.user['email'], 'Atualizou o próprio perfil')
            st.success('Perfil atualizado com sucesso.')
            st.rerun()
        except Exception as e:
            st.error(f'Não foi possível atualizar o perfil: {e}')

def page_dashboard():
    st.markdown('<div class="page-intro"><div class="page-intro-title">Visão geral</div><div class="page-intro-text">Acompanhe o andamento das avaliações e a distribuição dos trabalhos por área.</div></div>', unsafe_allow_html=True)
    b1, b2, b3 = st.columns([1, 1, 4])
    with b1:
        if st.button('Criar backup do banco'):
            backup_dir = BACKUP_DIR
            backup_dir.mkdir(parents=True, exist_ok=True)
            destino = backup_dir / f'avaliacao_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
            # Usa o mecanismo nativo de backup do SQLite para gerar um arquivo
            # consistente mesmo quando o banco está em uso pelo Streamlit.
            src=conn(); dst=sqlite3.connect(destino, timeout=30)
            try:
                src.backup(dst)
            finally:
                try: dst.close()
                except Exception: pass
                try: src.close()
                except Exception: pass
            log(st.session_state.user['email'], f'Criou backup {destino.name}')
            st.session_state['ultimo_backup']=destino.name
            st.success(f'Backup criado: {destino.name}')
    with b2:
        backups=sorted(BACKUP_DIR.glob('*.db'), key=lambda x:x.stat().st_mtime, reverse=True) if BACKUP_DIR.exists() else []
        if backups:
            bsel=st.selectbox('Backup disponível', [x.name for x in backups], key='backup_download_sel')
            bp=BACKUP_DIR/bsel
            st.download_button('Baixar backup selecionado', bp.read_bytes(), bsel, 'application/x-sqlite3', key='download_backup')
    with b3:
        st.markdown('**Restaurar backup**')
        up_backup=st.file_uploader('Envie um arquivo .db de backup', type=['db'], key='restore_backup_file')
        confirmar_restore=st.checkbox('Confirmo que desejo substituir o banco atual pelo backup enviado.', key='confirm_restore')
        if up_backup is not None and confirmar_restore and st.button('Restaurar backup', type='secondary', key='restore_backup_btn'):
            tmp=DATA_DIR/'_restore_tmp.db'
            try:
                tmp.write_bytes(up_backup.getvalue())
                test=sqlite3.connect(tmp, timeout=30)
                ok=test.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
                test.close()
                if not ok: raise ValueError('O arquivo de backup não passou no teste de integridade do SQLite.')
                # Fecha conexões próprias e troca atomicamente o arquivo.
                os.replace(tmp, DB)
                log(st.session_state.user['email'], f'Restaurou backup {up_backup.name}')
                st.success('Backup restaurado com sucesso. A página será recarregada.')
                st.rerun()
            except Exception as e:
                try: tmp.unlink(missing_ok=True)
                except Exception: pass
                st.error(f'Não foi possível restaurar o backup: {e}')
    if st.session_state.user.get('perfil') == 'master':
        st.markdown('---')
        st.subheader('Reinicializar plataforma')
        st.warning('Use somente para iniciar um novo ciclo/ano. A operação remove todos os trabalhos, PDFs/resumos, avaliações, atribuições, avaliadores, subcoordenadores e configurações de certificados, mantendo somente o coordenador master. Um backup automático será criado antes da limpeza.')
        conf_reset=st.checkbox('Confirmo que desejo REINICIALIZAR a plataforma',key='conf_reinicializar')
        senha_reset=st.text_input('Senha do coordenador master',type='password',key='senha_reinicializar',help='A reinicialização só pode ser executada pelo coordenador master e exige a senha atual.')
        if conf_reset and st.button('Reinicializar',type='secondary',key='reinicializar_btn'):
            # Dupla proteção: a seção já é exibida apenas ao master e a operação
            # exige a senha atual armazenada no banco, além da confirmação explícita.
            master=get_user(int(st.session_state.user['id']))
            if not master or master.get('perfil') != 'master':
                st.error('Apenas o coordenador master pode reinicializar a plataforma.')
                return
            if not senha_reset or not verify_password(senha_reset, master['senha']):
                st.error('Senha do coordenador master incorreta. A plataforma não foi reinicializada.')
                return
            try:
                backup_name=_reinicializar_plataforma()
                log(master['email'],f'Reinicializou a plataforma; backup automático {backup_name}')
                st.session_state.user=get_user(int(master['id']))
                _set_flash(f'Plataforma reinicializada com sucesso. Backup automático criado: {backup_name}.')
                st.rerun()
            except Exception as e:
                st.error(f'Não foi possível reinicializar a plataforma: {e}')
    areas = df("SELECT DISTINCT area FROM trabalhos WHERE TRIM(area) <> '' ORDER BY area")['area'].tolist()
    filtro_area = st.selectbox('Filtrar painel por área', ['Todas as áreas'] + areas, key='painel_area')
    where = '' if filtro_area == 'Todas as áreas' else ' WHERE t.area = ? '
    params = () if filtro_area == 'Todas as áreas' else (filtro_area,)
    total=int(df('SELECT COUNT(*) n FROM trabalhos' + ('' if not where else ' WHERE area = ?'), params).iloc[0,0])
    atribuicoes=int(df("SELECT COUNT(*) n FROM atribuicoes a JOIN trabalhos t ON t.id=a.trabalho_id WHERE a.tipo IN ('principal','principal2')" + ('' if not where else ' AND t.area = ?'), params).iloc[0,0])
    avaliadas=int(df("SELECT COUNT(*) n FROM avaliacoes a JOIN trabalhos t ON t.id=a.trabalho_id WHERE a.tipo IN ('principal','principal2')" + ('' if not where else ' AND t.area = ?'), params).iloc[0,0])
    concluidos=int(df("SELECT COUNT(*) n FROM trabalhos t WHERE (1=1)" + ('' if not where else ' AND t.area = ?') + " AND (SELECT COUNT(*) FROM avaliacoes a WHERE a.trabalho_id=t.id)>=1", params).iloc[0,0])
    discrep=int(df("SELECT COUNT(*) n FROM (SELECT t.id FROM trabalhos t JOIN avaliacoes a ON a.trabalho_id=t.id AND a.tipo IN ('principal','principal2')" + ('' if not where else ' WHERE t.area = ?') + " GROUP BY t.id HAVING COUNT(a.id)=2 AND ABS(MAX(a.nota)-MIN(a.nota))>4)", params).iloc[0,0])
    cols=st.columns(5)
    cards=[('Trabalhos submetidos',total,'Base cadastrada'),('Atribuições principais',atribuicoes,'Avaliadores atribuídos'),('Avaliações recebidas',avaliadas,'Notas enviadas'),('Trabalhos concluídos',concluidos,'Com pelo menos 1 avaliação'),('Discrepâncias',discrep,'Diferença superior a 4,0')]
    for c,(label,val,note) in zip(cols,cards):
        c.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{val}</div><div class="kpi-note">{note}</div></div>',unsafe_allow_html=True)
    st.markdown('### Acompanhamento por área')
    area_sql = """SELECT t.area, COUNT(*) trabalhos,
      SUM(CASE WHEN (SELECT COUNT(*) FROM avaliacoes a WHERE a.trabalho_id=t.id)>=1 THEN 1 ELSE 0 END) concluidos,
      SUM(CASE WHEN (SELECT COUNT(*) FROM atribuicoes x WHERE x.trabalho_id=t.id AND x.tipo IN ('principal','principal2'))<2 THEN 1 ELSE 0 END) sem_dois_avaliadores
      FROM trabalhos t"""
    if filtro_area != 'Todas as áreas':
        area_sql += ' WHERE t.area = ?'
    area_sql += ' GROUP BY t.area ORDER BY t.area'
    area=df(area_sql, params)
    if area.empty: st.info('Nenhum trabalho cadastrado.')
    else:
        area['progresso (%)']=(area['concluidos']/area['trabalhos']*100).round(1)
        st.dataframe(area.rename(columns={'area':'Área','trabalhos':'Trabalhos','concluidos':'Concluídos','sem_dois_avaliadores':'Sem duas atribuições','progresso (%)':'Progresso (%)'}),width='stretch',hide_index=True)
    st.markdown('### Status dos trabalhos')
    data_sql = """SELECT t.codigo,t.area,t.titulo,
      (SELECT COUNT(*) FROM atribuicoes x WHERE x.trabalho_id=t.id AND x.tipo IN ('principal','principal2')) atribuidores,
      (SELECT COUNT(*) FROM avaliacoes x WHERE x.trabalho_id=t.id AND x.tipo IN ('principal','principal2')) avaliadas,
      (SELECT COUNT(*) FROM avaliacoes x WHERE x.trabalho_id=t.id AND x.tipo='terceiro') terceiro
      FROM trabalhos t"""
    if filtro_area != 'Todas as áreas':
        data_sql += ' WHERE t.area = ?'
    data_sql += ' ORDER BY t.area, CAST(t.codigo AS INTEGER), t.codigo'
    data=df(data_sql, params)
    def status(r):
        if r.atribuidores<1: return 'Sem avaliador atribuído'
        if r.avaliadas<1: return 'Aguardando avaliação'
        if r.avaliadas<2 and r.atribuidores>=2: return '1 avaliação recebida - 2ª pendente'
        if r.terceiro>0: return 'Avaliação completa'
        return 'Avaliações concluídas'
    if not data.empty: data['Status']=data.apply(status,axis=1)
    st.dataframe(data.rename(columns={'codigo':'Código','area':'Área','titulo':'Título','atribuidores':'Avaliadores atribuídos','avaliadas':'Avaliações','terceiro':'Terceiro avaliador'}),width='stretch',hide_index=True)
    st.download_button('Exportar acompanhamento CSV',data.to_csv(index=False).encode('utf-8-sig'),'acompanhamento.csv','text/csv')

def _sort_codes(frame):
    if frame.empty:
        return frame
    return frame.assign(_ord=frame['codigo'].astype(str).str.extract(r'(\d+)', expand=False).fillna('0').astype(int)).sort_values(['_ord','codigo'], kind='stable').drop(columns=['_ord'])

def _safe_filename(text):
    import re
    s = re.sub(r'[<>:"/\\|?*]+', '_', str(text or '').strip())
    s = re.sub(r'\s+', ' ', s).strip(' .')
    return s[:160] or 'documento'

def _author_text(nomes):
    parts=[p.strip() for p in str(nomes or '').replace('\n',';').split(';') if p.strip()]
    if not parts:
        return 'os autores do trabalho'
    if len(parts)==1: return parts[0]
    if len(parts)==2: return f'{parts[0]} e {parts[1]}'
    return ', '.join(parts[:-1]) + ' e ' + parts[-1]

def _area_label(area):
    return 'PIBIC-EM' if str(area).strip().upper() == 'EM' else str(area or '').strip()

def _senha_inicial_nome(nome):
    primeiro = str(nome or '').strip().split()[0] if str(nome or '').strip() else 'usuario'
    primeiro = primeiro.replace('ç','c').replace('Ç','C')
    primeiro = unicodedata.normalize('NFKD', primeiro)
    primeiro = ''.join(ch for ch in primeiro if not unicodedata.combining(ch))
    primeiro = ''.join(ch for ch in primeiro.lower() if ch.isalnum())
    return primeiro or 'usuario'

def _cert_config():
    r=df('SELECT * FROM certificado_config WHERE id=1')
    if r.empty:
        q("INSERT OR IGNORE INTO certificado_config(id,prof1_nome,prof2_nome,prof3_nome,prof4_nome,local) VALUES(1,'','','','',?)",('Boa Vista/RR',))
        r=df('SELECT * FROM certificado_config WHERE id=1')
    return r.iloc[0].to_dict()

def _save_signature(uploaded, slot):
    if uploaded is None: return None
    ext=Path(uploaded.name).suffix.lower()
    if ext not in ('.png','.jpg','.jpeg','.webp'): ext='.png'
    path=SIGN_DIR/f'assinatura_{slot}{ext}'
    path.write_bytes(uploaded.getvalue())
    return str(path.relative_to(BASE)).replace('\\','/')

def _date_range_pt(data_inicio, data_fim):
    meses=['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro']
    if not data_inicio: return '________________'
    di=datetime.strptime(data_inicio,'%Y-%m-%d').date()
    if not data_fim or data_fim==data_inicio: return f'{di.day} de {meses[di.month-1]} de {di.year}'
    dfim=datetime.strptime(data_fim,'%Y-%m-%d').date()
    if di.year==dfim.year and di.month==dfim.month: return f'{di.day} a {dfim.day} de {meses[di.month-1]} de {di.year}'
    if di.year==dfim.year: return f'{di.day} de {meses[di.month-1]} a {dfim.day} de {meses[dfim.month-1]} de {di.year}'
    return f'{di.day} de {meses[di.month-1]} de {di.year} a {dfim.day} de {meses[dfim.month-1]} de {dfim.year}'

def page_import():
    st.title('Importar resumos')
    st.caption('Cadastre resumos por planilha ou inclua um trabalho individualmente. O PDF pode ser associado no mesmo cadastro.')
    cols=['Código','Nomes','Área','Título','Resumo','Nome do arquivo']
    st.write('Use exatamente estas colunas na planilha:')
    st.code(' | '.join(cols))
    modelo=pd.DataFrame(columns=cols); bio=io.BytesIO(); modelo.to_excel(bio,index=False)
    st.download_button('Baixar modelo Excel',bio.getvalue(),'modelo_resumos.xlsx')

    with st.expander('Cadastrar um resumo manualmente', expanded=True):
        with st.form('manual_trabalho'):
            codigo=st.text_input('Código *')
            nomes=st.text_input('Nomes dos autores *',help='Separe os autores por ponto e vírgula.')
            area=st.text_input('Área *')
            titulo=st.text_input('Título *')
            resumo=st.text_area('Resumo',height=180)
            pdf_up=st.file_uploader('PDF do resumo (opcional)',type=['pdf'],key='manual_pdf')
            salvar=st.form_submit_button('Cadastrar resumo',type='primary')
        if salvar:
            if not codigo.strip() or not nomes.strip() or not area.strip() or not titulo.strip():
                st.error('Código, nomes, área e título são obrigatórios.')
            else:
                arq=f'{_safe_filename(codigo)}.pdf' if pdf_up is not None else ''
                try:
                    q('INSERT INTO trabalhos(codigo,nomes,area,titulo,resumo,arquivo,criado_em) VALUES(?,?,?,?,?,?,?)',(codigo.strip(),nomes.strip(),area.strip(),titulo.strip(),resumo.strip(),arq,now()))
                    if pdf_up is not None:
                        (PDF_DIR/arq).write_bytes(pdf_up.getvalue())
                    log(st.session_state.user['email'],f'Cadastrou manualmente o trabalho {codigo.strip()}')
                    _set_flash(f'Trabalho {codigo.strip()} cadastrado com sucesso.')
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error('Já existe um trabalho com esse código.')
                except Exception as e:
                    st.error(f'Não foi possível cadastrar o trabalho: {e}')

    st.subheader('Importar por planilha')
    up=st.file_uploader('Planilha Excel ou CSV',type=['xlsx','xls','csv'],key='planilha_resumos')
    if not up:return
    try:
        d=pd.read_csv(up) if up.name.lower().endswith('.csv') else pd.read_excel(up)
    except Exception as e: st.error(str(e)); return
    missing=[x for x in cols if x not in d.columns]
    if missing: st.error('Colunas ausentes: '+', '.join(missing)); return
    d=d[cols].fillna(''); d['Código']=d['Código'].astype(str).str.strip()
    st.dataframe(d,width='stretch',hide_index=True)
    if st.button('Validar e importar planilha',type='primary'):
        ok=0; erros=[]
        for _,r in d.iterrows():
            if not r['Código']: continue
            try:
                q('''INSERT INTO trabalhos(codigo,nomes,area,titulo,resumo,arquivo,criado_em) VALUES(?,?,?,?,?,?,?)
                     ON CONFLICT(codigo) DO UPDATE SET nomes=excluded.nomes,area=excluded.area,titulo=excluded.titulo,resumo=excluded.resumo,arquivo=excluded.arquivo''',tuple(r.tolist()+[now()]))
                ok+=1
            except Exception as e: erros.append(f"{r['Código']}: {e}")
        log(st.session_state.user['email'],f'Importou/atualizou {ok} trabalhos por planilha')
        st.success(f'{ok} trabalho(s) importado(s)/atualizado(s).')
        if erros: st.warning('Alguns registros não foram processados: ' + ' | '.join(erros[:10]))

def _delete_work_ids(ids):
    """Exclui trabalhos e todos os dados derivados, inclusive avaliações e atribuições."""
    ids=[int(x) for x in ids]
    if not ids: return 0
    placeholders=','.join(['?']*len(ids))
    # Guarda os nomes dos PDFs antes de excluir os registros.
    rows=q(f"SELECT arquivo,codigo FROM trabalhos WHERE id IN ({placeholders})",tuple(ids))
    q(f"DELETE FROM avaliacoes WHERE trabalho_id IN ({placeholders})",tuple(ids))
    q(f"DELETE FROM atribuicoes WHERE trabalho_id IN ({placeholders})",tuple(ids))
    q(f"DELETE FROM trabalhos WHERE id IN ({placeholders})",tuple(ids))
    for r in rows:
        candidatos=[]
        if r[0]: candidatos.append(Path(str(r[0])).name)
        if r[1]: candidatos.append(f"{r[1]}.pdf")
        for nome in dict.fromkeys(candidatos):
            try: (PDF_DIR/nome).unlink(missing_ok=True)
            except Exception: pass
    return len(ids)

def _delete_evaluator_ids(ids):
    """Exclui avaliadores e suas avaliações/atribuições, inclusive históricas."""
    ids=[int(x) for x in ids]
    if not ids: return 0
    placeholders=','.join(['?']*len(ids))
    q(f"DELETE FROM avaliacoes WHERE avaliador_id IN ({placeholders})",tuple(ids))
    q(f"DELETE FROM atribuicoes WHERE avaliador_id IN ({placeholders})",tuple(ids))
    q(f"DELETE FROM users WHERE id IN ({placeholders}) AND perfil='avaliador'",tuple(ids))
    return len(ids)

def _reinicializar_plataforma():
    """Limpa o ciclo do evento, preservando somente o coordenador master."""
    # Backup automático antes da operação destrutiva.
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    destino=BACKUP_DIR/f"pre_reinicializacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    src=conn(); dst=sqlite3.connect(destino,timeout=30)
    try: src.backup(dst)
    finally:
        try: dst.close()
        except Exception: pass
        try: src.close()
        except Exception: pass
    q('DELETE FROM avaliacoes')
    q('DELETE FROM atribuicoes')
    q("DELETE FROM trabalhos")
    q("DELETE FROM users WHERE perfil <> 'master'")
    q("DELETE FROM auditoria")
    q("INSERT OR IGNORE INTO certificado_config(id,local) VALUES(1,'Boa Vista/RR')")
    q("UPDATE certificado_config SET prof1_nome='',prof1_cargo='',prof1_assinatura='',prof2_nome='',prof2_cargo='',prof2_assinatura='',prof3_nome='',prof3_cargo='',prof3_assinatura='',prof4_nome='',prof4_cargo='',prof4_assinatura='',data_inicio='',data_fim='',local='Boa Vista/RR' WHERE id=1")
    # PDFs dos resumos e assinaturas pertencem ao ciclo anterior.
    for pasta in (PDF_DIR,SIGN_DIR):
        if pasta.exists():
            for f in pasta.iterdir():
                if f.is_file():
                    try: f.unlink()
                    except Exception: pass
    return destino.name

def page_trabalhos():
    st.title('Trabalhos')
    d=df('SELECT * FROM trabalhos')
    if d.empty: st.info('Nenhum trabalho cadastrado.'); return
    areas=sorted([a for a in d['area'].dropna().unique().tolist() if str(a).strip()],key=lambda x:str(x).lower())
    filtro_area=st.selectbox('Filtrar por área',['Todas as áreas']+areas,key='trabalhos_area')
    ordem=st.selectbox('Ordenar códigos',['Crescente numérica','Alfabética'],key='trabalhos_ordem')
    if filtro_area!='Todas as áreas': d=d[d.area==filtro_area].copy()
    if d.empty: st.info('Nenhum trabalho encontrado para a área selecionada.'); return
    if ordem=='Crescente numérica': d=_sort_codes(d)
    else: d=d.sort_values('codigo',key=lambda x:x.astype(str).str.lower(),kind='stable')
    def pdf_exists(r):
        names=[]
        if str(r.get('arquivo','')).strip(): names.append(Path(str(r['arquivo'])).name)
        names.append(f"{r['codigo']}.pdf")
        return any((PDF_DIR/n).is_file() for n in dict.fromkeys(names))
    d['PDF']=d.apply(lambda r:'Disponível' if pdf_exists(r) else 'Não enviado',axis=1)
    st.dataframe(d[['codigo','nomes','area','titulo','arquivo','PDF']].rename(columns={'codigo':'Código','nomes':'Autores','area':'Área','titulo':'Título'}),width='stretch',hide_index=True)
    st.caption('A coluna PDF indica se o documento está salvo na pasta de resumos.')
    codes=d.codigo.tolist(); code=st.selectbox('Selecione o código',codes)
    row=d[d.codigo==code].iloc[0]
    qtd_av=int(df('SELECT COUNT(*) n FROM avaliacoes WHERE trabalho_id=?',(int(row.id),)).iloc[0,0])
    if qtd_av: st.warning('Este trabalho já possui avaliações. Alterações de conteúdo ficam bloqueadas para preservar a integridade do julgamento.')
    with st.expander('Modificar trabalho',expanded=True):
        area=st.text_input('Área',row.area); titulo=st.text_input('Título',row.titulo); nomes=st.text_input('Nomes dos autores',row.nomes); resumo=st.text_area('Resumo',row.resumo,height=180); arq=st.text_input('Nome do arquivo',row.arquivo)
        pdf_up=st.file_uploader('Enviar/substituir PDF',type=['pdf'],key=f'pdf_{int(row.id)}')
        if pdf_up is not None: arq=f'{_safe_filename(code)}.pdf'
        if st.button('Salvar alterações',type='primary') and qtd_av==0:
            q('UPDATE trabalhos SET area=?,titulo=?,nomes=?,resumo=?,arquivo=? WHERE codigo=?',(area,titulo,nomes,resumo,arq,code))
            if pdf_up is not None: (PDF_DIR/arq).write_bytes(pdf_up.getvalue())
            log(st.session_state.user['email'],f'Editou trabalho {code}'); _set_flash(f'Trabalho {code} atualizado com sucesso.'); st.rerun()
    st.subheader('Excluir trabalhos e resumos')
    st.warning('A exclusão é definitiva e também remove avaliações, atribuições e a entrada correspondente nos relatórios. É permitida mesmo quando o trabalho já foi avaliado.')
    todos_codes=[str(x) for x in d.codigo.tolist()]
    selecionar_todos=st.checkbox('Selecionar todos os trabalhos desta lista',key='sel_todos_trabalhos')
    if selecionar_todos:
        selecionados=todos_codes
    else:
        selecionados=st.multiselect('Selecione um ou mais trabalhos para excluir',todos_codes,key='trabalhos_para_excluir')
    confirmar=st.checkbox('Confirmo a exclusão definitiva dos trabalhos selecionados',key='conf_excluir_trabalhos')
    if confirmar and selecionados and st.button('Excluir trabalhos selecionados',type='secondary',key='excluir_trabalhos_sel'):
        ids=[int(d[d.codigo.astype(str)==str(c)].iloc[0].id) for c in selecionados]
        n=_delete_work_ids(ids)
        log(st.session_state.user['email'],f'Excluiu {n} trabalho(s)/resumo(s), incluindo avaliações e atribuições')
        st.success(f'{n} trabalho(s) excluído(s).')
        st.rerun()

def page_users():
    st.title('Gestão de avaliadores')
    st.caption('Cadastre, edite, ative ou bloqueie contas de avaliadores.')
    st.dataframe(df("SELECT id,nome,email,perfil,tipo_autenticacao AS autenticacao,CASE WHEN ativo=1 THEN 'Ativo' ELSE 'Bloqueado' END AS status FROM users ORDER BY nome"),width='stretch',hide_index=True)
    st.subheader('Importar avaliadores por planilha')
    st.caption('A planilha deve conter Nome e E-mail. A senha inicial é primeiro_nome + avaliador para todas as contas, independentemente do domínio. No primeiro acesso, a troca de senha será obrigatória.')
    arquivo_planilha=st.file_uploader('Planilha de avaliadores (.xlsx ou .csv)',type=['xlsx','csv'],key='planilha_avaliadores')
    if arquivo_planilha is not None and st.button('Importar planilha',type='primary'):
        try:
            imp=pd.read_csv(arquivo_planilha) if arquivo_planilha.name.lower().endswith('.csv') else pd.read_excel(arquivo_planilha)
            imp.columns=[str(c).strip().lower() for c in imp.columns]
            mapa={c.replace('á','a').replace('ã','a').replace('é','e').replace('ê','e').replace('í','i').replace('ó','o').replace('ô','o').replace('ú','u'):c for c in imp.columns}
            nome_col=mapa.get('nome') or mapa.get('nome completo'); email_col=mapa.get('e-mail') or mapa.get('email')
            if not nome_col or not email_col: st.error('A planilha precisa conter as colunas Nome e E-mail.')
            else:
                cred=[]; ok=0; erros=[]
                for _,r in imp.iterrows():
                    nome=str(r[nome_col]).strip(); email=str(r[email_col]).strip().lower()
                    if not nome or not email or email=='nan': continue
                    # Duplicidade: se o e-mail já estiver cadastrado, não importar novamente.
                    # A comparação também considera nome + e-mail para tornar a regra explícita.
                    existente=q('SELECT id FROM users WHERE lower(email)=lower(?) OR (lower(trim(nome))=lower(trim(?)) AND lower(email)=lower(?))',(email,nome,email))
                    if existente:
                        continue
                    primeiro=_senha_inicial_nome(nome)
                    senha_inicial=primeiro+'avaliador'
                    try:
                        q('INSERT INTO users(nome,email,perfil,senha,ativo,tipo_autenticacao,deve_trocar_senha) VALUES(?,?,?,?,1,\'local\',1)',(nome,email,'avaliador',pw(senha_inicial)))
                        cred.append({'Nome':nome,'E-mail':email,'Senha inicial':senha_inicial}); ok+=1
                    except sqlite3.IntegrityError:
                        # Outra linha da própria planilha ou outra sessão pode ter criado a conta.
                        continue
                    except Exception as e: erros.append(f'{email}: {e}')
                if cred:
                    st.success(f'{ok} avaliador(es) importado(s).')
                    st.dataframe(pd.DataFrame(cred),hide_index=True,width='stretch')
                    st.download_button('Baixar credenciais iniciais (CSV)',pd.DataFrame(cred).to_csv(index=False).encode('utf-8-sig'),'credenciais_avaliadores.csv','text/csv')
                if erros: st.warning('Contas não criadas: ' + ' | '.join(erros[:10]))
        except Exception as e: st.error(f'Não foi possível importar a planilha: {e}')
    st.subheader('Cadastrar avaliador')
    st.session_state.setdefault('novo_user_form_version',0); v=st.session_state.novo_user_form_version
    with st.form(f'novo_user_{v}'):
        nome=st.text_input('Nome completo',key=f'nome_{v}'); email=st.text_input('E-mail',key=f'email_{v}')
        senha=st.text_input('Senha inicial',type='password',key=f'senha_{v}')
        submit=st.form_submit_button('Cadastrar avaliador')
    if submit:
        if not nome.strip() or not email.strip() or not senha: st.error('Nome, e-mail e senha inicial são obrigatórios.')
        elif len(senha)<6: st.error('A senha deve possuir pelo menos 6 caracteres.')
        else:
            try:
                q('INSERT INTO users(nome,email,perfil,senha,ativo,tipo_autenticacao,deve_trocar_senha) VALUES(?,?,?,?,1,\'local\',1)',(nome.strip(),email.strip().lower(),'avaliador',pw(senha)))
                log(st.session_state.user['email'],f'Cadastrou avaliador {email.strip().lower()}'); st.success('Avaliador cadastrado.'); st.session_state.novo_user_form_version+=1; st.rerun()
            except Exception as e: st.error(f'Não foi possível cadastrar: {e}')
    usuarios=df("SELECT id,nome,email,ativo FROM users WHERE perfil='avaliador' ORDER BY nome")
    st.subheader('Administrar conta')
    escolha=st.selectbox('Selecione o avaliador',['Nenhum']+[f"{r.nome} - {r.email}" for _,r in usuarios.iterrows()])
    if escolha!='Nenhum':
        u=usuarios.loc[usuarios.apply(lambda r:f"{r['nome']} - {r['email']}"==escolha,axis=1)].iloc[0]
        uid=int(u.id)
        with st.form(f'editar_user_{uid}'):
            novo_nome=st.text_input('Nome',value=u.nome)
            novo_email=st.text_input('E-mail',value=u.email)
            nova_senha=st.text_input('Nova senha (opcional)',type='password')
            ativo=st.checkbox('Conta ativa',value=bool(u.ativo))
            salvar=st.form_submit_button('Salvar alterações')
        if salvar:
            if not novo_nome.strip() or not novo_email.strip(): st.error('Nome e e-mail são obrigatórios.')
            elif nova_senha and len(nova_senha)<6: st.error('A nova senha deve possuir pelo menos 6 caracteres.')
            else:
                try:
                    if nova_senha:
                        q('UPDATE users SET nome=?,email=?,senha=?,ativo=?,deve_trocar_senha=1 WHERE id=?',(novo_nome.strip(),novo_email.strip().lower(),pw(nova_senha),int(ativo),uid))
                    else:
                        q('UPDATE users SET nome=?,email=?,ativo=? WHERE id=?',(novo_nome.strip(),novo_email.strip().lower(),int(ativo),uid))
                    log(st.session_state.user['email'],f'Alterou conta do avaliador {uid}'); st.success('Conta atualizada.'); st.rerun()
                except Exception as e: st.error(f'Não foi possível atualizar: {e}')

    st.subheader('Excluir avaliador')
    if escolha=='Nenhum':
        st.info('Selecione um avaliador acima para excluir individualmente. A exclusão em lote permanece disponível abaixo.')
    else:
        st.warning('A exclusão remove também as atribuições e avaliações desse avaliador. É permitida mesmo que ele já tenha enviado avaliações. Essa operação não pode ser desfeita.')
        confirmar_exclusao=st.checkbox('Confirmo que desejo excluir definitivamente este avaliador',key=f'conf_excluir_av_{uid}')
        if confirmar_exclusao and st.button('Excluir avaliador definitivamente',type='secondary',key=f'excluir_av_{uid}'):
            try:
                qtd_eval=int(q('SELECT COUNT(*) FROM avaliacoes WHERE avaliador_id=?',(uid,))[0][0])
                qtd_atr=int(q('SELECT COUNT(*) FROM atribuicoes WHERE avaliador_id=?',(uid,))[0][0])
                _delete_evaluator_ids([uid])
                log(st.session_state.user['email'],f'Excluiu avaliador {uid} (avaliações={qtd_eval}, atribuições={qtd_atr})')
                st.success('Avaliador excluído com sucesso.')
                st.rerun()
            except Exception as e:
                st.error(f'Não foi possível excluir o avaliador: {e}')

    avaliadores=df("SELECT id,nome,email FROM users WHERE perfil='avaliador' ORDER BY nome")
    if not avaliadores.empty:
        st.markdown('#### Exclusão em lote')
        todos_av=[f"{r.nome} - {r.email}" for _,r in avaliadores.iterrows()]
        sel_todos_av=st.checkbox('Selecionar todos os avaliadores',key='sel_todos_avaliadores')
        sel_av=todos_av if sel_todos_av else st.multiselect('Selecione um ou mais avaliadores para excluir',todos_av,key='avaliadores_para_excluir')
        conf_lote=st.checkbox('Confirmo a exclusão definitiva dos avaliadores selecionados',key='conf_excluir_av_lote')
        if conf_lote and sel_av and st.button('Excluir avaliadores selecionados',type='secondary',key='excluir_av_lote'):
            mapa={f"{r.nome} - {r.email}":int(r.id) for _,r in avaliadores.iterrows()}
            ids=[mapa[x] for x in sel_av]
            n=_delete_evaluator_ids(ids)
            log(st.session_state.user['email'],f'Excluiu {n} avaliador(es), incluindo avaliações e atribuições')
            st.success(f'{n} avaliador(es) excluído(s).')
            st.rerun()

def page_distribution():
    st.title('Distribuição dos trabalhos')
    t=df('SELECT id,codigo,area,titulo FROM trabalhos')
    u=df("SELECT id,nome,email FROM users WHERE perfil='avaliador' AND ativo=1 ORDER BY nome")
    if t.empty or u.empty:
        st.info('Cadastre trabalhos e avaliadores primeiro.'); return
    ordem=st.selectbox('Ordenar trabalhos por código',['Crescente numérica','Alfabética'],key='distribuicao_ordem')
    t=_sort_codes(t) if ordem=='Crescente numérica' else t.sort_values('codigo',key=lambda x:x.astype(str).str.lower(),kind='stable')
    code=st.selectbox('Trabalho',t.codigo.tolist()); tr=t[t.codigo==code].iloc[0]
    current=df("SELECT id,avaliador_id,tipo FROM atribuicoes WHERE trabalho_id=? AND tipo IN ('principal','principal2')",(int(tr.id),))
    ev=df("SELECT avaliador_id,tipo FROM avaliacoes WHERE trabalho_id=? AND tipo IN ('principal','principal2')",(int(tr.id),))
    assigned_map={str(r.tipo):int(r.avaliador_id) for _,r in current.iterrows()}
    evaluated_types=set(str(r.tipo) for _,r in ev.iterrows())
    uopts={f"{r.nome} - {r.email}":int(r.id) for _,r in u.iterrows()}
    opts1=list(uopts.keys()); cur1=assigned_map.get('principal'); idx1=list(uopts.values()).index(cur1) if cur1 in uopts.values() else 0
    lock1='principal' in evaluated_types
    one=st.selectbox('Avaliador 1',opts1,index=idx1,disabled=lock1,help='Um avaliador que já enviou a avaliação não pode ser substituído.')
    opts2={'- Não atribuído -':None,**uopts}; cur2=assigned_map.get('principal2'); idx2=list(opts2.values()).index(cur2) if cur2 in opts2.values() else 0
    lock2='principal2' in evaluated_types
    two=st.selectbox('Avaliador 2 (opcional)',list(opts2),index=idx2,disabled=lock2,help='O avaliador pode ser substituído enquanto ainda não tiver enviado a avaliação.')
    one_id=uopts[one]; two_id=opts2[two]
    if two_id is not None and one_id==two_id: st.warning('Escolha avaliadores diferentes.')
    if len(evaluated_types)==1:
        st.info('Um dos avaliadores já enviou a avaliação. O outro ainda pode ser substituído ou alterado.')
    elif len(evaluated_types)>=2:
        st.warning('Os dois avaliadores principais já enviaram suas avaliações. A distribuição está bloqueada.')
    else:
        st.info('Nenhuma avaliação principal foi enviada. A distribuição pode ser alterada.')
    if st.button('Salvar distribuição',type='primary',disabled=(len(evaluated_types)>=2 or (two_id is not None and one_id==two_id))):
        if not lock1:
            q("DELETE FROM atribuicoes WHERE trabalho_id=? AND tipo='principal'",(int(tr.id),))
            q("INSERT INTO atribuicoes(trabalho_id,avaliador_id,tipo) VALUES(?,?,?)",(int(tr.id),one_id,'principal'))
        if not lock2:
            q("DELETE FROM atribuicoes WHERE trabalho_id=? AND tipo='principal2'",(int(tr.id),))
            if two_id is not None:
                q("INSERT INTO atribuicoes(trabalho_id,avaliador_id,tipo) VALUES(?,?,?)",(int(tr.id),two_id,'principal2'))
        log(st.session_state.user['email'],f'Atualizou distribuição do trabalho {code}')
        st.success('Atribuições atualizadas. Avaliações já enviadas foram preservadas.')
        st.rerun()
    st.subheader('Distribuição atual')
    st.dataframe(df("""SELECT t.codigo,t.area,t.titulo,u.nome,u.email,a.tipo,CASE WHEN EXISTS(SELECT 1 FROM avaliacoes x WHERE x.trabalho_id=a.trabalho_id AND x.avaliador_id=a.avaliador_id AND x.tipo=a.tipo) THEN 'Avaliação enviada' ELSE 'Pendente' END AS status FROM atribuicoes a JOIN trabalhos t ON t.id=a.trabalho_id JOIN users u ON u.id=a.avaliador_id ORDER BY t.area,CAST(t.codigo AS INTEGER),t.codigo,a.tipo"""),width='stretch',hide_index=True)
def assigned(uid):
    d=df('''SELECT t.*,a.tipo FROM atribuicoes a JOIN trabalhos t ON t.id=a.trabalho_id WHERE a.avaliador_id=?''',(uid,))
    return _sort_codes(d) if not d.empty else d

def page_evaluator():
    u=st.session_state.user; st.title('Meus trabalhos'); d=assigned(u['id']); done=df('SELECT trabalho_id FROM avaliacoes WHERE avaliador_id=?',(u['id'],)); doneids=set(done.trabalho_id.tolist())
    a,b,c=st.columns(3); a.metric('Atribuídos',len(d)); b.metric('Concluídos',len(doneids)); c.metric('Pendentes',len(d)-len(doneids))
    if d.empty: st.info('Não há trabalhos atribuídos a você.'); return
    pend_codes=set(d.loc[~d.id.isin(doneids),'codigo'].astype(str).tolist())
    if pend_codes:
        st.markdown('<div style="background:#fff1df;border-left:5px solid #f39c12;padding:8px 12px;border-radius:6px;margin:4px 0 12px 0;color:#7a4a00"><b>🟠 Pendentes de avaliação</b> - os trabalhos pendentes estão identificados com o marcador laranja na lista.</div>',unsafe_allow_html=True)
    labels=[]
    for _,rr in d.iterrows():
        c=str(rr['codigo']); prefix='🟠 PENDENTE · ' if c in pend_codes else '✓ CONCLUÍDO · '
        labels.append(f'{prefix}{c} - {rr["titulo"]}')
    selected=st.selectbox('Selecione um trabalho',labels)
    selected_code=selected.split(' · ',1)[1].split(' - ',1)[0] if ' · ' in selected else selected.split(' - ',1)[0]
    code=selected_code; tr=d[d.codigo.astype(str)==str(code)].iloc[0]
    st.subheader(f'{tr.codigo} - {tr.titulo}'); st.caption(f'Área: {tr.area} · Papel: {"Terceiro avaliador" if tr.tipo=="terceiro" else "Avaliador principal"}')
    with st.expander('Resumo do trabalho',expanded=True):
        st.write(tr.resumo or 'Resumo não informado.'); nomes_pdf=[]
        if tr.arquivo and str(tr.arquivo).strip(): nomes_pdf.append(Path(str(tr.arquivo)).name)
        nomes_pdf.append(f'{tr.codigo}.pdf'); pdf_path=next((PDF_DIR/n for n in dict.fromkeys(nomes_pdf) if (PDF_DIR/n).is_file()),None)
        if pdf_path is not None:
            pdf_bytes=pdf_path.read_bytes(); st.markdown('**Visualização do PDF**')
            try: st.pdf(pdf_bytes,height=760)
            except AttributeError:
                encoded=base64.b64encode(pdf_bytes).decode('ascii'); components.html(f'<object data="data:application/pdf;base64,{encoded}" type="application/pdf" width="100%" height="760"><p>Use o botão abaixo para baixar.</p></object>',height=780,scrolling=True)
            st.download_button('Baixar PDF do trabalho',pdf_bytes,file_name=pdf_path.name,mime='application/pdf')
        else: st.warning('PDF ainda não disponibilizado pela coordenação.')
    if int(tr.id) in doneids: st.success('Sua avaliação já foi enviada.'); return
    st.subheader('Ficha de avaliação'); vals=[]
    for i,(name,weight) in enumerate(CRITERIOS): vals.append(st.number_input(f'{i+1}. {name} - peso {weight:.0%}',min_value=0.0,max_value=10.0,value=0.0,step=0.1,format='%.1f',key=f'n_{u["id"]}_{tr.id}_{i}'))
    nota=sum(v*w for v,(_,w) in zip(vals,CRITERIOS)); st.metric('Nota calculada',f'{nota:.2f}')
    com=st.text_area('Comentário (Obrigatório)',placeholder='Justifique brevemente a avaliação.')
    recomendacao=st.selectbox('Recomendação',RECOMENDACOES)
    if st.button('Enviar avaliação',type='primary'):
        if not com.strip(): st.error('O comentário é obrigatório para enviar a avaliação.')
        else:
            q('INSERT INTO avaliacoes(trabalho_id,avaliador_id,tipo,n1,n2,n3,n4,n5,nota,comentario,recomendacao,enviada_em) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(int(tr.id),u['id'],tr.tipo,*vals,round(nota,2),com.strip(),recomendacao,now()))
            log(u['email'],f'Enviou avaliação do trabalho {code}'); st.success('Avaliação enviada e bloqueada para edição.'); st.rerun()

def page_discrep():
    st.title('Discrepâncias e terceiro avaliador')
    d=df('''SELECT t.id,t.codigo,t.area,t.titulo,MAX(CASE WHEN a.tipo IN ('principal','principal2') THEN a.nota END) maxn,MIN(CASE WHEN a.tipo IN ('principal','principal2') THEN a.nota END) minn,COUNT(CASE WHEN a.tipo IN ('principal','principal2') THEN 1 END) qtd,(SELECT COUNT(*) FROM avaliacoes x WHERE x.trabalho_id=t.id AND x.tipo='terceiro') terceiro FROM trabalhos t LEFT JOIN avaliacoes a ON a.trabalho_id=t.id GROUP BY t.id''')
    if d.empty: st.info('Nenhum trabalho.'); return
    d['diferença']=d.apply(lambda r:round(r.maxn-r.minn,2) if r.qtd>=2 else None,axis=1); d['necessita']=d.apply(lambda r:r.qtd>=2 and r.diferença>4 and r.terceiro==0,axis=1)
    st.dataframe(d[['codigo','area','titulo','qtd','diferença','terceiro','necessita']].rename(columns={'codigo':'Código','area':'Área','titulo':'Título','qtd':'Avaliações principais','terceiro':'Terceiro atribuído','necessita':'Necessita terceiro'}),width='stretch',hide_index=True)
    cand=d[d.necessita]
    if cand.empty: st.success('Não há discrepâncias pendentes.'); return
    u=df("SELECT id,nome,email FROM users WHERE perfil='avaliador' AND ativo=1"); principals=df("SELECT trabalho_id,avaliador_id FROM atribuicoes WHERE tipo IN ('principal','principal2')")
    for _,r in cand.iterrows():
        st.markdown(f"**{r.codigo} - {r.titulo}** | diferença: **{r['diferença']:.2f}**"); used=set(principals.loc[principals.trabalho_id==r.id,'avaliador_id'].tolist()); u3=u[~u.id.isin(used)]; opts={f'{x.nome} - {x.email}':int(x.id) for _,x in u3.iterrows()}
        if not opts: st.warning('Não há avaliadores disponíveis diferentes dos dois principais.'); continue
        choice=st.selectbox('Terceiro avaliador',list(opts),key=f't_{r.id}')
        if st.button('Atribuir terceiro avaliador',key=f'b_{r.id}',type='primary'):
            q("INSERT OR IGNORE INTO atribuicoes(trabalho_id,avaliador_id,tipo) VALUES(?,?,?)",(int(r.id),opts[choice],'terceiro')); log(st.session_state.user['email'],f'Atribuiu terceiro avaliador ao trabalho {r.codigo}'); st.success('Terceiro avaliador atribuído.'); st.rerun()

def _results_table():
    ev=df('''SELECT t.id,t.codigo,t.nomes,t.area,t.titulo,a.id avaliacao_id,a.tipo,a.avaliador_id,u.nome avaliador,a.n1,a.n2,a.n3,a.n4,a.n5,a.nota,a.comentario,a.recomendacao,a.enviada_em FROM trabalhos t JOIN avaliacoes a ON a.trabalho_id=t.id JOIN users u ON u.id=a.avaliador_id ORDER BY t.area,CAST(t.codigo AS INTEGER),t.codigo,a.id''')
    if ev.empty: return pd.DataFrame()
    rows=[]
    for tid,g in ev.groupby('id',sort=False):
        base=g.iloc[0]; vals=g['nota'].dropna().tolist(); final=round(sum(vals)/len(vals),2) if vals else pd.NA
        crit=[float(g[f'n{i}'].mean()) for i in range(1,6)]
        rec={ 'id':int(tid),'codigo':base['codigo'],'nomes':base['nomes'],'area':base['area'],'titulo':base['titulo'],'Nota avaliador 1':pd.NA,'Nota avaliador 2':pd.NA,'Nota terceiro':pd.NA,'Nota final':final,
              'Critério 1':crit[0],'Critério 2':crit[1],'Critério 3':crit[2],'Critério 4':crit[3],'Critério 5':crit[4] }
        for _,r in g.iterrows():
            if r['tipo']=='principal': rec['Nota avaliador 1']=r['nota']
            elif r['tipo']=='principal2': rec['Nota avaliador 2']=r['nota']
            elif r['tipo']=='terceiro': rec['Nota terceiro']=r['nota']
        rows.append(rec)
    out=pd.DataFrame(rows)
    out=out[out['Nota final'].notna()].copy()
    # Desempate: critério 4, depois 3, 1, 2 e 5.
    out['_area']=out['area'].fillna('').astype(str); out['_code']=out['codigo'].fillna('').astype(str)
    out=out.sort_values(['_area','Nota final','Critério 4','Critério 3','Critério 1','Critério 2','Critério 5','_code'],ascending=[True,False,False,False,False,False,False,True],kind='stable')
    # Empates exatos em todos os critérios recebem a mesma posição. A posição seguinte
    # considera apenas a próxima combinação distinta (ex.: 1º, 1º, 2º).
    keys=['Nota final','Critério 4','Critério 3','Critério 1','Critério 2','Critério 5']
    positions=[]
    for _,g in out.groupby('area',dropna=False,sort=False):
        last=None; pos=0
        for _,rr in g.iterrows():
            key=tuple(None if pd.isna(rr[k]) else float(rr[k]) for k in keys)
            if key != last:
                pos += 1; last=key
            positions.append((rr['id'],pos))
    posmap=dict(positions); out['Posição']=out['id'].map(posmap).astype(int)
    out['Resultado']=out['Posição'].apply(lambda x:'Premiado' if x<=3 else ('Suplente' if x<=5 else ''))
    return out.drop(columns=['_area','_code'])

def page_results():
    st.title('Resultados finais')
    st.caption('Somente trabalhos com pelo menos uma avaliação entram na classificação. O desempate segue: critério 4 → 3 → 1 → 2 → 5.')
    piv=_results_table()
    if piv.empty: st.info('Ainda não há avaliações.'); return
    areas=['Todas as áreas']+sorted(piv.area.dropna().unique().tolist(),key=lambda x:str(x).lower()); escolha=st.selectbox('Selecionar área',areas)
    view=piv if escolha=='Todas as áreas' else piv[piv.area==escolha]
    display_cols=['Posição','codigo','titulo','Nota avaliador 1','Nota avaliador 2','Nota terceiro','Nota final','Resultado']
    tab1,tab2=st.tabs(['Por área','Classificação geral'])
    with tab1:
        if escolha=='Todas as áreas':
            for area_name,g in piv.groupby('area',sort=True):
                st.markdown(f'#### {_area_label(area_name)}'); st.dataframe(g[display_cols].rename(columns={'codigo':'Código','titulo':'Título'}),width='stretch',hide_index=True)
        else: st.dataframe(view[display_cols].rename(columns={'codigo':'Código','titulo':'Título'}),width='stretch',hide_index=True)
    with tab2: st.dataframe(view[['area']+display_cols].rename(columns={'area':'Área','codigo':'Código','titulo':'Título'}),width='stretch',hide_index=True)
    xbuf=io.BytesIO()
    with pd.ExcelWriter(xbuf,engine='openpyxl') as writer:
        for area_name,g in piv.groupby('area',sort=True):
            sheet=_safe_filename(area_name)[:31] or 'Sem area'; g[display_cols+['Critério 4','Critério 3','Critério 1','Critério 2','Critério 5']].rename(columns={'codigo':'Código','titulo':'Título'}).to_excel(writer,index=False,sheet_name=sheet)
        piv.to_excel(writer,index=False,sheet_name='Classificação geral')
    st.download_button('Exportar resultados Excel',xbuf.getvalue(),'resultados_ufrr.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

def _pdf_bytes(title,subtitle,lines,logos=False):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib.enums import TA_CENTER,TA_JUSTIFY
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image as RLImage,KeepTogether
    from reportlab.lib.units import cm
    from xml.sax.saxutils import escape
    buf=io.BytesIO(); doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=42,leftMargin=42,topMargin=38,bottomMargin=42)
    styles=getSampleStyleSheet(); story=[]
    if logos:
        paths=[BASE/'assets'/'brasao_ufrr.png',BASE/'assets'/'IFRR Horizontal_1-Cores.png',BASE/'assets'/'logo-uerr2.png',BASE/'assets'/'hu_ufrr.png']
        cells=[]
        for p in paths:
            if p.exists():
                im=RLImage(str(p),width=3.3*cm,height=1.8*cm); cells.append(im)
            else: cells.append('')
        t=Table([cells],colWidths=[4.1*cm]*4); t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ALIGN',(0,0),(-1,-1),'CENTER'),('LEFTPADDING',(0,0),(-1,-1),2),('RIGHTPADDING',(0,0),(-1,-1),2)])); story.append(t); story.append(Spacer(1,12))
    story.append(Paragraph(escape(title),ParagraphStyle('T',parent=styles['Title'],alignment=TA_CENTER,textColor=colors.HexColor('#0b3b60'),fontSize=18,leading=22)))
    story.append(Spacer(1,8)); story.append(Paragraph(escape(subtitle),ParagraphStyle('S',parent=styles['Normal'],alignment=TA_CENTER,fontSize=9,textColor=colors.HexColor('#60758a')))); story.append(Spacer(1,16))
    for item in lines:
        if isinstance(item,(list,tuple)):
            # item can be a table matrix
            matrix=[]
            for rr in item:
                matrix.append([Paragraph(escape(str(x)),styles['Normal']) for x in rr])
            t=Table(matrix,repeatRows=1); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dcecf9')),('TEXTCOLOR',(0,0),(-1,0),colors.HexColor('#0b3b60')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#b7d4ec')),('VALIGN',(0,0),(-1,-1),'TOP'),('FONTSIZE',(0,0),(-1,-1),8),('PADDING',(0,0),(-1,-1),6)])); story.append(t)
        else: story.append(Paragraph(str(item),styles['Normal']))
        story.append(Spacer(1,8))
    doc.build(story); return buf.getvalue()

def _comment_pdf(records):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,KeepTogether,Table,TableStyle
    from xml.sax.saxutils import escape
    if isinstance(records, dict): records=[records]
    records=list(records)
    first=records[0] if records else {}
    buf=io.BytesIO(); doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=48,leftMargin=48,topMargin=48,bottomMargin=48)
    styles=getSampleStyleSheet(); story=[]
    story.append(Paragraph('Notas e comentários da avaliação',ParagraphStyle('T',parent=styles['Title'],alignment=TA_CENTER,textColor=colors.HexColor('#0b3b60'),fontSize=18)))
    story.append(Spacer(1,12))
    story.append(Paragraph(f'<b>{escape(str(first.get("titulo", "")))}</b>',ParagraphStyle('H',parent=styles['Heading2'],alignment=TA_CENTER,textColor=colors.HexColor('#17324d'),fontSize=13)))
    story.append(Spacer(1,16))
    for i,r in enumerate(records,1):
        bloco=[Paragraph(f'<b>Avaliador {i}</b>',styles['Heading3'])]
        rows=[]
        for j,(name,weight) in enumerate(CRITERIOS,1):
            val=r.get(f'n{j}')
            valtxt='-' if val is None or pd.isna(val) else f'{float(val):.1f}'
            rows.append([f'{j}. {name}', f'{valtxt} (peso {weight:.0%})'])
        final=r.get('nota'); finaltxt='-' if final is None or pd.isna(final) else f'{float(final):.2f}'
        rows.append(['Nota final', finaltxt])
        tab=Table([[Paragraph('<b>Critério</b>',styles['BodyText']),Paragraph('<b>Nota</b>',styles['BodyText'])]]+[[Paragraph(escape(str(a)),styles['BodyText']),Paragraph(escape(str(b)),styles['BodyText'])] for a,b in rows],colWidths=[350,100])
        tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dcecf9')),('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#b7d4ec')),('VALIGN',(0,0),(-1,-1),'TOP'),('ALIGN',(1,1),(1,-1),'CENTER'),('PADDING',(0,0),(-1,-1),5)]))
        recomendacao=str(r.get('recomendacao') or '').strip()
        bloco += [tab,Spacer(1,8),Paragraph(f'<b>Recomendação:</b> {escape(recomendacao) if recomendacao else "-"}',styles['BodyText']),Spacer(1,8),Paragraph('<b>Comentário</b>',styles['BodyText'])]
        comentario=str(r.get('comentario') or '').strip()
        bloco.append(Paragraph(escape(comentario) if comentario else 'Nenhum comentário registrado.',styles['BodyText']))
        bloco.append(Spacer(1,14))
        story.append(KeepTogether(bloco))
    doc.build(story); return buf.getvalue()

def _certificate_pdf(r, config, kind='premiacao'):
    """Gera o certificado sobre a moldura limpa fornecida pelo evento.

    O mesmo PDF-base é usado para apresentação e premiação. Como a moldura
    não contém campos de exemplo, nada é apagado do template; o código apenas
    acrescenta os dados variáveis.
    """
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.utils import ImageReader
    from pypdf import PdfReader, PdfWriter
    from PIL import Image
    from xml.sax.saxutils import escape

    # A mesma moldura limpa é utilizada nos dois tipos de certificado.
    template = TEMPLATE_PREMIO if kind == 'premiacao' else TEMPLATE_PARTICIPACAO
    if not template.exists():
        # fallback para o arquivo-base único
        template = BASE/'assets'/'certificado.pdf'
    if not template.exists():
        raise FileNotFoundError('Modelo limpo de certificado não encontrado.')

    reader = PdfReader(str(template))
    page = reader.pages[0]
    W = float(page.mediabox.width)
    H = float(page.mediabox.height)

    ov = io.BytesIO()
    c = canvas.Canvas(ov, pagesize=(W, H))
    blue = colors.HexColor('#064de8')

    nomes_raw = str(r.get('nomes', '') or '').replace('\n', ';')
    autores = [x.strip() for x in nomes_raw.split(';') if x.strip()]
    multi = len(autores) > 1
    nomes = _author_text(nomes_raw)

    # Nome(s) dos autores. A moldura limpa não possui texto nessa região.
    nsize = 18 if len(nomes) <= 55 else (16 if len(nomes) <= 75 else 14)
    pn = Paragraph(
        escape(nomes),
        ParagraphStyle(
            'CERT_NOME_NEW', fontName='Times-Bold', fontSize=nsize,
            leading=nsize+2, textColor=blue, alignment=TA_CENTER))
    pn.wrapOn(c, 620, 55)
    # Linha horizontal do campo de nomes, seguindo a moldura original.
    c.setStrokeColor(blue)
    c.setLineWidth(2.2)
    c.line(179.1, 360.86, 677.21, 360.86)
    pn.drawOn(c, 110, 374)

    # Texto central.
    area = _area_label(r.get('area', ''))
    dr = _date_range_pt(config.get('data_inicio', ''), config.get('data_fim', ''))
    if kind == 'premiacao':
        verbo = 'foram premiados' if multi else 'foi premiado'
        lugar = f"{int(r['Posição'])}º Lugar"
        texto = (
            f"{verbo} em <b>{escape(lugar)}</b> na área <b>{escape(area)}</b>, "
            f"no <b>Encontro de Iniciação Científica de Roraima</b>, realizado "
            f"entre os dias {escape(dr)}, na Universidade Federal de Roraima."
        )
    else:
        verbo = 'apresentaram' if multi else 'apresentou'
        titulo = str(r.get('titulo', '') or '').strip()
        texto = (
            f"{verbo} o trabalho <b>{escape(titulo)}</b>, no "
            f"<b>Encontro de Iniciação Científica de Roraima</b>, realizado "
            f"entre os dias {escape(dr)}, na Universidade Federal de Roraima."
        )
    pb = Paragraph(
        texto,
        ParagraphStyle(
            'CERT_BODY_NEW', fontName='Helvetica', fontSize=13.2,
            leading=18, textColor=blue, alignment=TA_CENTER))
    # Caixa de texto deliberadamente mais estreita (15%) para evitar que
    # textos longos invadam as áreas laterais da moldura.
    body_w = 646  # 760 * 0.85
    body_x = (W - body_w) / 2
    pb.wrapOn(c, body_w, 110)
    pb.drawOn(c, body_x, 286)

    # Assinaturas: quatro linhas rigorosamente iguais.
    # Subimos ligeiramente o conjunto e mantemos espaço confortável para a data.
    slots = [
        (179.1, 215.0, 424.1, config.get('prof1_nome',''), config.get('prof1_cargo',''), config.get('prof1_assinatura','')),
        (442.61, 215.0, 687.61, config.get('prof2_nome',''), config.get('prof2_cargo',''), config.get('prof2_assinatura','')),
        (179.1, 135.0, 424.1, config.get('prof3_nome',''), config.get('prof3_cargo',''), config.get('prof3_assinatura','')),
        (442.61, 135.0, 687.61, config.get('prof4_nome',''), config.get('prof4_cargo',''), config.get('prof4_assinatura','')),
    ]
    for x0, yline, x1, nome, cargo, sigrel in slots:
        c.setStrokeColor(blue)
        c.setLineWidth(2.2)
        c.line(x0, yline, x1, yline)

        if sigrel:
            sp = BASE / sigrel
            if sp.exists():
                try:
                    im = Image.open(sp).convert('RGBA')
                    iw, ih = im.size
                    maxw = x1-x0-12
                    maxh = 34
                    scale = min(maxw/iw, maxh/ih)
                    sw, sh = iw*scale, ih*scale
                    c.drawImage(
                        ImageReader(im), x0+(x1-x0-sw)/2,
                        yline+2+(maxh-sh)/2,
                        width=sw, height=sh, mask='auto',
                        preserveAspectRatio=True)
                except Exception:
                    pass

        # Nomes dos signatários com fonte maior.
        ps = ParagraphStyle(
            'CERT_SIGN_NAME_NEW', fontName='Times-Bold', fontSize=11.2,
            leading=13, textColor=blue, alignment=TA_CENTER)
        pc = ParagraphStyle(
            'CERT_SIGN_CARGO_NEW', fontName='Helvetica', fontSize=9.0,
            leading=10.5, textColor=blue, alignment=TA_CENTER)
        qn = Paragraph(escape(str(nome or '')), ps)
        qn.wrapOn(c, x1-x0, 18)
        qn.drawOn(c, x0, yline-19)
        qc = Paragraph(escape(str(cargo or '')), pc)
        qc.wrapOn(c, x1-x0, 15)
        qc.drawOn(c, x0, yline-34)

    # Data de emissão: preenchida automaticamente no momento da geração do
    # certificado. Não é escolhida pelo usuário e não usa as datas do evento.
    # Usamos o fuso de Roraima para que a data seja coerente mesmo se o servidor
    # Oracle estiver configurado em UTC.
    from zoneinfo import ZoneInfo
    data_emissao = datetime.now(ZoneInfo('America/Boa_Vista')).date()
    meses_emissao=['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro']
    data_emissao_pt = f"{data_emissao.day} de {meses_emissao[data_emissao.month-1]} de {data_emissao.year}"
    c.setFillColor(blue)
    c.setFont('Helvetica', 10.0)
    c.drawCentredString(W/2, 83.0, f"{config.get('local') or 'Boa Vista/RR'}, {data_emissao_pt}.")

    c.save()
    ov.seek(0)
    op = PdfReader(ov)
    page.merge_page(op.pages[0])
    out = PdfWriter()
    out.add_page(page)
    result = io.BytesIO()
    out.write(result)
    return result.getvalue()

def _zip_files(items):
    import zipfile
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in items: z.writestr(name,data)
    return buf.getvalue()

def _certificate_settings_ui(key_suffix):
    cfg=_cert_config()
    st.subheader('Configuração dos certificados')
    with st.form(f'config_certificados_{key_suffix}'):
        d1=st.date_input('Data inicial do evento',datetime.strptime(cfg['data_inicio'],'%Y-%m-%d').date() if cfg.get('data_inicio') else datetime.now().date(),key=f'd1_{key_suffix}')
        d2=st.date_input('Data final do evento',datetime.strptime(cfg['data_fim'],'%Y-%m-%d').date() if cfg.get('data_fim') else datetime.now().date(),key=f'd2_{key_suffix}')
        local=st.text_input('Local',cfg.get('local') or 'Boa Vista/RR',key=f'local_{key_suffix}')
        prof=[]
        for i in range(1,5):
            a,b=st.columns(2)
            prof.append((a.text_input(f'Professor {i} - Nome',cfg.get(f'prof{i}_nome',''),key=f'cn{i}_{key_suffix}'),b.text_input(f'Professor {i} - Cargo',cfg.get(f'prof{i}_cargo',''),key=f'cc{i}_{key_suffix}')))
        salvar=st.form_submit_button('Salvar dados dos certificados',type='primary')
    if salvar:
        args=[]
        for n,cargo in prof: args.extend([n.strip(),cargo.strip()])
        args.extend([d1.strftime('%Y-%m-%d'),d2.strftime('%Y-%m-%d'),local.strip() or 'Boa Vista/RR'])
        q("UPDATE certificado_config SET prof1_nome=?,prof1_cargo=?,prof2_nome=?,prof2_cargo=?,prof3_nome=?,prof3_cargo=?,prof4_nome=?,prof4_cargo=?,data_inicio=?,data_fim=?,local=? WHERE id=1",tuple(args))
        log(st.session_state.user['email'],'Atualizou configuração dos certificados')
        st.success('Dados dos certificados salvos.')
        st.rerun()
    cfg=_cert_config()
    st.write('**Assinaturas**')
    for i in range(1,5):
        up=st.file_uploader(f'Upload da assinatura do Professor {i}',type=['png','jpg','jpeg','webp'],key=f'sig{i}_{key_suffix}')
        if up is not None:
            rel=_save_signature(up,i)
            q(f'UPDATE certificado_config SET prof{i}_assinatura=? WHERE id=1',(rel,))
            cfg[f'prof{i}_assinatura']=rel
            st.success(f'Assinatura do Professor {i} salva.')
        if cfg.get(f'prof{i}_assinatura') and (BASE/cfg[f'prof{i}_assinatura']).exists():
            st.caption(f"Assinatura cadastrada: {Path(cfg[f'prof{i}_assinatura']).name}")
    return _cert_config()

def page_reports():
    st.title('Relatórios e documentos oficiais')
    st.caption('Relatórios, notas e comentários das avaliações, certificados de premiação e certificados gerais de apresentação.')
    piv=_results_table()
    all_ev=df("""SELECT t.id AS trabalho_id,t.codigo,t.nomes,t.area,t.titulo,t.arquivo,a.id AS avaliacao_id,a.tipo,a.nota,a.n1,a.n2,a.n3,a.n4,a.n5,a.comentario,a.recomendacao,a.enviada_em,u.nome avaliador FROM trabalhos t JOIN avaliacoes a ON a.trabalho_id=t.id JOIN users u ON u.id=a.avaliador_id ORDER BY t.area,CAST(t.codigo AS INTEGER),t.codigo,a.id""")
    tipo=st.radio('Documento',['Relatório geral','Relatório por área','Notas e comentários','Comentários em PDF','Certificados de premiação','Certificados de apresentação'],horizontal=True)
    if tipo in ('Relatório geral','Relatório por área'):
        if piv.empty: st.info('Ainda não existem avaliações.'); return
        if tipo=='Relatório geral': g=piv; nome='relatorio_geral.pdf'
        else:
            area=st.selectbox('Área',sorted(piv.area.dropna().unique().tolist(),key=lambda x:str(x).lower())); g=piv[piv.area==area]; nome=f'resultados_{_safe_filename(area)}.pdf'
        linhas=[['Posição','Área','Código','Título','Av. 1','Av. 2','Terceiro','Nota final','Resultado']]
        for _,r in g.iterrows(): linhas.append([str(r['Posição']),_area_label(r['area']),str(r['codigo']),str(r['titulo'])[:55],str(r['Nota avaliador 1'] if pd.notna(r['Nota avaliador 1']) else '-'),str(r['Nota avaliador 2'] if pd.notna(r['Nota avaliador 2']) else '-'),str(r['Nota terceiro'] if pd.notna(r['Nota terceiro']) else '-'),str(r['Nota final']),str(r['Resultado'])])
        data=_pdf_bytes('Relatório de resultados','Plataforma de Avaliação de Resumos - UFRR',[linhas]); st.download_button('Gerar PDF',data,nome,'application/pdf')
    elif tipo=='Notas e comentários':
        if all_ev.empty: st.info('Ainda não há avaliações.'); return
        cols=['codigo','area','titulo','avaliador','tipo','nota','recomendacao','comentario']; view=all_ev[cols].rename(columns={'codigo':'Código','area':'Área','titulo':'Título','avaliador':'Avaliador','tipo':'Tipo','nota':'Nota final do avaliador','recomendacao':'Recomendação','comentario':'Comentário'})
        st.dataframe(view,width='stretch',hide_index=True); st.download_button('Exportar notas e comentários (Excel)',_excel_bytes(view,'Notas e comentários'),'notas_comentarios.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    elif tipo=='Comentários em PDF':
        if all_ev.empty: st.info('Ainda não há comentários.'); return
        selected=st.selectbox('Selecione o trabalho',all_ev.apply(lambda r:f"{r['codigo']} - {r['titulo']}",axis=1).drop_duplicates().tolist())
        subset=all_ev[all_ev.apply(lambda r:f"{r['codigo']} - {r['titulo']}"==selected,axis=1)].copy()
        subset['_ord']=subset['tipo'].map({'principal':1,'principal2':2,'terceiro':3}).fillna(9)
        subset=subset.sort_values(['_ord','avaliacao_id']).drop(columns=['_ord'])
        data=_comment_pdf([row for _,row in subset.iterrows()]); base=_safe_filename(Path(str(subset.iloc[0]['arquivo'])).stem if str(subset.iloc[0].get('arquivo','')).strip() else subset.iloc[0]['codigo']); st.download_button('Baixar comentários em PDF',data,f'{base} _ comentario.pdf','application/pdf')
        items=[]
        for _,grp in all_ev.groupby(['codigo','titulo'],sort=False):
            grp=grp.copy(); grp['_ord']=grp['tipo'].map({'principal':1,'principal2':2,'terceiro':3}).fillna(9); grp=grp.sort_values(['_ord','avaliacao_id']).drop(columns=['_ord']); rr=grp.iloc[0]; base=_safe_filename(Path(str(rr.get('arquivo',''))).stem if str(rr.get('arquivo','')).strip() else rr['codigo']); items.append((f'{base} _ comentario.pdf',_comment_pdf([row for _,row in grp.iterrows()])))
        st.download_button('Gerar todos os comentários (ZIP)',_zip_files(items),'comentarios_avaliacoes.zip','application/zip')
    elif tipo=='Certificados de premiação':
        if piv.empty: st.info('Ainda não há resultados.'); return
        cfg=_certificate_settings_ui('premiacao')
        premiados=piv[piv.Resultado=='Premiado'].copy()
        st.write(f'{len(premiados)} certificado(s) de premiação serão disponibilizados.')
        if premiados.empty: st.info('Não há premiados no momento.'); return
        items=[]
        for _,r in premiados.iterrows():
            items.append((f"{_safe_filename(r['codigo'])} - {_safe_filename(_author_text(r['nomes']))} - {int(r['Posição'])} lugar.pdf",_certificate_pdf(r,cfg,'premiacao')))
        st.download_button('Gerar todos os certificados de premiação (ZIP)',_zip_files(items),'certificados_premiacao.zip','application/zip')
        sel=st.selectbox('Certificado individual',[f"{i}. {r['codigo']} - {r['titulo']} - {int(r['Posição'])}º lugar" for i,(_,r) in enumerate(premiados.iterrows(),1)])
        rr=premiados.iloc[premiados.apply(lambda r:f"{r['codigo']} - {r['titulo']} - {int(r['Posição'])}º lugar"==sel.split('. ',1)[1],axis=1).idxmax()]
        st.download_button('Baixar certificado selecionado',_certificate_pdf(rr,cfg,'premiacao'),f"certificado_{_safe_filename(rr['codigo'])}.pdf",'application/pdf')
    else:
        works=df('SELECT id,codigo,nomes,area,titulo FROM trabalhos ORDER BY id ASC')
        if works.empty: st.info('Ainda não há trabalhos cadastrados.'); return
        cfg=_certificate_settings_ui('participacao')
        st.write('Os certificados de apresentação seguem o modelo fornecido e usam os mesmos dados do evento e assinaturas.')
        items=[(f"{_safe_filename(r['codigo'])} - participacao.pdf",_certificate_pdf(r,cfg,'participacao')) for _,r in works.iterrows()]
        st.download_button('Gerar todos os certificados de apresentação (ZIP)',_zip_files(items),'certificados_participacao.zip','application/zip')
        sel=st.selectbox('Certificado individual de apresentação',[f"{i}. {r['codigo']} - {r['titulo']}" for i,(_,r) in enumerate(works.iterrows(),1)])
        rr=works.iloc[works.apply(lambda r:f"{r['codigo']} - {r['titulo']}"==sel.split('. ',1)[1],axis=1).idxmax()]
        st.download_button('Baixar certificado selecionado',_certificate_pdf(rr,cfg,'participacao'),f"certificado_participacao_{_safe_filename(rr['codigo'])}.pdf",'application/pdf')
def _excel_bytes(data,sheet='Dados'):
    buf=io.BytesIO()
    with pd.ExcelWriter(buf,engine='openpyxl') as writer: data.to_excel(writer,index=False,sheet_name=sheet[:31])
    return buf.getvalue()

def render_footer():
    st.markdown('<div class="app-footer"><strong>Aviso:</strong> esta não é uma página oficial nem é gerenciada pela UFRR. O conteúdo é de responsabilidade de seus idealizadores. PRPPG-UFRR.<br>Ferramenta destinada ao processo de avaliação de resumos científicos.</div>', unsafe_allow_html=True)
def page_subcoordenadores():
    st.title('Subcoordenadores')
    if st.session_state.user.get('perfil') != 'master':
        st.error('Somente o coordenador master pode adicionar subcoordenadores.')
        return
    st.caption('Subcoordenadores possuem as permissões da coordenação, exceto criar outros subcoordenadores.')
    with st.form('novo_subcoord'):
        nome=st.text_input('Nome completo')
        email=st.text_input('E-mail')
        senha=st.text_input('Senha inicial',type='password')
        ok=st.form_submit_button('Adicionar subcoordenador',type='primary')
    if ok:
        if not nome.strip() or not email.strip() or len(senha)<6:
            st.error('Informe nome, e-mail e uma senha inicial com pelo menos 6 caracteres.')
        else:
            try:
                q("INSERT INTO users(nome,email,perfil,senha,ativo,tipo_autenticacao,deve_trocar_senha) VALUES(?,?,?,?,1,'local',1)",(nome.strip(),email.strip().lower(),'coord',pw(senha)))
                st.success('Subcoordenador criado.')
                st.rerun()
            except Exception as e: st.error(f'Não foi possível criar a conta: {e}')
    st.subheader('Subcoordenadores cadastrados')
    st.dataframe(df("SELECT nome,email,CASE WHEN ativo=1 THEN 'Ativo' ELSE 'Bloqueado' END AS status FROM users WHERE perfil='coord' ORDER BY nome"),hide_index=True,width='stretch')

def _set_flash(message, kind='success'):
    st.session_state['_flash_message'] = message
    st.session_state['_flash_kind'] = kind

def _show_flash():
    msg = st.session_state.pop('_flash_message', None)
    kind = st.session_state.pop('_flash_kind', 'success')
    if msg:
        if kind == 'error': st.error(msg)
        elif kind == 'warning': st.warning(msg)
        else: st.success(msg)

def main():
    init_db()
    _show_flash()
    if 'user' not in st.session_state:
        login()
        render_footer()
        return
    header(); u=st.session_state.user
    if u.get('deve_trocar_senha'):
        st.warning('Por segurança, altere sua senha inicial antes de acessar os demais recursos.')
        page_profile()
        render_footer()
        return
    if u['perfil'] in ('coord','master'):
        items=['Painel','Avaliadores','Resumos','Trabalhos','Distribuição de trabalhos','Discrepâncias','Resultados','Relatórios e documentos','Subcoordenadores','Meu Perfil','Sair']
        menu=sidebar(items)
        routes={'Painel':page_dashboard,'Avaliadores':page_users,'Resumos':page_import,'Trabalhos':page_trabalhos,'Distribuição de trabalhos':page_distribution,'Discrepâncias':page_discrep,'Resultados':page_results,'Relatórios e documentos':page_reports,'Subcoordenadores':page_subcoordenadores,'Meu Perfil':page_profile}
        routes[menu]()
    else:
        menu=sidebar(['Meus trabalhos','Meu Perfil','Sair'])
        if menu == 'Meu Perfil': page_profile()
        elif menu == 'Sair': pass
        else: page_evaluator()
    render_footer()

if __name__=='__main__': main()
