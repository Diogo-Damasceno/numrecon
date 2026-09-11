"""Consulta de operadora atual na ABR Telecom (portabilidade numérica BR).

Fonte oficial: https://consultanumero.abrtelecom.com.br
Entidade Administradora da Portabilidade Numérica no Brasil. Devolve a
operadora DE FATO (pós-portabilidade) — bem melhor que inferir por prefixo.

IMPORTANTE (ToS / automação):
- O site exige hCaptcha. Não contornamos: o fluxo é MANUAL ASSISTIDO — a
  ferramenta abre a URL do desafio, VOCÊ resolve (é o seu número), cola o
  token, e ela faz o POST + parseia a tabela de resultado. Legítimo para
  auto-auditoria; não é automação em massa.
- Endpoint descoberto por inspeção: POST /consultanumero/consulta/
  executaConsultaSituacaoAtual (csrfTokenCN + telefone + h-captcha-response).
"""
from __future__ import annotations

import re
import urllib.parse
import urllib.request

BASE = "https://consultanumero.abrtelecom.com.br"
SITEKEY = "6LetJT0mAAAAAHHjqRIbvtua09CQ8JTdpa5h0GKe"


def challenge_url() -> str:
    """URL do desafio hCaptcha para o usuário resolver manualmente."""
    q = urllib.parse.urlencode(
        {
            "sitekey": SITEKEY,
            "hl": "pt-BR",
            # callback dummy — o usuário copia o token da dev tools ou de uma
            # extensão; para uso simples deixamos o site oficial mesmo.
        }
    )
    return f"{BASE}/consultanumero/consulta/consultaSituacaoAtualCtg?{q}"


def _get_csrf() -> tuple[str, dict]:
    req = urllib.request.Request(
        f"{BASE}/consultanumero/consulta/consultaSituacaoAtualCtg",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=25) as r:  # noqa: S310 - https only
        html = r.read().decode("iso-8859-1", errors="replace")
        cookie = r.headers.get("Set-Cookie", "")
    m = re.search(r'name="csrfTokenCN" value="([^"]+)"', html)
    csrf = m.group(1) if m else ""
    return csrf, {"Cookie": cookie}


def _parse_result(html: str) -> dict:
    out = {"carrier": None, "legal_name": None, "date": None, "raw": None}
    # Procura a tabela #resultado
    tbl = re.search(r'<table id="resultado".*?</table>', html, re.S | re.I)
    if not tbl:
        if re.search(r"não existem dados", html, re.I):
            out["raw"] = "sem dados para este número"
        else:
            out["raw"] = "captcha inválido / ausente ou sem resultado"
        return out
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", tbl.group(0), re.S | re.I)
    for row in rows[1:]:  # pula cabeçalho
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S | re.I)
        cells = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
        # Colunas: Data | Nome da Prestadora | (Razão Social)
        if len(cells) >= 2:
            out["date"] = cells[0] or out["date"]
            out["carrier"] = cells[1] or out["carrier"]
            if len(cells) >= 3:
                out["legal_name"] = cells[2] or out["legal_name"]
    return out


def consulta(numero_nacional: str, hcaptcha_token: str) -> dict:
    """Consulta a operadora atual.

    numero_nacional: só dígitos nacionais, ex. '11999998888'.
    hcaptcha_token: token real resolvido pelo usuário no site.
    """
    csrf, headers = _get_csrf()
    if not csrf:
        return {"carrier": None, "legal_name": None, "date": None,
                "raw": "não foi possível obter csrfTokenCN"}
    data = urllib.parse.urlencode(
        {
            "csrfTokenCN": csrf,
            "telefone": f"({numero_nacional[:2]}) {numero_nacional[2:]}",
            "h-captcha-response": hcaptcha_token,
        }
    ).encode()
    req = urllib.request.Request(
        f"{BASE}/consultanumero/consulta/executaConsultaSituacaoAtual",
        data=data,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": f"{BASE}/consultanumero/consulta/consultaSituacaoAtualCtg",
            **headers,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=25) as r:  # noqa: S310
        html = r.read().decode("iso-8859-1", errors="replace")
    return _parse_result(html)
