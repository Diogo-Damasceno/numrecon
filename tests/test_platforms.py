from numrecon.platforms import list_platforms, run_platforms


def test_registry_has_all():
    keys = {c.key for c in list_platforms()}
    assert {"telegram", "whatsapp", "instagram", "breach"} <= keys


def test_whatsapp_safe_no_automation():
    r = run_platforms("+5511999998888")
    by_name = {x.name: x for x in r}
    wa = by_name["WhatsApp"]
    assert wa.available is True
    assert wa.checked is False  # por design não automatiza
    assert "ToS" in wa.terms_note
    assert wa.manual_steps  # tem passo-a-passo


def test_instagram_safe_no_automation():
    r = run_platforms("+5511999998888")
    by_name = {x.name: x for x in r}
    ig = by_name["Instagram"]
    assert ig.checked is False
    assert "anti-spam" in ig.terms_note


def test_telegram_missing_creds_no_crash():
    r = run_platforms("+5511999998888", creds={})
    by_name = {x.name: x for x in r}
    tg = by_name["Telegram"]
    assert tg.available is False  # telethon ausente ou creds faltando
    assert "api_id" in tg.detail or "telethon" in tg.detail


def test_breach_points_to_hibp():
    r = run_platforms("+5511999998888")
    by_name = {x.name: x for x in r}
    br = by_name["Breach (HIBP)"]
    assert "haveibeenpwned" in br.detail
    assert "telefone" in br.terms_note  # não cruzamos por telefone
