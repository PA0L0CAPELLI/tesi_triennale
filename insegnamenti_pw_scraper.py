
from __future__ import annotations

import asyncio
import hashlib
import re
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError
import unicodedata

def flatten_sezioni_special(sezioni: dict) -> dict:
    """
    Appiattisce `sezioni` e restituisce solo gli header fissi richiesti.
    - Le sottochiavi di 'Informazioni generali' vengono portate a top-level.
    - Sinonimi e varianti (accenti, apostrofi, plurali) vengono unificati.
    - Se arrivano più valori per lo stesso header, si sceglie il migliore (non vuoto; più lungo).
    - Campi mancanti -> None.
    """

    # Header fissi e ordine
    headers = [
        "Corso di studi", "Percorso", "Tipo di corso", "Anno di offerta", "Anno di corso",
        "Tipo Attività Formativa", "Ambito", "Lingua", "Crediti", "Tipo attività didattica",
        "Valutazione", "Periodo didattico", "Docente titolare", "Responsabili", "Durata",
        "Frequenza", "Modalità didattica", "Settore scientifico disciplinare", "Sede",
        "Obiettivi agenda", "Prerequisiti", "Obiettivi formativi", "Contenuti",
        "Metodi didattici", "Verifica dell'apprendimento", "Altro",
        "Risorse online", "Testi"
    ]

    # Normalizzazione chiavi: lowercase, no accenti, apostrofi uniformati, no punteggiatura (tranne spazi)
    def _canon(s: str) -> str:
        s = (s or "").strip().lower()
        # uniforma apostrofi
        s = s.replace("’", "'").replace("`", "'")
        # rimuovi accenti
        s = "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch))
        # sostituisci apostrofi con nulla
        s = s.replace("'", "")
        # rimuovi tutto ciò che non è alfanumerico o spazio
        s = re.sub(r"[^a-z0-9\s]", " ", s)
        # comprimi spazi
        s = re.sub(r"\s+", " ", s).strip()
        return s

    # Mappa sinonimi/varianti (chiavi canoniche -> header target)
    syn = {
        # generali
        "corso di studi": "Corso di studi",
        "percorso": "Percorso",
        "tipo di corso": "Tipo di corso",
        "anno di offerta": "Anno di offerta",
        "anno di corso": "Anno di corso",
        "tipo attivita formativa": "Tipo Attività Formativa",
        "ambito": "Ambito",
        "lingua": "Lingua",
        "crediti": "Crediti",
        "crediti cfu": "Crediti",
        "cfu": "Crediti",
        "tipo attivita didattica": "Tipo attività didattica",
        "valutazione": "Valutazione",
        "periodo didattico": "Periodo didattico",
        "docente titolare": "Docente titolare",
        "docenti": "Docente titolare",
        "responsabili": "Responsabili",
        "durata": "Durata",
        "frequenza": "Frequenza",
        "modalita didattica": "Modalità didattica",
        "modalita dell insegnamento": "Modalità didattica",
        "settore scientifico disciplinare": "Settore scientifico disciplinare",
        "sede": "Sede",
        "obiettivi agenda": "Obiettivi agenda",
        "prerequisiti": "Prerequisiti",
        # obiettivi
        "obiettivi formativi": "Obiettivi formativi",
        "obiettivi del modulo": "Obiettivi formativi",
        "obiettivi dell insegnamento": "Obiettivi formativi",
        "obiettivi insegnamento": "Obiettivi formativi",
        "obiettivi specifici": "Obiettivi formativi",
        # contenuti
        "contenuti": "Contenuti",
        "contenuti del modulo": "Contenuti",
        "contenuto del modulo": "Contenuti",
        "programma del corso": "Contenuti",
        # metodi
        "metodi didattici": "Metodi didattici",
        "metodologia didattica": "Metodi didattici",
        # verifica
        "verifica dell apprendimento": "Verifica dell'apprendimento",
        "valutazione dell apprendimento": "Verifica dell'apprendimento",
        # altro / risorse / testi
        "altro": "Altro",
        "risorse online": "Risorse online",
        "testi": "Testi",
        "testi d esame": "Testi",
        "testi esame": "Testi",
        "testi di esame": "Testi",
    }

    # Helper: scegli il "miglior" valore fra due (preferisci non vuoto; poi quello più lungo)
    def _choose_better(old, new):
        old_s = ("" if old is None else str(old)).strip()
        new_s = ("" if new is None else str(new)).strip()
        if old_s and not new_s:
            return old
        if new_s and not old_s:
            return new
        # entrambi valorizzati: tieni il più lungo per perdere meno info
        return new if len(new_s) > len(old_s) else old

    # 1) raccogli in un buffer tutti i candidati (dopo normalizzazione + sinonimi)
    collected = {}

    if isinstance(sezioni, dict):
        # Informazioni generali
        info_gen = sezioni.get("Informazioni generali")
        if isinstance(info_gen, dict):
            for k, v in info_gen.items():
                key_std = syn.get(_canon(k), None)
                if key_std in headers:
                    collected[key_std] = _choose_better(collected.get(key_std), v)

        # Altre sezioni
        for k, v in sezioni.items():
            if k == "Informazioni generali":
                continue
            key_c = _canon(k)
            key_std = syn.get(key_c, None)
            if isinstance(v, dict):
                # Sezione strutturata non mappata: prova a pescare testo utile
                # (qui puoi specializzare se alcune sezioni strutturate vanno mappate)
                for subk, subv in v.items():
                    sub_std = syn.get(_canon(subk), None)
                    if sub_std in headers:
                        collected[sub_std] = _choose_better(collected.get(sub_std), subv)
            else:
                if key_std in headers:
                    collected[key_std] = _choose_better(collected.get(key_std), v)

    # 2) costruisci l'output con TUTTI gli header (missing -> None)
    final = {h: collected.get(h, None) for h in headers}
    return final

