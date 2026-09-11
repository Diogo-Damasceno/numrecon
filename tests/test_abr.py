from numrecon.abr import _parse_result, challenge_url, SITEKEY
from numrecon.platforms import run_platforms


def test_parse_result_ok():
    html = (
        '<table id="resultado" class="grid">'
        '<tr><th>Data</th><th>Nome da Prestadora</th><th>Razao Social</th></tr>'
        '<tr><td>01/01/2020</td><td>CLARO S.A.</td><td>CLARO S.A.</td></tr>'
        '</table>'
    )
    r = _parse_result(html)
    assert r["carrier"] == "CLARO S.A."
    assert r["legal_name"] == "CLARO S.A."
    assert r["date"] == "01/01/2020"


def test_parse_result_none():
    r = _parse_result('<div>nao existem dados retornados para consulta</div>')
    assert r["carrier"] is None
    assert r["raw"]


def test_carrier_no_token_gives_steps():
    r = run_platforms("+5511999998888")
    by = {x.name: x for x in r}
    c = by["Operadora (ABR Telecom)"]
    assert c.checked is False
    assert "abr_challenge" in c.manual_steps or "captcha" in c.manual_steps.lower()
    assert SITEKEY in challenge_url()


def test_carrier_non_br_rejected():
    r = run_platforms("+351912345678")
    by = {x.name: x for x in r}
    assert "BR" in by["Operadora (ABR Telecom)"].detail
