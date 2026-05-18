# -*- coding: utf-8 -*-
"""Convert legal .docx files to full HTML pages."""
from __future__ import annotations

import html
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
BASE = Path(__file__).resolve().parent.parent
STOP_MARKERS = ("ВЕРСИЯ ИГОРЯ",)

SHELL_HEAD = """<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="{desc}" />
    <title>{title} — Мой авто</title>
    <link rel="icon" type="image/png" href="assets/favicon.png" sizes="32x32" />
    <link rel="icon" type="image/png" href="assets/favicon-16.png" sizes="16x16" />
    <link rel="apple-touch-icon" href="assets/apple-touch-icon.png" sizes="180x180" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap"
      rel="stylesheet"
    />
    <link rel="stylesheet" href="css/document.css" />
  </head>
  <body class="doc-page">
    <header class="doc-header">
      <a class="doc-header__brand brand" href="index.html" aria-label="На главную">
        <div class="brand__icon">
          <img src="assets/app-icon.png" alt="" width="48" height="48" />
        </div>
        <div class="brand__text">
          <p class="brand__title">Мой авто</p>
          <p class="brand__tagline">Учет пробега и расходов</p>
        </div>
      </a>
    </header>
    <main class="doc-content">
      <article class="doc-article">
"""

SHELL_TAIL = """
      </article>
    </main>
    <script src="js/home-links.js" defer></script>
  </body>
</html>
"""


def para_text(p_elem: ET.Element) -> str:
    parts: list[str] = []
    for t in p_elem.iter(f"{{{NS_W}}}t"):
        if t.text:
            parts.append(t.text)
        if t.tail:
            parts.append(t.tail)
    return "".join(parts).strip()


def is_bold(p_elem: ET.Element) -> bool:
    for r in p_elem.findall(f".//{{{NS_W}}}r"):
        r_pr = r.find(f"{{{NS_W}}}rPr")
        if r_pr is not None and r_pr.find(f"{{{NS_W}}}b") is not None:
            return True
    return False


def parse_docx(path: Path) -> list[dict]:
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
    body = root.find(f".//{{{NS_W}}}body")
    items: list[dict] = []
    for child in body:
        if child.tag.split("}")[-1] != "p":
            continue
        text = para_text(child)
        if text:
            items.append({"text": text, "bold": is_bold(child)})
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

        if any(m in text for m in STOP_MARKERS):
            break

        if i == 0 and bold:
            out.append(f"        <h1>{html.escape(text)}</h1>\n")
            i += 1
            continue

        if "Дата публикации" in text:
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
    (
        "privacy.html",
        "Политика обработки персональных данных",
        "Политика обработки персональных данных приложения Мой авто",
        BASE / "lagal docs" / "Политика конфиденциальности (Privacy Policy).docx",
    ),
    (
        "terms.html",
        "Пользовательское соглашение",
        "Пользовательское соглашение приложения Мой авто",
        BASE / "lagal docs" / "Пользовательское соглашение (Terms of Service).docx",
    ),
]


def write_page(filename: str, title: str, desc: str, docx_path: Path) -> None:
    article = items_to_html(parse_docx(docx_path))
    content = SHELL_HEAD.format(title=title, desc=desc) + article + SHELL_TAIL
    (BASE / filename).write_text(content, encoding="utf-8")
    print(f"Wrote {filename}")


if __name__ == "__main__":
    for args in PAGES:
        write_page(*args)
