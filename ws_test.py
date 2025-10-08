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

#entra nei dipartimenti
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

    # entra nei corsi
   corsi_selector = '#main-content a'
   corsi = WebDriverWait(driver, 60).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, corsi_selector))
    )

    # 1️⃣ estrai tutti gli href dei link trovati
   links_corsi = []
   for corso in corsi:
        href = corso.get_attribute("href")
        if href:  # solo se l'attributo esiste
            links_corsi.append(href)

    #2️⃣ accedi alle pagine web associate ai link
   for link in links_corsi:
        driver.get(link)  # naviga alla pagina del corso

        # 3️⃣ estrai il nome del corso
        name_corso_selector = '.u-filetto'
        name_corso = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, name_corso_selector))
        )
        print(name_corso.text)

        # opzionale: torna indietro alla pagina dei corsi
        driver.back()
    #torna indietro ai dipartimenti
   driver.back()

dipartimenti = WebDriverWait(driver, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, dipartimenti_selector)))
driver.back() #torna indietro ai dipartimenti
    




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

