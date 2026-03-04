from __future__ import annotations

import os
import random
import re
import time
import unicodedata
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus, urlparse

import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from ..models import Automacao
from provedor.models import Provedor


# =========================
# CONFIG (ajuste se quiser)
# =========================
HEADLESS = True
PAGE_LOAD_TIMEOUT = 30
WAIT_TIMEOUT = 10

# quantos sites salvar por linha
MAX_SITES_POR_LINHA = 3

# pausa aleatória entre ações
SLEEP_ENTRE_ACOES = (0.6, 1.4)

# se True, pula termos muito genéricos
PULAR_TERMOS_GENERICOS = False


BLACKLIST_GERAL = [
    ".gov.br",
    "wikipedia",
    "jusbrasil",
    "camara.",
    "licitacao",
    "diariooficial",
    "youtube",
    "facebook",
    "instagram",
    "twitter",
    "linkedin",
    "pinterest",
    "mercadolivre",
    "amazon",
    "magazineluiza",
    "shopee",
    "olx",
    "tiktok",
]

BLACKLIST_AGREGADORES = [
    "minhaconexao",
    "melhorescolha",
    "melhorplano",
    "assine",
    "selectra",
    "podecomparar",
    "portaldeplanos",
    "comparador",
    "telefone.ninja",
    "guiamais",
    "telelistas",
    "telefonia",
    "anatel",
    "reclameaqui",
    "speedtest",
    "nperf",
    "vivofibra",
    "clarofibra",
    "timlive",
    "oi.com.br",
    "lojavivo",
    "parceirovivo",
    "revenda",
    "claro",
]


# =========================
# helpers
# =========================
def _sleep() -> None:
    time.sleep(random.uniform(*SLEEP_ENTRE_ACOES))


def _norm(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^a-z0-9_]+", "", s)
    return s


def _pd_value(v):
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    s = str(v).strip()
    return s if s else None


def _parece_termo_generico(texto: str) -> bool:
    t = (texto or "").strip().lower()
    if not t:
        return True
    palavras = t.split()
    if len(palavras) >= 4 and any(p in palavras for p in ("na", "no", "em", "do", "da", "dos", "das", "para")):
        return True
    genericos = ("internet", "fibra", "banda", "provedor", "provedores", "melhor", "barata", "planos")
    if len(palavras) <= 2 and any(g in t for g in genericos):
        return True
    return False


def _url_valida(url: str) -> bool:
    if not url:
        return False
    try:
        u = urlparse(url)
        return u.scheme in ("http", "https") and bool(u.netloc)
    except Exception:
        return False


def eh_link_provedor_real(url: str) -> bool:
    if not _url_valida(url):
        return False
    url_lower = url.lower()
    for t in BLACKLIST_GERAL + BLACKLIST_AGREGADORES:
        if t in url_lower:
            return False
    if any(url_lower.endswith(ext) for ext in (".pdf", ".jpg", ".png", ".zip", ".rar")):
        return False
    return True