# -----------------------------
# Utilità di normalizzazione
# -----------------------------
def _norm(s: str | None) -> str:
    """Normalizza spazi/NBSP e comprime righe vuote consecutive, mantenendo i \n tra paragrafi."""
    if not s:
        return ""
    s = s.replace("\xa0", " ")
    # compatta spazi multipli dentro la singola riga
    lines = [re.sub(r"[ \t]+", " ", L.strip()) for L in s.splitlines()]
    out: List[str] = []
    prev_blank = False
    for L in lines:
        blank = (L == "")
        if blank and prev_blank:
            continue
        out.append(L)
        prev_blank = blank
    return "\n".join(out).strip()


# -----------------------------
# Browser/context manager
# -----------------------------
@asynccontextmanager
async def _launch_browser(headless: bool = True):
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        context = await browser.new_context()
        try:
            yield context
        finally:
            await context.close()
            await browser.close()


# -----------------------------
# Scraper di una singola pagina
# -----------------------------
async def _scrape_single_insegnamento(
    id_corso: str,
    context,
    url: str,
    timeout_ms: int = 20000,
    retries: int = 2
) -> Dict[str, Any]:
    import re
    last_exc: Optional[Exception] = None

    for attempt in range(retries + 1):
        page = await context.new_page()
        try:
            # 1) Carica e attendi Angular
            await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            await page.wait_for_selector(".pageTitle h1.corso-title, h1.corso-title", timeout=timeout_ms)
            await page.wait_for_selector(".insegnamento-accordion dl.accordion", timeout=timeout_ms)

            # 2) Titolo del corso
            title = None
            for sel in [".pageTitle h1.corso-title", "h1.corso-title", ".pageTitle h1", "h1"]:
                loc = page.locator(sel).first
                if await loc.count():
                    txt = _norm(await loc.inner_text())
                    if txt:
                        title = txt
                        break

            # 3) Sezioni top-level: dt (titolo) + dd (contenuto)
            dts = page.locator(".insegnamento-accordion dl.accordion > dt")
            sezioni: Dict[str, Any] = {}

            dt_count = await dts.count()
            for i in range(dt_count):
                dt_node = dts.nth(i)

                # Apri la sezione se non è già aperta (classe 'open')
                try:
                    cls = (await dt_node.get_attribute("class")) or ""
                    if "open" not in cls:
                        await dt_node.click()
                        # aspetta il suo dd immediato
                        await dt_node.locator("xpath=following-sibling::dd[1]").wait_for(timeout=timeout_ms)
                except Exception:
                    pass

                # Titolo sezione
                header_text = None
                header_loc = dt_node.locator(".flex-container").first
                if await header_loc.count():
                    header_text = _norm(await header_loc.inner_text())
                if not header_text:
                    header_text = _norm(await dt_node.inner_text())
                if not header_text:
                    continue

                # dd associato (fratello immediato) — USA XPATH, non CSS!
                dd_node = dt_node.locator("xpath=following-sibling::dd[1]").first
                if not await dd_node.count():
                    continue

                # Caso A: sotto-tabella <dl> interna (es. "Informazioni generali")
                subdata: Dict[str, str] = {}
                inner_dts = dd_node.locator("dl > dt, dt[title]")
                inner_count = await inner_dts.count()

                if inner_count > 0:
                    for k in range(inner_count):
                        sdt = inner_dts.nth(k)
                        key = (await sdt.get_attribute("title")) or _norm(await sdt.inner_text())
                        key = _norm(key)

                        # dd del sotto-dt — USA XPATH, non CSS!
                        sdd = sdt.locator("xpath=following-sibling::dd[1]").first
                        val = ""
                        if await sdd.count():
                            val = _norm(await sdd.inner_text())
                            if not val:
                                val = _norm(await sdd.evaluate("el => el.textContent"))

                        if key:
                            subdata[key] = val

                    if subdata:
                        sezioni[header_text] = subdata
                        continue

                # Caso B: testo libero
                content_text = _norm(await dd_node.inner_text())
                if not content_text:
                    content_text = _norm(await dd_node.evaluate("el => el.textContent"))
                sezioni[header_text] = content_text

            # 4) Estrai CFU da "Informazioni generali"
            cfu: Optional[int] = None
            info_keys = (
                "Informazioni generali",
                "Informazioni generali  del modulo",
                "Informazioni generali del modulo",
            )
            info_gen: Optional[Dict[str, str]] = None
            for k in info_keys:
                v = sezioni.get(k)
                if isinstance(v, dict):
                    info_gen = v
                    break

            if info_gen:
                cred = info_gen.get("Crediti") or info_gen.get("Crediti ")
                if cred:
                    m = re.search(r"(\d+)\s*CFU", cred, flags=re.I)
                    if m:
                        try:
                            cfu = int(m.group(1))
                        except Exception:
                            cfu = None

            hash_part = hashlib.sha1(title.encode("utf-8")).hexdigest()[:10]
            id_insegnamento=f"I-{hash_part}"
            flat_sezioni = flatten_sezioni_special(sezioni)
            

            result = {
                "id_insegnamento": id_insegnamento,
                "id_corso": id_corso,
                "title": title,
                "cfu": cfu,
                "source_url": url,
                **flat_sezioni,
            }

            await page.close()
            return result

        except Exception as e:
            last_exc = e
            try:
                await page.close()
            except Exception:
                pass
            await asyncio.sleep(0.5 * (attempt + 1))

    return {
        "id_insegnamento": f"I-ERROR-{hashlib.sha1(url.encode('utf-8')).hexdigest()[:10]}",
        "id_corso": id_corso,
        "title": None,
        "cfu": None,
        "source_url": url,
        "Corso di studi": None,
        "Tipo di corso": None,
        "Anno di offerta": None,
        "Anno di corso": None,
        "Lingua": None,
        "Crediti": None,
        "Docenti": None,
        "Sede": None,
        "Prerequisiti": None,
        "Obiettivi formativi": None,
        "Contenuti": None,
        "Metodi didattici": None,
        "Verifica dell'apprendimento": None,
        "Risorse online": None,
        "Altro": None,
        "error": str(last_exc) if last_exc else "Unknown error",
    }


