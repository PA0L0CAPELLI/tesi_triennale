from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

# Crea l'istanza del driver Chrome usando Selenium Manager 
driver = webdriver.Chrome()

# Apri sito web
driver.get('https://unibg.coursecatalogue.cineca.it')

#accetta i cookies
accept_cookies_selector = 'c-p-bn'
accept_cookies = WebDriverWait(driver, 60).until(
    EC.element_to_be_clickable((By.ID, accept_cookies_selector)))
accept_cookies.click()

#seleziono l'anno di immatricolazione

a_immatricolazione_selector = '#offerta-formativa'
select_element = driver.find_element(By.CSS_SELECTOR, a_immatricolazione_selector)
select = Select(select_element) # crea un oggetto Select
selected_option = select.first_selected_option # ottieni l'opzione selezionata
print(selected_option.text)  

#entra nei dipartimenti------------------------------------------------------
dipartimenti_selector = '.u-font-text'
dipartimenti = WebDriverWait(driver, 60).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, dipartimenti_selector)))

for i in range(len(dipartimenti)):
   dipartimenti = WebDriverWait(driver, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, dipartimenti_selector)))
   dipartimenti[i].click()


   name_dipartimento_selector = '.corsi-group-title'
   name_dipartimento = WebDriverWait(driver, 60).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, name_dipartimento_selector)))
   print(name_dipartimento.text)

    # entra nei corsi-----------------------------------------------------
   corsi_selector = '#main-content a'
   corsi = WebDriverWait(driver, 60).until(
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
        name_corso = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, name_corso_selector))
        )

        #prendo il contenitore delle informazioni
        contenitore = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".accordion"))
        )
        # prendo l'ultimo dd
        last_dd = contenitore.find_element(By.XPATH, ".//dd[last()]")
        # scrollo fino a quell'elemento
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", last_dd)
        last_dd.click()
        # estraggo i dati dei primi e ultimi dd
        last_dt  = contenitore.find_element(By.XPATH, ".//dt[last()]").text
        first_dd = contenitore.find_element(By.XPATH, ".//dd[1]")
        last_dd = contenitore.find_element(By.XPATH, ".//dd[last()]").text    

        name_corso = name_corso.text.strip()  
        id_corso = name_corso.split("]")[0].strip("[")     
        name_corso = name_corso.split("]")[1]       
        corso = {
             "id": id_corso,
             "titolo": name_corso

         }
              # Trova tutti i blocchi <dl> dentro il contenitore principale
        blocchi = first_dd.find_elements(By.XPATH, ".//dl")

        for blocco in blocchi:
            # Etichetta (dt)
            chiave = blocco.find_element(By.TAG_NAME, "dt").text.strip()
            # Valore (dd)
            valore = blocco.find_element(By.TAG_NAME, "dd").text.strip()
            corso[chiave] = valore
        
        corso[last_dt] = last_dd

        print(corso)

        #entro nella pagina degli insegnamenti
        btn_insegnamenti=WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ".active~ li+ li a"))
        )
        btn_insegnamenti.click()
        #prendo i link degli insegnamenti
        insegnamenti_selector = '.flex-container a'
        insegnamenti = WebDriverWait(driver, 60).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, corsi_selector))
        )

        #estrai tutti gli href dei link trovati
        links_insegnamenti = []
        for insegnamento in insegnamenti:
            href = insegnamento.get_attribute("href")
            if href:  # solo se l'attributo esiste
                links_insegnamenti.append(href)

        print(len(links_insegnamenti))
        
        #torna al blocco INFO
        driver.back()
        # torna indietro alla pagina dei corsi
        driver.back()
    #torna indietro ai dipartimenti
   driver.back()

dipartimenti = WebDriverWait(driver, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, dipartimenti_selector)))
driver.back()
    




# # INSEGNAMENTO----------------------------------------------------------
# #----------------------------------------------------------------------
# #selezione la parte interessata
# selector = 'dd+ dt'
# #Attendo che gli elementi siano presenti
# links = WebDriverWait(driver, 60).until(
#     EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
# )

# # Itera su ogni elemento in links
# for link in links:
#     try:
#         # Clicca sull'elemento per rivelare il contenuto
#         link.click()
        
        
#     except Exception as e:
#         print(f"Errore durante il clic su un elemento: {e}")

# content_selector = '.accordion'
# contents = WebDriverWait(driver, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, content_selector)))
 
# all_data = []

# title_selector = '.u-filetto'
# titles = WebDriverWait(driver, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, title_selector)))


# # Estrazione dei dati
# for title in titles:
#     title = title.text.strip()  
#     id_corso = title.split("]")[0].strip("[")     
#     titolo_corso = title.split(" - ")[1]          

# # Creazione del dizionario
# corso = {
#     "id": id_corso,
#     "titolo": titolo_corso
# }

# all_data.append(corso)


# for dl in contents:
#     dt_elements = dl.find_elements(By.TAG_NAME, "dt")
#     dd_elements = dl.find_elements(By.TAG_NAME, "dd")

#     data = {}
#     for dt, dd in zip(dt_elements, dd_elements):
#         key = dt.text.strip()
#         value = dd.text.strip()
#         data[key] = value

#     all_data.append(data)
# # for content in contents:
# #    print(content.text)
# # Rimuovi la chiave 'Informazioni generali' se esiste
# data.pop('Informazioni generali', None)

# # Unione dei due dizionari
# insegnamento = {**all_data[0], **all_data[1]}
# print(insegnamento)
# #----------------------------------------------------------------------


# Chiudi il driver
driver.quit()

