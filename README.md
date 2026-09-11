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

### Telegram (opcional)

1. Crie um app em https://my.telegram.org (api_id, api_hash).
2. Exporte como variáveis de ambiente e rode:

```bash
export TG_API_ID=seu_id
export TG_API_HASH=seu_hash
numrecon 11999998888 --platforms
```

A checagem usa `contacts.importContacts` (API oficial) — nunca faz spam nem
contorna captcha. Na primeira execução você faz login na sua conta.

### WhatsApp

Sem API oficial de checagem. **Por design não automatizamos** (vira enumeração
de números, contra os ToS). O relatório indica o método manual seguro: adicione
o contato no seu próprio WhatsApp e veja status/foto.

## Limitações (intencionais)

- **Operadora exata não é inferida offline.** A portabilidade numérica torna
  qualquer inferência por faixa de números falsa. Isso é documentado, não bug.
- Cobertura de DDD/país é a mais comum; base local pode estar incompleta.

## Testes

```bash
pytest -q
```

## Licença

MIT
