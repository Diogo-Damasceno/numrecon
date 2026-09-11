"""Checagem de registro em plataformas (self-OSINT).

AVISO IMPORTANTE DE ToS / USO:
- Use SOMENTE com o SEU próprio número e suas próprias contas.
- Cada plataforma tem termos que podem proibir automação/checagem.
- Este módulo NÃO contorna captchas nem faz spam: a checagem de Telegram
  usa a própria API oficial (telethon) com CREDENCIAIS SUAS (api_id/api_hash
  do my.telegram.org). Sem elas, nada é feito.

A arquitetura é um registro de "checkers". Cada checker declara o que
precisa (deps, creds) e só roda se disponível. Checkers que exigem serviço
externo são OPCIONAIS e nunca quebram o fluxo offline.
"""
from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field


@dataclass
class PlatformResult:
    name: str
    available: bool = False
    checked: bool = False
    registered: bool | None = None
    detail: str = ""
    terms_note: str = ""


@dataclass
class Checker:
    key: str
    label: str
    needs: list[str] = field(default_factory=list)  # nomes de dependências python
    needs_creds: list[str] = field(default_factory=list)
    fn: object = None  # callable(e164, creds) -> PlatformResult


_REGISTRY: list[Checker] = []


def register(c: Checker) -> Checker:
    _REGISTRY.append(c)
    return c


def _have(mod: str) -> bool:
    return importlib.util.find_spec(mod) is not None


def list_platforms() -> list[Checker]:
    return list(_REGISTRY)


# ---------------------------------------------------------------------------
# Telegram — usa a API oficial via telethon (contacts.importContacts).
# Requer api_id e api_hash do my.telegram.org e um número/sessão próprios.
# ---------------------------------------------------------------------------
def _telegram_check(e164: str, creds: dict) -> PlatformResult:
    res = PlatformResult(name="Telegram")
    res.terms_note = (
        "Telegram permite importar contatos pela API oficial; use apenas com "
        "seu próprio número. Rate limit: ~5 contatos/min em sessão nova."
    )
    if not _have("telethon"):
        res.detail = "telethon não instalado (pip install telethon)"
        return res
    api_id = creds.get("telegram_api_id")
    api_hash = creds.get("telegram_api_hash")
    if not (api_id and api_hash):
        res.detail = "creds ausentes: telegram_api_id / telegram_api_hash"
        return res

    from telethon.sync import TelegramClient

    phone = "+" + e164.lstrip("+")
    try:
        with TelegramClient("numrecon_session", int(api_id), api_hash) as client:
            # importContacts com o número alvo; o retorno mapeia se há conta.
            contacts = client.import_contacts([phone])
            imp = getattr(contacts, "imported", None)
            registered = None
            if imp:
                registered = any(getattr(c, "user_id", None) for c in imp)
            res.available = True
            res.checked = True
            res.registered = bool(registered)
            res.detail = (
                "registrado" if registered else "não registrado / sem retorno de user_id"
            )
    except Exception as e:  # noqa: BLE001 - reportar, não quebrar
        res.detail = f"erro Telegram: {type(e).__name__}: {e}"
    return res


register(
    Checker(
        key="telegram",
        label="Telegram",
        needs=["telethon"],
        needs_creds=["telegram_api_id", "telegram_api_hash"],
        fn=_telegram_check,
    )
)


# ---------------------------------------------------------------------------
# WhatsApp — checkers não-oficiais violam os ToS e são bloqueados.
# Em vez de automatizar, documentamos como o próprio app revela (status/
# foto) e damos o caminho manual seguro. NÃO fazemos requisição.
# ---------------------------------------------------------------------------
def _whatsapp_check(e164: str, creds: dict) -> PlatformResult:
    res = PlatformResult(name="WhatsApp")
    res.terms_note = (
        "Sem API oficial de checagem. Não automatizamos (viola ToS e vira "
        "enumeração de números). Método seguro: adicione o contato no seu "
        "próprio WhatsApp e veja se há status/foto/última vez."
    )
    res.available = True
    res.checked = False
    res.detail = "checagem manual — sem automação por design"
    return res


register(Checker(key="whatsapp", label="WhatsApp", fn=_whatsapp_check))


def run_platforms(e164: str, creds: dict | None = None) -> list[PlatformResult]:
    creds = creds or {}
    out = []
    for c in _REGISTRY:
        if c.fn is None:
            out.append(PlatformResult(name=c.label, detail="não implementado"))
            continue
        try:
            out.append(c.fn(e164, creds))
        except Exception as e:  # noqa: BLE001
            r = PlatformResult(name=c.label, detail=f"erro: {e}")
            out.append(r)
    return out
