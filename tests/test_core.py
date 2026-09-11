import pytest

from numrecon import analyze, normalize


def test_normalize_varied_formats():
    assert normalize("11999998888") == "+5511999998888"
    assert normalize("+5511999998888") == "+5511999998888"
    assert normalize("(11) 99999-8888") == "+5511999998888"
    assert normalize("00 55 11 99999 8888") == "+5511999998888"
    assert normalize("352912345678") == "+352912345678"  # Luxemburgo, sem +


def test_analyze_br_mobile():
    r = analyze("11999998888")
    assert r["valid"] is True
    assert r["e164"] == "+5511999998888"
    assert r["iso"] == "BR"
    assert r["type"] == "mobile"
    assert r["region"]["uf"] == "SP"
    assert r["region"]["city"] == "São Paulo"


def test_analyze_br_landline():
    r = analyze("1133334444")
    assert r["valid"] is True
    assert r["type"] == "landline"
    assert r["region"]["uf"] == "SP"


def test_analyze_br_short_invalid():
    r = analyze("119999")
    assert r["valid"] is False


def test_analyze_foreign():
    r = analyze("+351912345678")
    assert r["valid"] is True
    assert r["iso"] == "PT"
    assert r["country"] == "Portugal"
    assert r["type"] == "unknown"  # não inferimos fora do BR


def test_analyze_unknown_country():
    r = analyze("+999999999999")
    assert r["valid"] is False
    assert r["iso"] is None
    assert any("não reconhecido" in n for n in r["notes"])


def test_empty_raises():
    with pytest.raises(ValueError):
        normalize("")
    with pytest.raises(ValueError):
        normalize("   ")
