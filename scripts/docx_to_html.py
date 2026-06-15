# -*- coding: utf-8 -*-
"""Convert legal .docx files to full HTML pages."""
from __future__ import annotations

import html
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{NS_W}}}"
BASE = Path(__file__).resolve().parent.parent
STOP_MARKERS = ("ВЕРСИЯ ИГОРЯ",)
NEW_DOCS = BASE / "lagal docs" / "new docs"


@dataclass(frozen=True)
class Page:
    filename: str
    lang: str
    title: str
    desc: str
    docx_path: Path
    ru_href: str
    en_href: str
    toolbar_label: str
    switch_label: str

SHELL_HEAD = """<!DOCTYPE html>
<html lang="{lang}">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="{desc}" />
    <title>{title}</title>
    <link rel="alternate" hreflang="ru" href="{ru_href}" />
    <link rel="alternate" hreflang="en" href="{en_href}" />
    <link rel="icon" type="image/png" href="assets/favicon.png" sizes="32x32" />
    <link rel="icon" type="image/png" href="assets/favicon-16.png" sizes="16x16" />
    <link rel="apple-touch-icon" href="assets/apple-touch-icon.png" sizes="180x180" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&amp;display=swap"
      rel="stylesheet"
    />
    <link rel="stylesheet" href="css/document.css?v=20260615-2" />
  </head>
  <body class="doc-page">
    <main class="doc-content">
      <nav class="doc-toolbar" aria-label="{toolbar_label}">
        <div class="language-switch" role="group" aria-label="{switch_label}">
          <a class="language-switch__option" href="{ru_href}" lang="ru"{ru_current}>Ru</a>
          <a class="language-switch__option" href="{en_href}" lang="en"{en_current}>En</a>
        </div>
      </nav>
      <article class="doc-article">
"""

SHELL_TAIL = """
      </article>
    </main>
  </body>
</html>
"""


def para_text(p_elem: ET.Element) -> str:
    parts: list[str] = []
    for t in p_elem.iter(f"{W}t"):
        if t.text:
            parts.append(t.text)
        if t.tail:
            parts.append(t.tail)
    return "".join(parts).strip()


def style_value(p_elem: ET.Element) -> str:
    p_style = p_elem.find(f"./{W}pPr/{W}pStyle")
    if p_style is None:
        return ""
    return p_style.attrib.get(f"{W}val", "")


def is_bold_paragraph(p_elem: ET.Element) -> bool:
    text_runs = []
    for r in p_elem.findall(f".//{W}r"):
        run_text = "".join(t.text or "" for t in r.findall(f".//{W}t"))
        if not run_text.strip():
            continue
        r_pr = r.find(f"{W}rPr")
        text_runs.append(r_pr is not None and r_pr.find(f"{W}b") is not None)
    return bool(text_runs) and all(text_runs)


def parse_docx(path: Path) -> list[dict]:
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
    body = root.find(f".//{W}body")
    items: list[dict] = []
    for child in body:
        if child.tag.split("}")[-1] != "p":
            continue
        text = para_text(child)
        if text:
            style = style_value(child)
            items.append(
                {
                    "text": text,
                    "bold": is_bold_paragraph(child),
                    "is_list": style.lower().startswith("list"),
                }
            )
    return items


def is_definition(text: str, bold: bool) -> bool:
    return bold and " — " in text


def is_list_trigger(text: str) -> bool:
    lower = text.lower()
    return any(
        t in lower
        for t in (
            "вправе:",
            "имеет право:",
            "запрещается:",
            "регулируют:",
            "не несет ответственности за:",
            "при условии:",
            "должно содержать:",
            "включая:",
        )
    )


def is_list_item(text: str) -> bool:
    if text.endswith(";"):
        return True
    if len(text) <= 70 and text.endswith("."):
        return True
    if text and text[0].islower():
        return True
    starters = (
        "удалить ",
        "направить ",
        "последствия ",
        "ущерб,",
        "за потерю",
        "Указание ",
        "Сведения ",
        "Для физического",
        "Для юридического",
        "Подпись ",
        "приостановить ",
        "отказать ",
        "сохранения ",
        "сохранение ",
    )
    return any(text.startswith(s) for s in starters)