def _dedup_preserve(items: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    seen = set()
    out: List[Tuple[str, str]] = []
    for title, link in items:
        key = (link or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append((title, link))
    return out


def _pick(row: pd.Series, *cands: str) -> Optional[str]:
    for c in cands:
        v = _pd_value(row.get(c))
        if v:
            return v
    row_map = {_norm(k): k for k in row.index}
    for c in cands:
        cn = _norm(c)
        if cn in row_map:
            v = _pd_value(row.get(row_map[cn]))
            if v:
                return v
    return None


# =========================
# selenium driver
# =========================
def _detectar_chrome_binario() -> Optional[str]:
    candidatos = [
        os.getenv("CHROME_BINARY"),
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
    ]
    for c in candidatos:
        if c and os.path.exists(c):
            return c
    return None


def _detectar_chromedriver_binario() -> Optional[str]:
    candidatos = [
        os.getenv("CHROMEDRIVER_PATH"),
        "/usr/bin/chromedriver",
        "/usr/local/bin/chromedriver",
    ]
    for c in candidatos:
        if c and os.path.exists(c):
            return c
    return None


def configurar_driver() -> webdriver.Chrome:
    options = Options()
    if HEADLESS:
        options.add_argument("--headless=new")

    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--lang=pt-BR")

    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    chrome_bin = _detectar_chrome_binario()
    if chrome_bin:
        options.binary_location = chrome_bin

    driver_path = _detectar_chromedriver_binario()
    if driver_path:
        driver = webdriver.Chrome(service=Service(driver_path), options=options)
    else:
        driver = webdriver.Chrome(options=options)  # Selenium Manager

    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver


# =========================
# search
# =========================
class SearchBlocked(Exception):
    pass


def _google_consent(driver: webdriver.Chrome) -> None:
    candidates = [
        (By.ID, "L2AGLb"),
        (By.XPATH, "//button[contains(., 'Aceitar')]"),
        (By.XPATH, "//button[contains(., 'Concordo')]"),
        (By.XPATH, "//button[contains(., 'I agree')]"),
    ]
    for by, sel in candidates:
        try:
            btn = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((by, sel)))
            btn.click()
            _sleep()
            return
        except Exception:
            pass


def buscar_google(driver: webdriver.Chrome, query: str) -> List[Tuple[str, str]]:
    url = f"https://www.google.com/search?q={quote_plus(query)}&hl=pt-BR&gl=BR&num=10"
    driver.get(url)
    cur = (driver.current_url or "").lower()

    if "consent" in cur:
        _google_consent(driver)
        driver.get(url)
        cur = (driver.current_url or "").lower()

    if "sorry" in cur:
        raise SearchBlocked("Google bloqueou (página /sorry)")

    try:
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div#search a h3"))
        )
    except TimeoutException:
        if "sorry" in (driver.current_url or "").lower():
            raise SearchBlocked("Google bloqueou (página /sorry)")
        return []

    resultados: List[Tuple[str, str]] = []
    for h3 in driver.find_elements(By.CSS_SELECTOR, "div#search a h3"):
        try:
            a = h3.find_element(By.XPATH, "./ancestor::a")
            link = a.get_attribute("href")
            titulo = (h3.text or "").strip()
            if link:
                resultados.append((titulo, link))
        except Exception:
            continue
    return _dedup_preserve(resultados)


def buscar_duckduckgo_html(driver: webdriver.Chrome, query: str) -> List[Tuple[str, str]]:
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    driver.get(url)

    try:
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.result__a"))
        )
    except TimeoutException:
        return []

    resultados: List[Tuple[str, str]] = []
    for a in driver.find_elements(By.CSS_SELECTOR, "a.result__a"):
        try:
            link = a.get_attribute("href")
            titulo = (a.text or "").strip()
            if link:
                resultados.append((titulo, link))
        except Exception:
            continue
    return _dedup_preserve(resultados)


def buscar_bing(driver: webdriver.Chrome, query: str) -> List[Tuple[str, str]]:
    url = f"https://www.bing.com/search?q={quote_plus(query)}"
    driver.get(url)

    try:
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.b_algo h2 a"))
        )
    except TimeoutException:
        return []

    resultados: List[Tuple[str, str]] = []
    for a in driver.find_elements(By.CSS_SELECTOR, "li.b_algo h2 a"):
        try:
            link = a.get_attribute("href")
            titulo = (a.text or "").strip()
            if link:
                resultados.append((titulo, link))
        except Exception:
            continue
    return _dedup_preserve(resultados)


def buscar_sites(driver: webdriver.Chrome, query: str) -> List[Tuple[str, str]]:
    try:
        res = buscar_google(driver, query)
        if res:
            return res
    except SearchBlocked:
        pass
    except Exception:
        pass

    try:
        res = buscar_duckduckgo_html(driver, query)
        if res:
            return res
    except Exception:
        pass

    try:
        return buscar_bing(driver, query)
    except Exception:
        return []


# =========================
# planilha -> model mapping
# =========================
def _model_fields_norm(model) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for f in model._meta.get_fields():
        if not hasattr(f, "attname"):
            continue
        out[_norm(f.attname)] = f.attname
    return out


def _defaults_from_row(row: pd.Series, field_map: Dict[str, str]) -> Dict[str, str]:
    defaults: Dict[str, str] = {}

    aliases = {
        "uf": "estado",
        "sigla_uf": "estado",
        "link": "url_site",
        "site": "url_site",
        "website": "url_site",
    }

    for col in row.index:
        v = _pd_value(row.get(col))
        if v is None:
            continue

        c = _norm(col)
        if c in aliases:
            c = _norm(aliases[c])

        if c in field_map:
            defaults[field_map[c]] = v

    return defaults


