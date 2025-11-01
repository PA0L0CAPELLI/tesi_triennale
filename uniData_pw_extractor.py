import time
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
import hashlib



# Crea l'istanza del driver Chrome usando Selenium Manager 
driver = webdriver.Chrome()

# Apri sito web
driver.get('https://unibg.coursecatalogue.cineca.it')

#accetta i cookies
accept_cookies_selector = 'c-p-bn'
accept_cookies = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, accept_cookies_selector)))
accept_cookies.click()

all_data_corsi = []
all_data_insegnamenti = []

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

for i in range(2,3):  # selezione per INDICE: 0,1,2,... (coincide con "0: Object", "1: Object", ...)
    driver.get('https://unibg.coursecatalogue.cineca.it')
    time.sleep(1)  # breve pausa per stabilità
    # ricarico la select ad ogni giro (anti-Stale)
    select_el = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ANNO_SELECT_CSS))
    )
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", select_el)

    sel = Select(select_el)

    # micro-retry contro StaleElementReference
    for _ in range(2):
        try:
            sel.select_by_index(i)  # <-- cambiato: per indice (minima modifica ma robusta su "0: Object")
            break
        except StaleElementReferenceException:
            select_el = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(By.CSS_SELECTOR, ANNO_SELECT_CSS))
            
            sel = Select(select_el)

    anno_value = sel.options[i].get_attribute("value")
    a_immatricolazione_selector = '#offerta-formativa'
    # attendo che si popolino/aggiornino i dipartimenti per quell'anno
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".u-font-text"))
    )
    
    print(f"[OK] Anno selezionato: {year_labels[i]}")
    anno_label = year_labels[i]
    #all_data.append({"anno_immatricolazione": anno_label})
    
    #entra nei dipartimenti------------------------------------------------------
    dipartimenti_selector = '.u-font-text'
    dipartimenti = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, dipartimenti_selector)))

    for i in range(len(dipartimenti)):
        select_el = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, a_immatricolazione_selector)))
        Select(select_el).select_by_value(anno_value)
        dipartimenti = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, dipartimenti_selector)))
        dipartimenti[i].click()


        name_dipartimento_selector = '.corsi-group-title'
        name_dipartimento = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, name_dipartimento_selector)))
        #all_data.append({"dipartimento": name_dipartimento.text.strip()})
        dipartimento_label = name_dipartimento.text.strip()

        name_dipartimento_selector = '.corsi-group-title'
        name_dipartimento = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, name_dipartimento_selector)))
        
        
        
        print({"anno_immatricolazione": anno_label, "dipartimento": name_dipartimento.text.strip()})
        








            # entra nei corsi-----------------------------------------------------
        corsi_selector = '#main-content a'
        corsi = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, corsi_selector))
            )

            #estrai tutti gli href dei link trovati
        links_corsi = []
        for corso in corsi:
                href = corso.get_attribute("href")
                if href:  # solo se l'attributo esiste
                    links_corsi.append(href)

            #accedi alle pagine web associate ai link
        for link in links_corsi:
                driver.get(link)  # naviga alla pagina del corso

                #ESTRAZIONE DATI CORSO
                #estrai il nome del corso
                name_corso_selector = '.u-filetto'
                name_corso = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, name_corso_selector))
                )
                name_corso = name_corso.text.strip()  
                id_corso = name_corso.split("]")[0].strip("[")     
                base = f"{id_corso.strip()}|{anno_label.strip()}"
                hash_part = hashlib.sha1(base.encode("utf-8")).hexdigest()[:10]
                id_corso=f"C-{hash_part}"    
                corso = {
                    "id_corso": id_corso,
                    "titolo_corso": name_corso,
                    "anno_immatricolazione": anno_label,
                    "dipartimento": dipartimento_label

                }

                #prendo il contenitore delle informazioni
                contenitore = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".accordion"))
                )
                
                # =========================
                # Sezione: Informazioni generali
                # =========================
                try:
                    # Trova il <dt> della sezione il cui <div> interno contiene il testo "Informazioni generali"
                    dt_info = contenitore.find_element(
                        By.XPATH,
                        ".//dt[.//div[contains(normalize-space(.), 'Informazioni generali')]]"
                    )
                    # Prende il <dd> immediatamente successivo: è il contenuto della sezione
                    dd_info = dt_info.find_element(By.XPATH, "following-sibling::dd[1]")

                    # Dentro il <dd> ci sono tanti sotto-blocchi <dl>, ognuno con una coppia <dt>(chiave) / <dd>(valore)
                    dls = dd_info.find_elements(By.XPATH, ".//dl[.//dt]")
                    for dl in dls:
                        # Estrae la chiave (testo del <dt>)
                        key = dl.find_element(By.TAG_NAME, "dt").text.strip()
                        # Prende il <dd> associato (il valore)
                        dd = dl.find_element(By.TAG_NAME, "dd")

                        # Inizializza contenuto testuale e (se presente) URL
                        text = ""
                        url = None
                        try:
                            # Se dentro il <dd> c'è un link <a>, usa il testo del link e cattura anche l'href
                            a = dd.find_element(By.TAG_NAME, "a")
                            text = a.text.strip()
                            url = a.get_attribute("href")
                        except:
                            try:
                                # Altrimenti, se c'è uno <span>, usa il testo dello span
                                text = dd.find_element(By.TAG_NAME, "span").text.strip()
                            except:
                                # Fallback: prendi tutto il testo del <dd>
                                text = dd.text.strip()

                        # Normalizza la chiave per evitare ritorni a capo/spazi strani
                        key_norm = key.replace("\n", " ").replace("\r", " ").strip()

                        # Salva nel dizionario con un prefisso per non confondere con altre sezioni
                        corso[f"corso_{key_norm}"] = text
                        # # Se c'è un URL (es. "Sito web"), salvalo in una colonna dedicata
                        # if url:
                        #     corso[f"corso_{key_norm}_url"] = url
                except:
                    # Se la sezione non esiste/è nascosta o cambia struttura, evita che il codice si blocchi
                    pass

                # =========================
                # Sezione: Programma, testi e obiettivi
                # =========================
                # default
                corso["programma_disponibile"] = False
                corso["corso_descrizione"] = "NON TROVATO"

                try:
                    # cerca un <dt> che contenga "programma" (case-insensitive)
                    dt = next(iter(contenitore.find_elements(
                        By.XPATH,
                        ".//dt[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'programma')]"
                    )), None)

                    if dt:
                        try: dt.click()
                        except: driver.execute_script("arguments[0].click();", dt)

                        dd = next(iter(dt.find_elements(By.XPATH, "following-sibling::dd[1]")), None)
                        txt = (dd.get_attribute("innerText") or "").strip() if dd else ""
                        if txt:
                            corso["programma_disponibile"] = True
                            corso["corso_descrizione"] = txt
                except Exception:
                    pass  # resta coi default
                
                
                all_data_corsi.append(corso)

                
                buttons = driver.find_elements(By.CSS_SELECTOR, ".active~ li+ li a")

                if buttons:
                    try:
                        btn_insegnamenti = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, ".active~ li+ li a"))
                        )
                        btn_insegnamenti.click()
                        print("✅ Bottone 'Insegnamenti offerti' cliccato correttamente.")
                    except Exception as e:
                        print(f"⚠️ Errore durante il click sul bottone: {e}")
                        driver.back()     # torna all’elenco corsi
                        continue          # passa al prossimo corso

                    # --- scraping della pagina insegnamenti ---
                    time.sleep(1)  # breve pausa per stabilità
                    # prendo i link degli insegnamenti
                    insegnamenti_selector = ".card-insegnamento-right"
                    insegnamenti = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, insegnamenti_selector))
                    )

                    # estrai tutti gli href dei link trovati
                    links_insegnamenti = []
                    base_url = driver.current_url

                    for insegnamento in insegnamenti:
                        # se 12 CFU controlla che ci siano 2 moduli, e prendi i link. Altrimenti prendi il link dell'insegnamento
                        has_12or9CFU = bool(insegnamento.find_elements(
                                By.XPATH,
                                ".//div[contains(@class,'card-insegnamento-footer')]"
                                "//div[contains(@class,'card-insegnamento-cfu')]["
                                "contains(translate(normalize-space(.),"
                                " 'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÈÉÌÒÙ', 'abcdefghijklmnopqrstuvwxyzàèéìòù'), '12 cfu')"
                                " or "
                                "contains(translate(normalize-space(.),"
                                " 'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÈÉÌÒÙ', 'abcdefghijklmnopqrstuvwxyzàèéìòù'), '9 cfu')]"
                            ))
                        if has_12or9CFU:
                            # 🔧 più tollerante: prendi l'anchor principale (non "h4 div a" rigido)
                            try:
                                a_main = insegnamento.find_element(By.CSS_SELECTOR, "h4 a[href], a[href]")
                                href_main = urljoin(base_url, a_main.get_attribute("href"))
                            except NoSuchElementException:
                                href_main = None

                            if not href_main:
                                continue  # nessun link valido nella card

                            driver.get(href_main)

                            try:
                                WebDriverWait(driver, 4).until(
                                    EC.presence_of_element_located((
                                        By.XPATH,
                                        "//div[contains(@class,'insegnamento-links')]"
                                        "//p[contains(translate(normalize-space(.),"
                                        " 'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÈÉÌÒÙ','abcdefghijklmnopqrstuvwxyzàèéìòù'),"
                                        " 'diviso in moduli')]"
                                    ))
                                )
                                div_moduli = driver.find_elements(By.CSS_SELECTOR, "div.insegnamento-links li a[href]")
                                for modulo in div_moduli:
                                    href = modulo.get_attribute("href")
                                    if href:
                                        links_insegnamenti.append(urljoin(driver.current_url, href))
                            except TimeoutException:
                                # Nessun div 'insegnamento-links' → salva comunque il link principale
                                links_insegnamenti.append(driver.current_url)

                            driver.back()
                            continue  # passa al prossimo insegnamento

                        else:
                            # ⛏️ PRIMA: href = insegnamento.get_attribute("href")  (sempre None sul <div>)
                            # ORA: prendi l’<a href> interno alla card
                            try:
                                a_main = insegnamento.find_element(By.CSS_SELECTOR, "h4 a[href], a[href]")
                                href = a_main.get_attribute("href")
                                if href:
                                    links_insegnamenti.append(urljoin(base_url, href))
                            except NoSuchElementException:
                                pass  # nessun link nella card: salta

                            

                        
                    #FUNZIONE PLAYWRIGHT PER GLI INSEGNAMENTI
                    
                    if links_insegnamenti:
                        print(f"\n🚀 Avvio scraping asincrono di {len(links_insegnamenti)} insegnamenti...")

                        dati = scrape_insegnamenti(id_corso, links_insegnamenti, concurrency=6, timeout_ms=25000)
                        all_data_insegnamenti.extend(dati)
                        print(f"✅ Raccolti {len(dati)} insegnamenti.")
                        print(f"Totale elementi in all_data_insegnamenti: {len(all_data_insegnamenti)}")
                    else:
                        print("⚠️ Nessun link insegnamento trovato.")
            
                    #torna al blocco INFO
                    driver.back()
                    # torna indietro alla pagina della lista corsi
                    driver.back()




                    
                   

                else:
                    print("⚠️ Nessun bottone 'Insegnamenti offerti' trovato — torno indietro.")
                    driver.back()   # TORNO alla lista dei corsi
                    continue        # passo al prossimo corso
                

         # === Percorso della cartella di output ===
        output_dir = "unibg_data"
        os.makedirs(output_dir, exist_ok=True)  # crea la cartella se non esiste

        # === 1️⃣ CORSI ===
        df_corsi = pd.DataFrame(all_data_corsi)
        csv_corsi = os.path.join(output_dir, "data_corsi_BG.csv")

        if not os.path.exists(csv_corsi):
            # crea il file con intestazione
            df_corsi.to_csv(csv_corsi, index=False, mode="w", header=True, encoding="utf-8")
        else:
            # aggiunge in coda senza riscrivere l'intestazione
            df_corsi.to_csv(csv_corsi, index=False, mode="a", header=False, encoding="utf-8")

        print(f"✅ Salvati {len(df_corsi)} corsi in {csv_corsi}")

        # === 2️⃣ INSEGNAMENTI ===
        df_insegnamenti = pd.DataFrame(all_data_insegnamenti)
        csv_insegnamenti = os.path.join(output_dir, "data_insgn_BG.csv")

        if not os.path.exists(csv_insegnamenti):
            df_insegnamenti.to_csv(csv_insegnamenti, index=False, mode="w", header=True, encoding="utf-8")
        else:
            df_insegnamenti.to_csv(csv_insegnamenti, index=False, mode="a", header=False, encoding="utf-8")

        print(f"✅ Salvati {len(df_insegnamenti)} insegnamenti in {csv_insegnamenti}")    


        
        #torna indietro ai dipartimenti
        driver.back()
        
    





    dipartimenti = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, dipartimenti_selector)))
    driver.back()


#ChiBGi il driver
driver.quit()








