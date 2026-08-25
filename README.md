# iNaturalist → Artportalen

> Konverteringsverktyg för att omvandla iNaturalist-observationer till Artportalens importformat

---

## 📋 Översikt

Detta Python-skript konverterar observationer från **iNaturalist** (CSV-format) till **Artportalens** importformat (TSV). Skriptet hanterar:

- **Koordinatomvandling** från WGS84 (EPSG:4326) till SWEREF 99 TM (EPSG:3006)
- **Fältmappning** mellan iNaturalists och Artportalens datamodell
- **Datavalidering** för obligatoriska fält
- **Felhantering** med detaljerad loggning

---

## ⚙️ Förutsättningar

### Systemkrav

- Python 3.7 eller senare
- Minst 50 MB ledigt utökad minne per 10 000 observationer

### Python-paket

Skriptet kräver följande paket:

```bash
pip install pyproj
✅ pyproj används för koordinatomvandling och kräver PROJ-biblioteket systeminstallerat på vissa plattformar (Linux).

📥 Installation
1. Klona eller ladd ner
# Om du använder git
git clone <repository-url>
cd <mappnamn>

# Eller ladd ner filerna direkt
wget https://example.com/konvertering.py
2. Installera beroenden
pip install -r requirements.txt
Om du inte har en requirements.txt, installera manuellt:

pip install pyproj
🚀 Användning
Grundläggande användning
python inaturalist_to_artportalen.py
Steg-för-steg
Förbered din iNaturalist-data

Exportera dina observationer från iNaturalist som CSV
Filen måste heta inaturalist_observations.csv eller ändra INPUT_FILE i skriptet
Kör skriptet

python inaturalist_to_artportalen.py
Hämta resultaten

artportalen.tsv - Konverterade observationer redo för import
artportalen_fel.log - Logg med varningar och fel
📂 Filer
Fil	Beskrivning
inaturalist_observations.csv	Indata - iNaturalist-export (CSV)
artportalen.tsv	Utdata - Artportalen-import (TSV)
artportalen_fel.log	Logg - Fel och varningar
🔄 Konverteringsprocess
1. Koordinatomvandling
Indata: Latitud/Longitud (WGS84 / EPSG:4326)
Utdata: Ost/Nord (SWEREF 99 TM / EPSG:3006) som heltal
Hantering: Kommatecken i decimaltal konverteras till punkter
2. Fältmappning
Viktiga fältmappningar
iNaturalist	Artportalen	Beskrivning
scientific_name	Artnamn	Vetenskapligt namn (prioriteras)
species_guess	Artnamn	Artgissning (fallback)
common_name	Artnamn	Vanligt namn (fallback)
observed_on	Startdatum, Slutdatum	Observationsdatum (YYYY-MM-DD)
time_observed_at	Starttid, Sluttid	Observationstid (HH:MM)
place_guess	Lokalnamn	Platnamn
latitude, longitude	Ost, Nord	Koordinater (omvandlade)
public_positional_accuracy	Noggrannhet	Positionnoggrannhet (meter)
user_name / user_login	Med-observatör	Observatörens namn
image_url	Publik kommentar	Länk till foto (formaterad)
license	Privat kommentar	Licensinformation
id	Externid	iNaturalist-observations-ID
3. Standardvärden
Följande fält fylls med standardvärden:

Antal: 1 (varje observation = 1 individ)
Enhet: Tom
Startdatum = Slutdatum (samma datum)
Starttid = Sluttid (samma tid)
✅ Obligatoriska fält
Skriptet validerar att följande fält finns för varje observation:

✅ Artnamn - Artnamn (vetenskapligt, gissning eller vanligt namn)
✅ Lokalnamn - Platnamn
✅ Startdatum - Observationsdatum
✅ Ost - Ostkoordinat (SWEREF 99 TM)
✅ Nord - Nordkoordinat (SWEREF 99 TM)
⚠️ Observationer som saknar obligatoriska fält loggas i artportalen_fel.log men inkluderas ändå i utgående fil.

📝 Indataformat (iNaturalist CSV)
Skriptet förväntar sig följande kolumner i indatafilen:

id,uuid,observed_on_string,observed_on,time_observed_at,time_zone,user_id,user_login,user_name,created_at,updated_at,quality_grade,license,url,image_url,sound_url,tag_list,description,num_identification_agreements,num_identification_disagreements,captive_cultivated,oauth_application_id,place_guess,latitude,longitude,positional_accuracy,private_place_guess,private_latitude,private_longitude,public_positional_accuracy,geoprivacy,taxon_geoprivacy,coordinates_obscured,positioning_method,positioning_device,species_guess,scientific_name,common_name,iconic_taxon_name,taxon_id
Tips för iNaturalist-export
Använd Full Export för att få alla nödvändiga fält
Se till att latitude och longitude är inkluderade
Inkludera scientific_name för bästa artnamnsmatchning
📤 Utdataformat (Artportalen TSV)
Utdatafilen följer Artportalens import-specifikation med tab-separerade värden.

Kolumnöversikt
Kolumn	Typ	Beskrivning
Artnamn	Text	Artens namn
Antal	Numerisk	Antal observerade individer (alltid 1)
Enhet	Text	Enhet (tom)
Ost	Numerisk	Ostkoordinat (SWEREF 99 TM, heltal)
Nord	Numerisk	Nordkoordinat (SWEREF 99 TM, heltal)
Noggrannhet	Numerisk	Positionnoggrannhet i meter
Startdatum	Datum	Observationsdatum (YYYY-MM-DD)
Starttid	Tid	Observationstid (HH:MM)
Lokalnamn	Text	Platnamn
Publik kommentar	Text	Innehåller foto-länk om tillgänglig
Privat kommentar	Text	Innehåller licensinformation
Externid	Text	iNaturalist-observations-ID
Med-observatör	Text	Observatörens namn (första kolumnen)
📌 Notera: Artportalen har 10 kolumner med namnet "Med-observatör". Skriptet fyller endast den första med observatörens namn.

⚠️ Felhantering
Varningstyper
Läsfel - Rader som inte kan tolkas (felaktigt format)
Valideringsvarningar - Observationer som saknar obligatoriska fält
Loggfil
All varningar skrivs till artportalen_fel.log med följande format:

Rad 5: kunde inte tolkas.
Rad 12: saknar Artnamn, Startdatum, Ost
Inga varningar.
🔧 Anpassning
Ändra filnamn
Redigera följande konstanter i skriptet:

INPUT_FILE = "inaturalist_observations.csv"
OUTPUT_FILE = "artportalen.tsv"
ERROR_FILE = "artportalen_fel.log"
Ändra koordinatsystem
Om du behöver ett annat koordinatsystem, ändra:

TRANSFORMER = Transformer.from_crs(
    "EPSG:4326",  # Från: WGS84
    "EPSG:3006",  # Till: SWEREF 99 TM
    always_xy=True
)
📊 Exempel på körning
# 1. Förbered indata
# Ladd ner din iNaturalist-export som inaturalist_observations.csv

# 2. Kör konverteringen
$ python inaturalist_to_artportalen.py

============================================================
 iNaturalist -> Artportalen
 WGS84 -> SWEREF 99 TM
============================================================

Observationer lästa: 150

============================================================
KLART
============================================================

Skapad fil: artportalen.tsv
Antal observationer: 150

Första observationen:
  Artnamn:     Papilio machaon
  Lokalnamn:   Stockholm
  Ost:         6789123 (SWEREF 99 TM)
  Nord:        6543210 (SWEREF 99 TM)
  Startdatum:  2024-05-15
  Foto:        Foto: https://static.inaturalist.org/photos/123456789.jpg
  Externid:    123456789
  Observatör:  Användarnamn

✅ Alla obligatoriska uppgifter finns.
🎯 Tips och bästa praxis
1. Stora dataset
För >10 000 observationer: Kör skriptet med python -O för optimering
Minne: Ca 50 MB per 10 000 observationer
2. Testkörning
Testa med en liten subset av dina data först
Kontrollera artportalen_fel.log för varningar
3. Dataqualitet
Se till att alla observationer har koordinater
Kontrollera att scientific_name eller species_guess finns
Verifiera datumformat (YYYY-MM-DD)
4. Import till Artportalen
Ladd upp artportalen.tsv i Artportalens importverktyg
Använd TSV-format som indataformat
Kolumnrubrikerna matchar Artportalens förväntade format
🔍 Felsökning
Vanliga problem
"CSV-filen är tom"
Orsak: Indatafilen saknas eller är tom
Lösning: Kontrollera att inaturalist_observations.csv existerar och innehåller data
"Kunde inte skapa TSV"
Orsak: Skrivrättigheter saknas
Lösning: Kör skriptet med skrivrättigheter i mappen
"No module named 'pyproj'"
Orsak: pyproj är inte installerat
Lösning: pip install pyproj
Koordinater konverteras inte
Orsak: Ogiltigt koordinatformat
Lösning: Kontrollera att latitude/longitude är numeriska värden
"PROJ: proj_create_from_database: Cannot find proj.db"
Orsak: PROJ-databas saknas (Linux)
Lösning: Installera PROJ-paketet:
# Ubuntu/Debian
sudo apt-get install proj-bin libproj-dev

# Fedora/RHEL
sudo dnf install proj
📚 Teknisk information
Koordinatsystem
System	EPSG-kod	Beskrivning
WGS84	EPSG:4326	iNaturalist standard (lat/lon)
SWEREF 99 TM	EPSG:3006	Artportalen standard (ost/nord)
Datum- och tidshantering
Datumformat: YYYY-MM-DD (extraheras från observed_on)
Tidsformat: HH:MM (extraheras från time_observed_at)
Tidzonshantering: Ignoreras (använder lokal tid)
Teckenhantering
Indata: UTF-8 med BOM (utf-8-sig)
Utdata: UTF-8 med BOM (utf-8-sig)
Fältavgränsare indata: Komma (,)
Fältavgränsare utdata: Tab (\t)
📜 Versionshistorik
Version	Datum	Ändringar
1.0	2024	Första version
🤝 Bidra
Om du hittar buggar eller har förbättringsförslag:

Kontrollera att problemet inte redan är rapporterat
Skapa en tydlig beskrivning av problemet
Inkludera exempeldata om möjligt
📄 Licens
Detta skript är fritt att använda, modifiera och distribuera.

🙏 Acknowledgements
iNaturalist - Källa till observationsdata
Artportalen - Svenskt artdatabas
pyproj - Koordinatomvandlingsbibliotek
