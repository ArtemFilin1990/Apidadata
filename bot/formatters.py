from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from typing import Any

MAX_MESSAGE_LENGTH = 3900

STATUS_LABELS = {
    "ACTIVE": "действующая",
    "LIQUIDATING": "ликвидируется",
    "LIQUIDATED": "ликвидирована",
    "BANKRUPT": "банкротство",
    "REORGANIZING": "реорганизация",
}

TAX_SYSTEM_LABELS = {
    "AUSN": "АУСН",
    "ESHN": "ЕСХН",
    "SRP": "СРП",
    "USN": "УСН",
}

INVALIDITY_LABELS = {
    "PARTY": "обращение лица/организации",
    "FTS": "проверка ФНС",
    "COURT": "решение суда",
    "OTHER": "прочие причины",
}


def render_section(payload: dict[str, Any], section: str) -> str:
    if section == "main":
        return _truncate(_render_main(payload))
    if section == "revenue":
        return _truncate(_render_revenue(payload))
    if section == "debt":
        return _truncate(_render_debt(payload))
    if section == "penalty":
        return _truncate(_render_penalty(payload))
    if section == "court":
        return _truncate(_render_court(payload))
    if section == "risks":
        return _truncate(_render_risks(payload))
    if section == "people":
        return _truncate(_render_people(payload))
    if section == "contacts":
        return _truncate(_render_contacts(payload))
    if section == "licenses":
        return _truncate(_render_licenses(payload))
    return _truncate(_render_main(payload))


def _render_main(payload: dict[str, Any]) -> str:
    data = payload.get("data") or {}
    title = _title(payload)
    finance = data.get("finance") or {}
    state = data.get("state") or {}
    management = data.get("management") or {}
    okved_code = _string(data.get("okved"))
    okved_name = _string((_first_okved_name(data) or {}).get("name"))

    lines = [
        f"<b>{title}</b>",
        f"ИНН: <code>{escape(str(data.get('inn') or '—'))}</code>",
        f"ОГРН: <code>{escape(str(data.get('ogrn') or '—'))}</code>",
        f"Статус: <b>{escape(_status_label(state.get('status')))}</b>",
        f"Руководитель: {_manager_label(management)}",
        f"Адрес: {_string((data.get('address') or {}).get('value'))}",
        f"ОКВЭД: {okved_code} {okved_name}",
        f"Выручка {_finance_year(finance)}: {_money(finance.get('revenue'))}",
        f"Недоимки {_finance_year(finance)}: {_money(finance.get('debt'))}",
        f"Штрафы {_finance_year(finance)}: {_money(finance.get('penalty'))}",
    ]
    return "\n".join(lines)


def _render_revenue(payload: dict[str, Any]) -> str:
    data = payload.get("data") or {}
    finance = data.get("finance") or {}
    lines = [
        f"<b>{escape(_title(payload))}</b>",
        "<b>Оборот и финансы</b>",
        f"Год: {_string(finance.get('year'))}",
        f"Выручка: {_money(finance.get('revenue'))}",
        f"Доходы: {_money(finance.get('income'))}",
        f"Расходы: {_money(finance.get('expense'))}",
        f"Налоговый режим: {escape(TAX_SYSTEM_LABELS.get(str(finance.get('tax_system') or ''), str(finance.get('tax_system') or '—')))}",
        f"Среднесписочная численность: {_string(data.get('employee_count'))}",
    ]
    return "\n".join(lines)


def _render_debt(payload: dict[str, Any]) -> str:
    data = payload.get("data") or {}
    finance = data.get("finance") or {}
    lines = [
        f"<b>{escape(_title(payload))}</b>",
        "<b>Долги</b>",
        f"Год: {_string(finance.get('year'))}",
        f"Недоимки по налогам: {_money(finance.get('debt'))}",
    ]
    return "\n".join(lines)


def _render_penalty(payload: dict[str, Any]) -> str:
    data = payload.get("data") or {}
    finance = data.get("finance") or {}
    lines = [
        f"<b>{escape(_title(payload))}</b>",
        "<b>Штрафы</b>",
        f"Год: {_string(finance.get('year'))}",
        f"Налоговые штрафы: {_money(finance.get('penalty'))}",
    ]
    return "\n".join(lines)


def _render_court(payload: dict[str, Any]) -> str:
    data = payload.get("data") or {}
    decisions = _collect_court_decisions(data)
    lines = [
        f"<b>{escape(_title(payload))}</b>",
        "<b>Суды</b>",
        "Показываю только решения суда, которые DaData вернула в признаках недостоверности. Это не полный реестр дел.",
    ]
    if not decisions:
        lines.append("Совпадений не найдено.")
        return "\n".join(lines)

    for item in decisions:
        lines.append(
            "\n" +
            f"• {escape(item['source'])}: {escape(item['court_name'] or 'суд не указан')}"
            + (f", № {escape(item['number'])}" if item['number'] else "")
            + (f", дата {_date_ms(item['date'])}" if item['date'] else "")
        )
    return "\n".join(lines)