def items_to_html(items: list[dict]) -> str:
    out: list[str] = []
    in_list = False
    i = 0

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            out.append("        </ul>\n")
            in_list = False

    while i < len(items):
        it = items[i]
        text = it["text"]
        bold = it["bold"]
        is_list = it["is_list"]

        if any(m in text for m in STOP_MARKERS):
            break

        if is_list:
            if not in_list:
                out.append("        <ul>\n")
                in_list = True
            item = text.lstrip("•").lstrip("—").strip()
            out.append(f"          <li>{html.escape(item)}</li>\n")
            i += 1
            continue

        if i == 0 and bold:
            out.append(f"        <h1>{html.escape(text)}</h1>\n")
            i += 1
            continue

        if (
            text.startswith("Дата публикации:")
            or text.startswith("Дата вступления")
            or text.startswith("Effective date:")
        ):
            close_list()
            out.append(f'        <p class="doc-lead">{html.escape(text)}</p>\n')
            i += 1
            continue

        if is_definition(text, bold):
            close_list()
            term, _, definition = text.partition(" — ")
            out.append(
                f"        <p><strong>{html.escape(term.strip())}</strong> — "
                f"{html.escape(definition.strip())}</p>\n"
            )
            i += 1
            continue

        if bold:
            close_list()
            out.append(f"        <h2>{html.escape(text)}</h2>\n")
            i += 1
            continue

        if text.startswith("•") or text.startswith("— "):
            if not in_list:
                out.append("        <ul>\n")
                in_list = True
            item = text.lstrip("•").lstrip("—").strip()
            out.append(f"          <li>{html.escape(item)}</li>\n")
            i += 1
            continue

        if is_list_trigger(text):
            close_list()
            out.append(f"        <p>{html.escape(text)}</p>\n")
            i += 1
            while i < len(items) and not items[i]["bold"]:
                nxt = items[i]["text"]
                if any(m in nxt for m in STOP_MARKERS):
                    break
                if is_list_trigger(nxt) or not is_list_item(nxt):
                    break
                if not in_list:
                    out.append("        <ul>\n")
                    in_list = True
                out.append(f"          <li>{html.escape(nxt)}</li>\n")
                i += 1
            close_list()
            continue

        close_list()
        out.append(f"        <p>{html.escape(text)}</p>\n")
        i += 1

    close_list()
    return "".join(out)


PAGES = [
    Page(
        filename="privacy.html",
        lang="ru",
        title="Политика конфиденциальности — Мой авто",
        desc="Политика конфиденциальности приложения Мой авто",
        docx_path=NEW_DOCS / "myauto_privacy_policy_ru_firebase_updated.docx",
        ru_href="privacy.html",
        en_href="privacy-en.html",
        toolbar_label="Выбор языка",
        switch_label="Язык документа",
    ),
    Page(
        filename="privacy-en.html",
        lang="en",
        title="Privacy Policy - My Auto",
        desc="Privacy Policy for the My Auto app",
        docx_path=NEW_DOCS / "myauto_privacy_policy_en_firebase_updated.docx",
        ru_href="privacy.html",
        en_href="privacy-en.html",
        toolbar_label="Language selection",
        switch_label="Document language",
    ),
    Page(
        filename="terms.html",
        lang="ru",
        title="Условия использования — Мой авто",
        desc="Условия использования приложения Мой авто",
        docx_path=NEW_DOCS / "myauto_terms_of_use_ru_firebase_updated.docx",
        ru_href="terms.html",
        en_href="terms-en.html",
        toolbar_label="Выбор языка",
        switch_label="Язык документа",
    ),
    Page(
        filename="terms-en.html",
        lang="en",
        title="Terms of Use - My Auto",
        desc="Terms of Use for the My Auto app",
        docx_path=NEW_DOCS / "myauto_terms_of_use_en_firebase_updated.docx",
        ru_href="terms.html",
        en_href="terms-en.html",
        toolbar_label="Language selection",
        switch_label="Document language",
    ),
]


def write_page(page: Page) -> None:
    article = items_to_html(parse_docx(page.docx_path))
    content = (
        SHELL_HEAD.format(
            lang=html.escape(page.lang),
            title=html.escape(page.title),
            desc=html.escape(page.desc),
            ru_href=html.escape(page.ru_href),
            en_href=html.escape(page.en_href),
            toolbar_label=html.escape(page.toolbar_label),
            switch_label=html.escape(page.switch_label),
            ru_current=' aria-current="true"' if page.lang == "ru" else "",
            en_current=' aria-current="true"' if page.lang == "en" else "",
        )
        + article
        + SHELL_TAIL
    )
    (BASE / page.filename).write_text(content, encoding="utf-8")
    print(f"Wrote {page.filename}")


if __name__ == "__main__":
    for page in PAGES:
        write_page(page)
