# numrecon

Self-OSINT para o **seu próprio** número de telefone. Analisa prefixo, país,
tipo (móvel/fixo) e região (DDD → UF/cidade no Brasil) **100% offline**, e
opcionalmente checa em quais plataformas o número está registrado.

> ⚠️ Uso ético: só para o seu próprio número/contas. A checagem em plataformas
> usa APIs oficiais com **suas** credenciais e respeita rate limits. Não faça
> enumeração de números de terceiros (viola ToS e leis de privacidade).

## Instalação

```bash
cd ~/AI/projects/numrecon
pip install -e .
# opcional, para checar Telegram:
pip install -e ".[telegram]"
```

## Uso

```bash
# Análise offline (país / tipo / região)
numrecon 11999998888
numrecon "+351912345678"
numrecon "(11) 99999-8888"

# Também checar registro em plataformas
numrecon 11999998888 --platforms

# Saída JSON (útil pra pipeline)
numrecon 11999998888 --json

# Smoke test interno
numrecon --self-test
```

### Telegram (opcional) — retorna nome + @username

1. Crie um app em https://my.telegram.org (api_id, api_hash).
2. Exporte como variáveis de ambiente e rode:

```bash
export TG_API_ID=seu_id
export TG_API_HASH=seu_hash
numrecon 11999998888 --platforms
```

A checagem usa `contacts.importContacts` (API oficial) e, para o seu número,
devolve **nome + @username da conta vinculada** — auto-auditoria legítima.
Nunca faz spam nem contorna captcha. Na primeira execução você faz login.

### WhatsApp / Instagram — checklist manual (sem automação)

Não há API oficial de lookup por telefone. Automatizar vira enumeração de
terceiros (viola ToS). O `--platforms` imprime o passo-a-passo seguro:

- **WhatsApp**: adicione o contato no app e veja foto/status/última vez.
- **Instagram**: "Descobrir pessoas" > sincronizar contatos no app.

### Operadora atual (ABR Telecom) — fonte oficial da portabilidade BR

Devolve a operadora **de fato** (pós-portabilidade) + razão social. O site
exige hCaptcha, então o fluxo é **manual-assistido** (seu número, dentro dos ToS):

```bash
# 1) mostra a URL do desafio hCaptcha
numrecon 11999998888 --carrier

# 2) resolva no navegador, copie o h-captcha-response e rode:
numrecon 11999998888 --carrier <TOKEN>
```

Não contornamos o captcha nem automatizamos em massa.

### Breach / vazamentos

Só por **E-MAIL** via HaveIBeenPwned (oficial, grátis) — nunca por telefone.
Bases de vazamento por telefone não são cruzadas (acesso/uso pode ser ilegal).

## Limitações (intencionais)

- **Operadora offline** só indica indisponibilidade (a real vem da ABR Telecom).
  A portabilidade numérica torna qualquer inferência por faixa falsa.
- Cobertura de DDD/país é a mais comum; base local pode estar incompleta.

## Testes

```bash
pytest -q
```

## Licença

MIT