def _render_risks(payload: dict[str, Any]) -> str:
    data = payload.get("data") or {}
    state = data.get("state") or {}
    lines = [
        f"<b>{escape(_title(payload))}</b>",
        "<b>Риски</b>",
        f"Общий флаг недостоверности: {'есть' if data.get('invalid') else 'нет'}",
        f"Статус: {escape(_status_label(state.get('status')))}",
        f"Дата регистрации: {_date_ms(state.get('registration_date'))}",
        f"Дата ликвидации: {_date_ms(state.get('liquidation_date'))}",
    ]

    risks = _collect_invalidity_reasons(data)
    if not risks:
        lines.append("Явных признаков недостоверности в адресе, руководителях и учредителях не найдено.")
    else:
        lines.append("Найденные признаки:")
        for risk in risks:
            lines.append(f"• {escape(risk)}")
    return "\n".join(lines)


def _render_people(payload: dict[str, Any]) -> str:
    data = payload.get("data") or {}
    lines = [
        f"<b>{escape(_title(payload))}</b>",
        "<b>Лица</b>",
        f"Руководитель: {_manager_label(data.get('management') or {})}",
    ]

    founders = data.get("founders") or []
    if founders:
        lines.append("\n<b>Учредители</b>")
        for founder in founders:
            lines.append(f"• {_founder_label(founder)}")
    else:
        lines.append("\n<b>Учредители</b>\nНет данных.")

    managers = data.get("managers") or []
    if managers:
        lines.append("\n<b>Руководители</b>")
        for manager in managers:
            lines.append(f"• {_manager_item_label(manager)}")

    return "\n".join(lines)


def _render_contacts(payload: dict[str, Any]) -> str:
    data = payload.get("data") or {}
    lines = [
        f"<b>{escape(_title(payload))}</b>",
        "<b>Контакты</b>",
        f"Адрес: {_string((data.get('address') or {}).get('unrestricted_value') or (data.get('address') or {}).get('value'))}",
    ]

    phones = data.get("phones") or []
    emails = data.get("emails") or []

    if phones:
        lines.append("\n<b>Телефоны</b>")
        for phone in phones:
            value = phone.get("value") or (phone.get("data") or {}).get("source")
            phone_type = (phone.get("data") or {}).get("type")
            provider = (phone.get("data") or {}).get("provider")
            label = escape(str(value)) if value else "—"
            details = " / ".join(part for part in [str(phone_type or "").strip(), str(provider or "").strip()] if part)
            if details:
                lines.append(f"• {label} — {escape(details)}")
            else:
                lines.append(f"• {label}")
    else:
        lines.append("\n<b>Телефоны</b>\nНет данных.")

    if emails:
        lines.append("\n<b>Email</b>")
        for email in emails:
            value = email.get("value") or (email.get("data") or {}).get("source")
            lines.append(f"• {escape(str(value or '—'))}")
    else:
        lines.append("\n<b>Email</b>\nНет данных.")

    return "\n".join(lines)


def _render_licenses(payload: dict[str, Any]) -> str:
    data = payload.get("data") or {}
    licenses = data.get("licenses") or []
    lines = [
        f"<b>{escape(_title(payload))}</b>",
        "<b>Лицензии</b>",
    ]
    if not licenses:
        lines.append("Нет данных.")
        return "\n".join(lines)

    for license_item in licenses:
        number = license_item.get("number")
        authority = license_item.get("issue_authority")
        valid_from = _date_ms(license_item.get("valid_from"))
        valid_to = _date_ms(license_item.get("valid_to"))
        activities = license_item.get("activities") or []
        lines.append(
            "\n" +
            f"• № {escape(str(number or '—'))}"
            + (f" — {escape(str(authority))}" if authority else "")
            + f"\n  Срок: {valid_from} → {valid_to}"
        )
        if activities:
            lines.append("  Виды деятельности:")
            for activity in activities[:5]:
                lines.append(f"   - {escape(str(activity))}")
            if len(activities) > 5:
                lines.append(f"   - и ещё {len(activities) - 5}")
    return "\n".join(lines)