# -----------------------------
# Batch asincrono
# -----------------------------
async def scrape_insegnamenti_async(
    id_corso: str,
    urls: List[str],
    concurrency: int = 6,
    timeout_ms: int = 20000
) -> List[Dict[str, Any]]:
    """
    Esegue lo scraping in parallelo di tutte le pagine in `urls` con limite di concorrenza.
    """
    sem = asyncio.Semaphore(concurrency)
    results: List[Dict[str, Any]] = []

    async with _launch_browser(headless=True) as context:

        async def worker(u: str):
            async with sem:
                return await _scrape_single_insegnamento(id_corso, context, u, timeout_ms=timeout_ms)

        tasks = [asyncio.create_task(worker(u)) for u in urls]
        for t in asyncio.as_completed(tasks):
            res = await t
            results.append(res)

    return results


# -----------------------------
# Wrapper sincrono
# -----------------------------
def scrape_insegnamenti(
    id_corso: str,
    urls: List[str],
    concurrency: int = 6,
    timeout_ms: int = 20000
) -> List[Dict[str, Any]]:
    """
    Wrapper sincrono per usare la funzione asincrona in qualsiasi script.
    """
    return asyncio.run(scrape_insegnamenti_async(id_corso, urls, concurrency=concurrency, timeout_ms=timeout_ms))
