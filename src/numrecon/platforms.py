"""Checagem de registro em plataformas (self-OSINT, apenas o SEU número).

LINHA ÉTICA / LEGAL (intencional e documentada):
- Só use com o SEU próprio número e suas próprias contas.
- Telegram: API oficial (telethon) com SUAS credenciais. Devolve nome/@username
  da conta vinculada — legítimo pra auto-auditoria.
- WhatsApp / Instagram: SEM automação. Não há API oficial de lookup por telefone;
  automatizar vira enumeração de terceiros (viola ToS). checklist manual abaixo.
- Vazamentos (leak dumps) / data brokers: NÃO cruzamos. Acesso/uso de bases de
  vazamento é ilegal em várias jurisdições. O checklist aponta verificação por
  E-MAIL no HaveIBeenPwned (oficial, gratuito), não por telefone.

Arquitetura: registro de "checkers". Cada um declara deps/creds e só roda se
disponível. Nada quebra o fluxo offline.
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
    display_name: str = ""
    username: str = ""
    detail: str = ""
    terms_note: str = ""
    manual_steps: str = ""


@dataclass
class Checker:
    key: str
    label: str
    needs: list[str] = field(default_factory=list)
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
# Telegram — API oficial (contacts.importContacts). Retorna nome + @username.
# ---------------------------------------------------------------------------
def _telegram_check(e164: str, creds: dict) -> PlatformResult:
    res = PlatformResult(name="Telegram")
    res.terms_note = (
        "API oficial (contacts.importContacts). Use só no seu número. "
        "Rate limit ~5 contatos/min em sessão nova."
    )
    if not _have("telethon"):
        res.detail = "telethon não instalado (pip install telethon)"
        return res
    api_id = creds.get("telegram_api_id")
    api_hash = creds.get("telegram_api_hash")
    if not (api_id and api_hash):
        res.detail = "creds ausentes: TG_API_ID / TG_API_HASH"
        return res

    from telethon.sync import TelegramClient

    phone = "+" + e164.lstrip("+")
    try:
        with TelegramClient("numrecon_session", int(api_id), api_hash) as client:
            result = client.import_contacts([phone])
            users = getattr(result, "users", None) or []
            imp = getattr(result, "imported", None) or []
            by_id = {getattr(u, "id", None): u for u in users}
            target = None
            for ic in imp:
                uid = getattr(ic, "user_id", None)
                if uid in by_id:
                    target = by_id[uid]
                    break
            if target is None and users:
                target = users[0]
            if target is not None:
                res.available = True
                res.checked = True
                res.registered = True
                res.display_name = " ".join(
                    filter(None, [getattr(target, "first_name", ""), getattr(target, "last_name", "")])
                ).strip()
                res.username = getattr(target, "username", "") or ""
                res.detail = f"registrado como {res.display_name or '(sem nome)'}" + (
                    f" (@{res.username})" if res.username else ""
                )
            else:
                res.available = True
                res.checked = True
                res.registered = False
                res.detail = "não registrado (sem user_id retornado)"
    except Exception as e:  # noqa: BLE001
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
# WhatsApp — sem API oficial de lookup. Checklist manual seguro.
# ---------------------------------------------------------------------------
def _whatsapp_check(e164: str, creds: dict) -> PlatformResult:
    res = PlatformResult(name="WhatsApp")
    res.terms_note = "Sem API oficial de checagem. Automatizar viola ToS (enumeração)."
    res.available = True
    res.checked = False
    res.detail = "checagem manual — sem automação por design"
    res.manual_steps = (
        f"1) Abra o WhatsApp e adicione o contato '{e164}'.\n"
        "2) Veja se há foto de perfil, status e 'última vez'.\n"
        "3) Em conversa, o nome exibido = o da conta vinculada."
    )
    return res


register(Checker(key="whatsapp", label="WhatsApp", fn=_whatsapp_check))


# ---------------------------------------------------------------------------
# Instagram — não há API oficial phone->conta. Checklist manual.
# ---------------------------------------------------------------------------
def _instagram_check(e164: str, creds: dict) -> PlatformResult:
    res = PlatformResult(name="Instagram")
    res.terms_note = (
        "Sem API oficial de lookup por telefone. O 'encontrar por contato' é "
        "in-app e bloqueado p/ automação (anti-spam). Não automatizamos."
    )
    res.available = True
    res.checked = False
    res.detail = "checagem manual — sem automação por design"
    res.manual_steps = (
        f"1) No app do Instagram, vá em 'Descobrir pessoas' > sincronize contatos.\n"
        f"2) O número '{e164}' aparece se houver conta vinculada (sujeito a "
        "configuração de privacidade do dono).\n"
        "3) Via web não há endpoint público confiável — não vale a pena raspar."
    )
    return res


register(Checker(key="instagram", label="Instagram", fn=_instagram_check))


# ---------------------------------------------------------------------------
# Breach / vazamentos — só por E-MAIL via HaveIBeenPwned (oficial). Não por tel.
# ---------------------------------------------------------------------------
def _breach_check(e164: str, creds: dict) -> PlatformResult:
    res = PlatformResult(name="Breach (HIBP)")
    res.terms_note = (
        "HaveIBeenPwned é por E-MAIL, não por telefone. Bases de vazamento por "
        "telefone não são cruzadas aqui (acesso/uso pode ser ilegal)."
    )
    res.available = True
    res.checked = False
    res.detail = "use seu E-MAIL em https://haveibeenpwned.com (oficial, grátis)"
    res.manual_steps = (
        "1) Vá em https://haveibeenpwned.com\n"
        "2) Digite o E-MAIL vinculado a este número (não o telefone).\n"
        "3) Veja em quais vazamentos o e-mail apareceu."
    )
    return res


register(Checker(key="breach", label="Breach (HIBP)", fn=_breach_check))


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
            out.append(PlatformResult(name=c.label, detail=f"erro: {e}"))
    return out
