from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
import pandas as pd
import os
from openpyxl import load_workbook
from insegnamenti_pw_scraper import scrape_insegnamenti
from urllib.parse import urljoin
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import StaleElementReferenceException

def _select_year_once(driver, css_selector="#offerta-formativa", visible_text="2024/2025"):
    """
    Robustly select a single year in the year <select> without looping.
    - Scrolls into view
    - Handles stale elements by retrying a couple times
    - Falls back to partial text match if exact isn't found
    """
    attempts = 3
    last_err = None
    for _ in range(attempts):
        try:
            select_el = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector))
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", select_el)
            sel = Select(select_el)

            # Try exact visible text first
            try:
                sel.select_by_visible_text(visible_text)
                return True
            except Exception:
                # Fallback: find an option that contains the text "2024/2025"
                options = [o for o in sel.options if visible_text in o.text]
                if options:
                    options[0].click()
                    return True
                else:
                    # As last fallback, try to pick by value if it looks like "2025" or similar
                    for o in sel.options:
                        t = o.text.strip()
                        v = (o.get_attribute("value") or "").strip()
                        if "2024" in t and "2025" in t:
                            o.click()
                            return True
                        if v.endswith("2025") or v == "2025":
                            o.click()
                            return True
                    raise NoSuchElementException(f"Nessuna opzione contenente '{visible_text}'")
        except StaleElementReferenceException as e:
            last_err = e
            continue
        except Exception as e:
            last_err = e
            break
    if last_err:
        raise last_err
    return False




# Crea l'istanza del driver Chrome usando Selenium Manager 
driver = webdriver.Chrome()

# Apri sito web
driver.get('https://unibg.coursecatalogue.cineca.it')

#accetta i cookies
accept_cookies_selector = 'c-p-bn'
accept_cookies = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, accept_cookies_selector)))
accept_cookies.click()

all_data = []

# =========================
# seleziono l'anno di immatricolazione (minima modifica)
# =========================


ANNO_SELECT_CSS = "#offerta-formativa"  # id reale della select

# 1) prendo una sola volta QUANTI anni ci sono
_select_el = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, ANNO_SELECT_CSS))
)
_select = Select(_select_el)
num_years = len(_select.options)

# (alternativa: se preferisci per testo)
year_labels = [opt.text.strip() for opt in _select.options]


# Seleziona SOLO l'anno richiesto e prosegue senza loop
_select_year_once(driver, ANNO_SELECT_CSS, visible_text="2024/2025")

#Chiudi il driver
driver.quit()








