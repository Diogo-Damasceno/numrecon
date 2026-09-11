"""CLI do numrecon.

Uso:
  numrecon <numero>                 analisa prefixo/país/tipo/região
  numrecon <numero> --platforms    também roda checagem de plataformas
  numrecon <numero> --carrier TOK  consulta operadora real (ABR Telecom)
  numrecon --self-test             roda um smoke test interno

Exemplos:
  numrecon 11999998888
  numrecon +351912345678 --platforms
  numrecon 11999998888 --carrier <hCaptcha-token>
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import analyze, normalize
from .core import format_pt_br
from .platforms import list_platforms, run_platforms


def _print_platforms(results) -> None:
    print("\n--- Registro em plataformas ---")
    for r in results:
        status = "?" if not r.checked else ("SIM" if r.registered else "não")
        line = f"  {r.name:<22} disponível={r.available} checado={r.checked}"
        if r.checked:
            line += f" registrado={status}"
        line += f" | {r.detail}"
        print(line)
        if r.display_name or r.username:
            extra = r.display_name + (f" (@{r.username})" if r.username else "")
            print(f"     → resultado: {extra}")
        if r.terms_note:
            print(f"     ⚠ {r.terms_note}")
        if r.manual_steps:
            print("     passo-a-passo:")
            for step in r.manual_steps.split("\n"):
                print(f"       {step}")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="numrecon",
        description="Self-OSINT do seu próprio número de telefone.",
    )
    p.add_argument("number", nargs="?", help="número (aceita +55, (11)..., 11...)")
    p.add_argument("--platforms", action="store_true", help="checar registro em plataformas")
    p.add_argument(
        "--carrier",
        nargs="?",
        const="__SHOW__",
        metavar="TOKEN",
        help="consulta operadora (ABR Telecom); sem TOKEN mostra a URL do captcha",
    )
    p.add_argument("--json", action="store_true", help="saída JSON")
    p.add_argument("--self-test", action="store_true", help="smoke test interno")
    args = p.parse_args(argv)

    if args.self_test:
        return _self_test()

    if not args.number:
        p.error("informe um número (ou --self-test)")

    carrier_token = args.carrier if args.carrier and args.carrier != "__SHOW__" else None

    try:
        res = analyze(args.number)
    except ValueError as e:
        print(f"erro: {e}", file=sys.stderr)
        return 2

    # --carrier sem token: só mostra a URL do desafio e sai
    if args.carrier == "__SHOW__":
        from .abr import challenge_url

        print("Abra e resolva o captcha hCaptcha nesta URL:\n")
        print("  " + challenge_url() + "\n")
        print("Depois rode: numrecon " + args.number + " --carrier <TOKEN>")
        return 0

    if args.json:
        out = dict(res)
        creds = _creds(carrier_token)
        if args.platforms or args.carrier:
            out["platforms"] = [vars(r) for r in run_platforms(res["e164"], creds)]
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(format_pt_br(res))
        if args.platforms or args.carrier:
            _print_platforms(run_platforms(res["e164"], _creds(carrier_token)))

    return 0


def _creds(carrier_token: str | None = None) -> dict:
    return {
        "telegram_api_id": os.environ.get("TG_API_ID"),
        "telegram_api_hash": os.environ.get("TG_API_HASH"),
        "abr_hcaptcha_token": carrier_token,
    }


def _self_test() -> int:
    cases = {
        "11999998888": ("+5511999998888", True, "mobile", "SP"),
        "+351912345678": ("+351912345678", True, None, None),
        "1133334444": ("+551133334444", True, "landline", "SP"),
        "abc": (None, False, None, None),
    }
    ok = True
    for raw, (exp_e164, exp_valid, exp_type, exp_uf) in cases.items():
        try:
            r = analyze(raw)
        except ValueError:
            r = None
        if r is None:
            got_valid = False
        else:
            got_valid = r["valid"]
        if r is None or (exp_e164 is None and got_valid):
            continue
        if r is None:
            ok = False
            print(f"FAIL {raw}: esperado valid={exp_valid}, quebrou")
            continue
        if r["e164"] != exp_e164 or got_valid != exp_valid:
            ok = False
            print(f"FAIL {raw}: {r['e164']}!={exp_e164} ou valid {got_valid}!={exp_valid}")
            continue
        if exp_type and r["type"] != exp_type:
            ok = False
            print(f"FAIL {raw}: tipo {r['type']}!={exp_type}")
            continue
        if exp_uf and (not r["region"] or r["region"]["uf"] != exp_uf):
            ok = False
            print(f"FAIL {raw}: uf {r['region']}!={exp_uf}")
            continue
        print(f"ok   {raw} -> {r['e164']} valid={got_valid} type={r['type']} uf={exp_uf}")
    print("SELF-TEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
