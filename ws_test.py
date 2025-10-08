from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Crea l'istanza del driver Chrome usando Selenium Manager 
driver = webdriver.Chrome()

# Apri la pagina desiderata
driver.get('https://unibg.coursecatalogue.cineca.it/insegnamenti/2025/21011-1/2025/9170/1363?coorte=2025&schemaid=77517&adCodRadice=21011')
#selezione la parte interessata
selector = 'dd+ dt'
#Attendo che gli elementi siano presenti
links = WebDriverWait(driver, 60).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
)

# Itera su ogni elemento in links
for link in links:
    try:
        # Clicca sull'elemento per rivelare il contenuto
        link.click()
        
        
    except Exception as e:
        print(f"Errore durante il clic su un elemento: {e}")

content_selector = '.accordion'
contents = WebDriverWait(driver, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, content_selector)))
 
all_data = []

title_selector = '.u-filetto'
titles = WebDriverWait(driver, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, title_selector)))


# Estrazione dei dati
for title in titles:
    title = title.text.strip()  
    id_corso = title.split("]")[0].strip("[")     
    titolo_corso = title.split(" - ")[1]          

# Creazione del dizionario
corso = {
    "id": id_corso,
    "titolo": titolo_corso
}

all_data.append(corso)


for dl in contents:
    dt_elements = dl.find_elements(By.TAG_NAME, "dt")
    dd_elements = dl.find_elements(By.TAG_NAME, "dd")

    data = {}
    for dt, dd in zip(dt_elements, dd_elements):
        key = dt.text.strip()
        value = dd.text.strip()
        data[key] = value

    all_data.append(data)
# for content in contents:
#    print(content.text)
# Rimuovi la chiave 'Informazioni generali' se esiste
data.pop('Informazioni generali', None)

# Unione dei due dizionari
insegnamento = {**all_data[0], **all_data[1]}
print(insegnamento)

# Chiudi il driver
driver.quit()

