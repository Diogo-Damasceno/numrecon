"""Núcleo de análise de números de telefone (self-OSINT, offline).

Tudo aqui é baseado em regras públicas e bases locais. NÃO consulta
a portabilidade numérica (que exigiria serviço externo), então a
operadora exata NÃO é determinada offline de forma confiável após a
portabilidade — isso é documentado e intencional.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

_DATA = Path(__file__).parent / "data"

with open(_DATA / "country_codes.json", encoding="utf-8") as _f:
    COUNTRY_CODES: dict[str, dict] = json.load(_f)

with open(_DATA / "br_ddd.json", encoding="utf-8") as _f:
    BR_DDD: dict[str, dict] = json.load(_f)


def normalize(raw: str) -> str:
    """Converte entrada livre para formato E.164 (+<dígitos>).

    Aceita: +5511999999999, 5511999999999, 11999999999, (11) 99999-9999,
    00 55 11 99999 9999, 11 99999-9999.
    """
    if raw is None:
        raise ValueError("número vazio")
    s = re.sub(r"[^\d+]", "", str(raw).strip())
    if not s:
        raise ValueError("número vazio após limpeza")

    if s.startswith("+"):
        return s
    if s.startswith("00"):
        return "+" + s[2:]
    # Sem indicativo: deduz Brasil se parecer nacional BR (10 ou 11 dígitos)
    if len(s) in (10, 11):
        return "+55" + s
    if s.startswith("55") and len(s) in (12, 13):
        return "+" + s
    if len(s) >= 11:  # já inclui código de país sem o '+'
        return "+" + s
    return "+55" + s


def _split_country(digits: str) -> tuple[str | None, str]:
    """Retorna (código_do_pais, número_nacional) ou (None, digits)."""
    for length in (3, 2, 1):
        cand = digits[:length]
        if cand in COUNTRY_CODES:
            return cand, digits[length:]
    return None, digits


def analyze(number: str) -> dict:
    """Análise completa do número.

    Devolve dicionário com: input, e164, valid, country, iso, national_number,
    region (DDD->UF/cidade para BR), type (mobile/landline/unknown), carrier,
    notes.
    """
    e164 = normalize(number)
    digits = e164.lstrip("+")
    result: dict = {
        "input": number,
        "e164": e164,
        "valid": False,
        "country": None,
        "iso": None,
        "national_number": None,
        "region": None,
        "type": None,
        "carrier": None,
        "notes": [],
    }

    cc, national = _split_country(digits)
    if cc is None:
        result["notes"].append("Código de país não reconhecido na base local")
        return result

    meta = COUNTRY_CODES[cc]
    result["iso"] = meta["iso"]
    result["country"] = meta["name"]
    result["national_number"] = national

    if meta.get("special"):
        result["notes"].append("Código especial/não-geográfico")
        result["valid"] = True
        return result

    if result["iso"] == "BR":
        _analyze_br(result, national)
    else:
        result["type"] = "unknown"
        result["valid"] = 4 <= len(national) <= 15
        if not result["valid"]:
            result["notes"].append(
                f"Comprimento nacional {len(national)} fora da faixa E.164 (4-15)"
            )

    return result


def _analyze_br(result: dict, national: str) -> None:
    if len(national) == 10:
        result["type"] = "landline"
        result["valid"] = True
    elif len(national) == 11 and national[2] == "9":
        result["type"] = "mobile"
        result["valid"] = True
    elif len(national) == 11:
        result["type"] = "mobile"
        result["valid"] = True
        result["notes"].append(
            "Móvel de 11 dígitos sem '9' após o DDD (faixa antiga/rara)"
        )
    else:
        result["valid"] = False
        result["notes"].append(
            f"Comprimento nacional BR inválido: {len(national)} dígitos (esperado 10 ou 11)"
        )

    ddd = national[:2]
    if ddd in ("00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "20"):
        result["valid"] = False
        result["notes"].append(f"DDD {ddd} inválido")
    elif ddd in BR_DDD:
        result["region"] = BR_DDD[ddd]
    else:
        result["notes"].append(f"DDD {ddd} ausente na base local")

    # Operadora exata requer base de portabilidade (externa). Intencionalmente
    # não inferimos por faixa — a portabilidade tornaria a inferência falsa.
    result["carrier"] = "indisponível offline (portabilidade numérica)"


def format_pt_br(result: dict) -> str:
    """Formata um resultado de análise BR como texto legível (pt-BR)."""
    lines = []
    lines.append(f"Entrada        : {result['input']}")
    lines.append(f"E.164          : {result['e164']}")
    lines.append(f"Válido         : {'sim' if result['valid'] else 'NÃO'}")
    lines.append(f"País           : {result['country']} ({result['iso']})")
    if result["region"]:
        lines.append(
            f"Região (DDD)    : {result['region']['city']} / {result['region']['uf']}"
        )
    if result["type"]:
        tipo = {"mobile": "móvel", "landline": "fixo"}.get(result["type"], result["type"])
        lines.append(f"Tipo           : {tipo}")
    if result["carrier"]:
        lines.append(f"Operadora      : {result['carrier']}")
    if result["notes"]:
        lines.append("Obs            : " + "; ".join(result["notes"]))
    return "\n".join(lines)