def _collect_court_decisions(data: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    address_invalidity = (data.get("address") or {}).get("invalidity")
    if isinstance(address_invalidity, dict) and address_invalidity.get("code") == "COURT":
        result.append({
            "source": "адрес",
            "court_name": ((address_invalidity.get("decision") or {}).get("court_name") or ""),
            "number": ((address_invalidity.get("decision") or {}).get("number") or ""),
            "date": ((address_invalidity.get("decision") or {}).get("date")),
        })

    for founder in data.get("founders") or []:
        invalidity = founder.get("invalidity") or {}
        if invalidity.get("code") == "COURT":
            result.append({
                "source": f"учредитель {_founder_name(founder)}",
                "court_name": ((invalidity.get("decision") or {}).get("court_name") or ""),
                "number": ((invalidity.get("decision") or {}).get("number") or ""),
                "date": ((invalidity.get("decision") or {}).get("date")),
            })

    for manager in data.get("managers") or []:
        invalidity = manager.get("invalidity") or {}
        if invalidity.get("code") == "COURT":
            result.append({
                "source": f"руководитель {_manager_name(manager)}",
                "court_name": ((invalidity.get("decision") or {}).get("court_name") or ""),
                "number": ((invalidity.get("decision") or {}).get("number") or ""),
                "date": ((invalidity.get("decision") or {}).get("date")),
            })

    return result


def _collect_invalidity_reasons(data: dict[str, Any]) -> list[str]:
    result: list[str] = []

    address_invalidity = (data.get("address") or {}).get("invalidity")
    if isinstance(address_invalidity, dict) and address_invalidity.get("code"):
        result.append(f"адрес: {_invalidity_reason(address_invalidity)}")

    for founder in data.get("founders") or []:
        invalidity = founder.get("invalidity") or {}
        if invalidity.get("code"):
            result.append(f"учредитель {_founder_name(founder)}: {_invalidity_reason(invalidity)}")

    for manager in data.get("managers") or []:
        invalidity = manager.get("invalidity") or {}
        if invalidity.get("code"):
            result.append(f"руководитель {_manager_name(manager)}: {_invalidity_reason(invalidity)}")

    return result


def _invalidity_reason(invalidity: dict[str, Any]) -> str:
    code = str(invalidity.get("code") or "")
    base = INVALIDITY_LABELS.get(code, code or "не указано")
    decision = invalidity.get("decision") or {}
    if code == "COURT" and any(decision.values()):
        parts = [str(decision.get("court_name") or "").strip(), str(decision.get("number") or "").strip()]
        tail = ", ".join(part for part in parts if part)
        if tail:
            return f"{base} ({tail})"
    return base


def _title(payload: dict[str, Any]) -> str:
    data = payload.get("data") or {}
    name = (data.get("name") or {}).get("short_with_opf") or payload.get("value")
    if name:
        return str(name)
    fio = data.get("fio") or {}
    fio_parts = [fio.get("surname"), fio.get("name"), fio.get("patronymic")]
    joined = " ".join(str(part).strip() for part in fio_parts if part)
    return joined or "Компания"


def _status_label(value: Any) -> str:
    raw = str(value or "—")
    return STATUS_LABELS.get(raw, raw)


def _string(value: Any) -> str:
    if value in (None, "", []):
        return "—"
    return escape(str(value))


def _money(value: Any) -> str:
    if value is None:
        return "нет данных"
    try:
        amount = int(round(float(value)))
    except (TypeError, ValueError):
        return escape(str(value))
    return f"{amount:,}".replace(",", " ") + " ₽"


def _date_ms(value: Any) -> str:
    if not value:
        return "—"
    try:
        value_int = int(value)
    except (TypeError, ValueError):
        return escape(str(value))
    try:
        dt = datetime.fromtimestamp(value_int / 1000, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return escape(str(value))
    return dt.strftime("%d.%m.%Y")


def _manager_label(management: dict[str, Any]) -> str:
    name = management.get("name") or "—"
    post = management.get("post")
    start_date = _date_ms(management.get("start_date"))
    details = []
    if post:
        details.append(str(post))
    if start_date != "—":
        details.append(f"с {start_date}")
    suffix = f" ({', '.join(details)})" if details else ""
    return escape(str(name)) + escape(suffix)


def _manager_name(manager: dict[str, Any]) -> str:
    fio = manager.get("fio") or {}
    parts = [fio.get("surname"), fio.get("name"), fio.get("patronymic")]
    joined = " ".join(str(part).strip() for part in parts if part)
    return joined or str(manager.get("name") or "—")


def _manager_item_label(manager: dict[str, Any]) -> str:
    name = _manager_name(manager)
    post = manager.get("post")
    start = _date_ms(manager.get("start_date"))
    details = []
    if post:
        details.append(str(post))
    if start != "—":
        details.append(f"с {start}")
    suffix = f" ({', '.join(details)})" if details else ""
    return escape(name) + escape(suffix)


def _founder_name(founder: dict[str, Any]) -> str:
    fio = founder.get("fio")
    if isinstance(fio, dict):
        parts = [fio.get("surname"), fio.get("name"), fio.get("patronymic")]
        joined = " ".join(str(part).strip() for part in parts if part)
        if joined:
            return joined
    return str(founder.get("name") or founder.get("fio") or "—")


def _founder_label(founder: dict[str, Any]) -> str:
    name = _founder_name(founder)
    share = founder.get("share") or {}
    share_value = ""
    share_type = share.get("type")
    if share.get("value") is not None:
        if share_type == "PERCENT":
            share_value = f" — {share.get('value')}%"
        else:
            share_value = f" — {share.get('value')}"
    elif share.get("numerator") and share.get("denominator"):
        share_value = f" — {share.get('numerator')}/{share.get('denominator')}"
    return escape(name + share_value)


def _first_okved_name(data: dict[str, Any]) -> dict[str, Any] | None:
    okveds = data.get("okveds") or []
    for item in okveds:
        if item.get("main"):
            return item
    return okveds[0] if okveds else None


def _finance_year(finance: dict[str, Any]) -> str:
    year = finance.get("year")
    return str(year) if year else "—"


def _truncate(text: str) -> str:
    if len(text) <= MAX_MESSAGE_LENGTH:
        return text
    return text[: MAX_MESSAGE_LENGTH - 1] + "…"