def _nome_from_title_or_url(title: str, link: str) -> str:
    title = (title or "").strip()
    if title:
        return title
    try:
        dom = urlparse(link).netloc.replace("www.", "")
        if dom:
            return dom
    except Exception:
        pass
    return "Provedor"


# =========================
# AUTOMAÇÃO PRINCIPAL
# =========================
def automacao_provedores_web(tarefa_id, file_path):
    tarefa = None
    driver: Optional[webdriver.Chrome] = None

    try:
        tarefa = Automacao.objects.get(id=tarefa_id)
        df = pd.read_excel(file_path)
        field_map = _model_fields_norm(Provedor)

        driver = configurar_driver()

        total = len(df)
        for idx, row in df.iterrows():
            tarefa.refresh_from_db()
            if tarefa.status != "executando":
                break

            termo = _pick(row, "pesquisa", "query", "PESQUISA", "QUERY")
            nome = _pick(row, "nome", "NOME", "provedor", "PROVEDOR")
            cidade = _pick(row, "cidade", "CIDADE")
            uf = _pick(row, "estado", "ESTADO", "uf", "UF")

            if not termo:
                if nome:
                    termo = f"provedor de internet {nome} site oficial"
                elif cidade and uf:
                    termo = f"site provedor internet fibra {cidade} {uf}"
                elif cidade:
                    termo = f"site provedor internet fibra {cidade}"
                else:
                    continue

            if PULAR_TERMOS_GENERICOS and _parece_termo_generico(termo):
                print(f"[{idx+1}/{total}] Pulando termo genérico: {termo}")
                continue

            print(f"[{idx+1}/{total}] Pesquisando: {termo}")

            resultados = buscar_sites(driver, termo)
            if not resultados:
                print("   [ALERTA] Nenhum resultado")
                _sleep()
                continue

            links_validos: List[Tuple[str, str]] = []
            for title, link in resultados:
                if eh_link_provedor_real(link):
                    links_validos.append((title, link))
            links_validos = _dedup_preserve(links_validos)[:MAX_SITES_POR_LINHA]
            print(f"   [FILTRO] {len(links_validos)} sites potenciais")

            defaults_base = _defaults_from_row(row, field_map)

            # ✅ GARANTE STATUS "novo" em TODO registro criado (se o campo existir no model)
            if "status" in field_map.values() and not defaults_base.get("status"):
                defaults_base["status"] = "novo"

            # garante campos "cidade/estado" se existirem no seu model e não vieram na planilha
            if "cidade" in field_map.values() and not defaults_base.get("cidade"):
                defaults_base["cidade"] = cidade or "Itaitinga"
            if "estado" in field_map.values() and not defaults_base.get("estado"):
                defaults_base["estado"] = (uf or "CE")[:2]

            for title, link in links_validos:
                nome_final = _nome_from_title_or_url(title, link)

                defaults = dict(defaults_base)
                defaults["nome"] = nome_final
                defaults["url_site"] = link

                # lookup por url_site (evita duplicar)
                prov, created = Provedor.objects.get_or_create(
                    url_site=link,
                    defaults=defaults,
                )

                if not created:
                    # NÃO sobrescreve status existente, só preenche se estiver vazio
                    changed = False
                    for k, v in defaults.items():
                        if not hasattr(prov, k):
                            continue
                        cur = getattr(prov, k, None)
                        if (cur is None or cur == "") and (v is not None and v != ""):
                            setattr(prov, k, v)
                            changed = True
                    if changed:
                        prov.save()

                print(f"      [OK] {nome_final} -> {link}")
                _sleep()

        tarefa.refresh_from_db()
        if tarefa.status == "executando":
            tarefa.status = "concluido"
            tarefa.save()

    except (WebDriverException, TimeoutException) as e:
        print(f"Erro de navegador/selenium: {e}")
        try:
            tarefa = tarefa or Automacao.objects.get(id=tarefa_id)
            tarefa.status = "falha"
            tarefa.save()
        except Exception:
            pass

    except Exception as e:
        print(f"Erro geral: {e}")
        try:
            tarefa = tarefa or Automacao.objects.get(id=tarefa_id)
            tarefa.status = "falha"
            tarefa.save()
        except Exception:
            pass

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


REGISTRY = {
    # slug antigo (compatibilidade)
    "busca_google_provedores": automacao_provedores_web,
    # slug novo recomendado
    "busca_provedores_web": automacao_provedores_web,
}