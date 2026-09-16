#!/usr/bin/env python3

import csv
import re
import time
import requests
from pyproj import Transformer


# ============================================================
# FILER
# ============================================================

INPUT_FILE = "inaturalist_observations.csv"
OUTPUT_FILE = "artportalen_import.tsv"
ERROR_FILE = "artportalen_fel.log"

# Paus mellan API-anrop till iNaturalist
API_DELAY = 0.25

# iNaturalist API
INAT_API_URL = "https://api.inaturalist.org/v1/observations/{}"


# ============================================================
# KOORDINATSYSTEM
# ============================================================

# iNaturalist:
# WGS84 / EPSG:4326
#
# Artportalen:
# SWEREF 99 TM / EPSG:3006
#
# always_xy=True betyder:
# longitude, latitude
# ============================================================

TRANSFORMER = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:3006",
    always_xy=True
)


# ============================================================
# iNATURALIST-KOLUMNER
# ============================================================

INAT_FIELDS = [
    "id",
    "uuid",
    "observed_on_string",
    "observed_on",
    "time_observed_at",
    "time_zone",
    "user_id",
    "user_login",
    "user_name",
    "created_at",
    "updated_at",
    "quality_grade",
    "license",
    "url",
    "image_url",
    "sound_url",
    "tag_list",
    "description",
    "num_identification_agreements",
    "num_identification_disagreements",
    "captive_cultivated",
    "oauth_application_id",
    "place_guess",
    "latitude",
    "longitude",
    "positional_accuracy",
    "private_place_guess",
    "private_latitude",
    "private_longitude",
    "public_positional_accuracy",
    "geoprivacy",
    "taxon_geoprivacy",
    "coordinates_obscured",
    "positioning_method",
    "positioning_device",
    "species_guess",
    "scientific_name",
    "common_name",
    "iconic_taxon_name",
    "taxon_id",
]


# ============================================================
# ARTPORTALENS IMPORTKOLUMNER
# ============================================================

ARTPORTAL_FIELDS = [
    "Artnamn",
    "Antal",
    "Enhet",
    "Antal substrat",
    "Ålder-Stadium",
    "Kön",
    "Aktivitet",
    "Metod",
    "Lokalnamn",
    "Huvudlokal",
    "Ost",
    "Nord",
    "Noggrannhet",
    "Diffusion",
    "Djup min",
    "Djup max",
    "Höjd min",
    "Höjd max",
    "Startdatum",
    "Starttid",
    "Slutdatum",
    "Sluttid",
    "Publik kommentar",
    "Intressant kommentar",
    "Privat kommentar",
    "Ej återfunnen",
    "Dölj fyndet t.o.m.",
    "Andrahand",
    "Osäker artbestämning",
    "Ospontan",
    "Biotop",
    "Biotop-beskrivning",
    "Art som substrat",
    "Art som substrat beskrivning",
    "Substrat",
    "Substrat-beskrivning",
    "Offentlig samling",
    "Privat samling",
    "Samlings-nummer",
    "Bestämningsmetod",
    "Artbestämd av",
    "Artbestämd av (fritext)",
    "Bestämningsår",
    "Beskrivning artbestämning",
    "Bekräftad av",
    "Bekräftad av (fritext)",
    "Bekräftelseår",
    "Länk till BOLD/GenBank",
    "Med-observatör",
    "Med-observatör",
    "Med-observatör",
    "Med-observatör",
    "Med-observatör",
    "Med-observatör",
    "Med-observatör",
    "Med-observatör",
    "Med-observatör",
    "Med-observatör",
    "Externid",
    "Ej funnen",
]

if len(ARTPORTAL_FIELDS) != 60:
    raise RuntimeError(
        "Programmeringsfel: ARTPORTAL_FIELDS måste innehålla exakt 60 kolumner, "
        f"men innehåller {len(ARTPORTAL_FIELDS)}."
    )


# ============================================================
# HJÄLPFUNKTIONER
# ============================================================

def clean(value):
    if value is None:
        return ""
    return str(value).strip()


def parse_date(value):
    value = clean(value)

    if not value:
        return ""

    match = re.search(
        r"\d{4}-\d{2}-\d{2}",
        value
    )

    if match:
        return match.group(0)

    return ""


def parse_time(value):
    value = clean(value)

    if not value:
        return ""

    match = re.search(
        r"(?:T|\s)(\d{2}):(\d{2})",
        value
    )

    if match:
        return (
            match.group(1)
            + ":"
            + match.group(2)
        )

    return ""


# ============================================================
# KOORDINATER
# ============================================================

def convert_coordinates(latitude, longitude):
    """
    Konverterar WGS84 till SWEREF99 TM.

    In:
        latitude  = latitud
        longitude = longitud

    Ut:
        ost, nord som heltal
    """

    latitude = clean(latitude)
    longitude = clean(longitude)

    if not latitude or not longitude:
        return "", ""

    try:

        lat = float(
            latitude.replace(",", ".")
        )

        lon = float(
            longitude.replace(",", ".")
        )

        # WGS84 -> SWEREF99 TM
        ost, nord = TRANSFORMER.transform(
            lon,
            lat
        )

        # Artportalen ska ha heltal
        ost = int(round(ost))
        nord = int(round(nord))

        return str(ost), str(nord)

    except Exception:
        return "", ""


# ============================================================
# HÄMTA ALLA BILDLÄNKAR FRÅN INATURALIST
# ============================================================

def get_all_photo_urls(observation_id, fallback_image_url, session):
    """
    Hämtar en iNaturalist-observation via API och returnerar
    ALLA bildlänkar som hör till observationen.

    Vi använder iNaturalists API eftersom CSV-exportens
    image_url bara innehåller en bild.

    För varje foto används helst original-versionen.
    Om original-URL saknas används foto-URL:n från API:t.

    Om API-anropet misslyckas används image_url från CSV:n
    som reserv.
    """

    observation_id = clean(observation_id)

    if not observation_id:
        return [], "Saknar iNaturalist-ID"

    api_url = INAT_API_URL.format(observation_id)

    try:

        response = session.get(
            api_url,
            timeout=30
        )

        response.raise_for_status()

        payload = response.json()

        results = payload.get("results", [])

        if not results:
            return [], "Observation hittades inte i iNaturalist API"

        observation = results[0]

        photos = observation.get("photos", [])

        urls = []

        for photo in photos:

            if not isinstance(photo, dict):
                continue

            # Nya API-svar kan ha URL i "url".
            url = photo.get("url")

            if not url:
                url = photo.get("original_url")

            if not url:
                continue

            url = str(url).strip()

            # Om API:t ger medium/large/etc försöker vi
            # använda original-versionen.
            original_url = re.sub(
                r"/(?:square|small|medium|large|original)\.(jpg|jpeg)$",
                lambda m: "/original." + m.group(1),
                url,
                flags=re.IGNORECASE
            )

            if original_url not in urls:
                urls.append(original_url)

        # Om API:t inte gav några bilder:
        if not urls:

            fallback_image_url = clean(
                fallback_image_url
            )

            if fallback_image_url:
                return (
                    [fallback_image_url],
                    "API returnerade inga bilder; "
                    "använder image_url från CSV"
                )

            return [], "Observationen har inga bilder"

        return urls, ""

    except requests.RequestException as error:

        fallback_image_url = clean(
            fallback_image_url
        )

        if fallback_image_url:

            return (
                [fallback_image_url],
                "API-fel; använder image_url från CSV: "
                + str(error)
            )

        return [], "API-fel: " + str(error)

    except Exception as error:

        fallback_image_url = clean(
            fallback_image_url
        )

        if fallback_image_url:

            return (
                [fallback_image_url],
                "API-fel; använder image_url från CSV: "
                + str(error)
            )

        return [], "Fel vid hämtning av bilder: " + str(error)


# ============================================================
# LÄS INATURALIST
# ============================================================

def read_inaturalist():

    observations = []
    warnings = []

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.reader(
            f,
            delimiter=",",
            quotechar='"'
        )

        header = next(
            reader,
            None
        )

        if header is None:
            raise ValueError(
                "CSV-filen är tom."
            )

        print(
            "Antal rubriker:",
            len(header)
        )

        for line_number, values in enumerate(
            reader,
            start=2
        ):

            if not values:
                continue

            # ------------------------------------------------
            # NORMAL CSV-RAD
            # ------------------------------------------------

            if len(values) == len(INAT_FIELDS):

                row = dict(
                    zip(
                        INAT_FIELDS,
                        values
                    )
                )

                observations.append(
                    (line_number, row)
                )

                continue

            # ------------------------------------------------
            # FÖRSÖK REPARERA RAD SOM BLIVIT ETT FÄLT
            # ------------------------------------------------

            if len(values) == 1:

                try:

                    repaired = next(
                        csv.reader(
                            [values[0]],
                            delimiter=",",
                            quotechar='"'
                        )
                    )

                    if len(repaired) == len(INAT_FIELDS):

                        row = dict(
                            zip(
                                INAT_FIELDS,
                                repaired
                            )
                        )

                        observations.append(
                            (line_number, row)
                        )

                        continue

                except Exception:
                    pass

            warnings.append(
                "Rad "
                + str(line_number)
                + ": kunde inte tolkas."
            )

    return observations, warnings


# ============================================================
# KONVERTERA EN OBSERVATION
# ============================================================

def convert_observation(row, photo_urls):

    # --------------------------------------------------------
    # ART
    # --------------------------------------------------------

    art = clean(
        row.get("scientific_name")
    )

    if not art:
        art = clean(
            row.get("species_guess")
        )

    if not art:
        art = clean(
            row.get("common_name")
        )

    # --------------------------------------------------------
    # DATUM / TID
    # --------------------------------------------------------

    datum = parse_date(
        row.get("observed_on")
    )

    tid = parse_time(
        row.get("observed_on_string")
    )

    # --------------------------------------------------------
    # LOKAL
    # --------------------------------------------------------

    lokal = clean(
        row.get("place_guess")
    )

    # --------------------------------------------------------
    # KOORDINATER
    # --------------------------------------------------------

    ost, nord = convert_coordinates(
        row.get("latitude"),
        row.get("longitude")
    )

    # --------------------------------------------------------
    # NOGGRANNHET
    # --------------------------------------------------------

    noggrannhet = clean(
        row.get("public_positional_accuracy")
    )

    if not noggrannhet:
        noggrannhet = clean(
            row.get("positional_accuracy")
        )

    # Artportalen kräver att Noggrannhet är ett POSITIVT heltal.
    # iNaturalist kan ibland lämna public_positional_accuracy tomt
    # även när observationen har en positional_accuracy.
    try:
        if noggrannhet:
            noggrannhet = str(
                max(
                    1,
                    int(
                        round(
                            float(
                                noggrannhet.replace(",", ".")
                            )
                        )
                    )
                )
            )
        else:
            # Artportalen accepterar inte tomt värde här.
            # 1 m används endast som teknisk reserv om iNaturalist
            # saknar noggrannhetsuppgift helt.
            noggrannhet = "1"

    except (ValueError, TypeError):
        noggrannhet = "1"

    # --------------------------------------------------------
    # OBSERVATÖR
    # --------------------------------------------------------

    observer = clean(
        row.get("user_name")
    )

    if not observer:

        observer = clean(
            row.get("user_login")
        )

    # --------------------------------------------------------
    # ÖVRIGT
    # --------------------------------------------------------

    observation_id = clean(
        row.get("id")
    )

    license_name = clean(
        row.get("license")
    )

    # --------------------------------------------------------
    # ALLA FOTON
    #
    # Ett fynd = en rad.
    # Alla bildlänkar hamnar i Publik kommentar.
    #
    # Exempel:
    #
    # Foto 1: https://...
    # Foto 2: https://...
    # Foto 3: https://...
    # --------------------------------------------------------

    photo_lines = []

    for index, photo_url in enumerate(
        photo_urls,
        start=1
    ):

        photo_lines.append(
            "Foto "
            + str(index)
            + ": "
            + photo_url
        )

    inaturalist_url = (
        "https://www.inaturalist.org/observations/"
        + observation_id
    )

    comment_parts = photo_lines.copy()
    comment_parts.append(
        "iNaturalist: " + inaturalist_url
    )

    public_comment = " | ".join(comment_parts)

    # --------------------------------------------------------
    # DATA
    # --------------------------------------------------------

    data = {

        "Artnamn": art,

        "Antal": "1",

        "Enhet": "",

        "Antal substrat": "",

        "Ålder-Stadium": "",

        "Kön": "",

        "Aktivitet": "",

        "Metod": "",

        # Lokal
        "Lokalnamn": lokal,

        # Huvudlokal lämnas tomt.
        "Huvudlokal": "",

        # SWEREF99 TM
        # Heltal
        "Ost": ost,

        "Nord": nord,

        # Noggrannhet
        "Noggrannhet": noggrannhet,

        # Övriga koordinatfält
        "Diffusion": "",

        "Djup min": "",

        "Djup max": "",

        "Höjd min": "",

        "Höjd max": "",

        # Datum / tid
        "Startdatum": datum,

        "Starttid": tid,

        "Slutdatum": datum,

        "Sluttid": tid,

        # PUBLIK KOMMENTAR
        # Alla bildlänkar
        "Publik kommentar": public_comment,

        "Intressant kommentar": "",

        # Privat kommentar
        "iNaturalist licens: "
        "": ""
    }

    # Lägg licensen separat eftersom Python-dictionaryn
    # annars blir svårare att läsa.
    data["Privat kommentar"] = (
        "iNaturalist licens: "
        + license_name
        if license_name
        else ""
    )

    # --------------------------------------------------------
    # ÖVRIGA FÄLT
    # --------------------------------------------------------

    data.update({

        "Ej återfunnen": "",

        "Dölj fyndet t.o.m.": "",

        "Andrahand": "",

        "Osäker artbestämning": "",

        "Ospontan": "",

        "Biotop": "",

        "Biotop-beskrivning": "",

        "Art som substrat": "",

        "Art som substrat beskrivning": "",

        "Substrat": "",

        "Substrat-beskrivning": "",

        "Offentlig samling": "",

        "Privat samling": "",

        "Samlings-nummer": "",

        "Bestämningsmetod": "",

        "Artbestämd av": "",

        "Artbestämd av (fritext)": "",

        "Bestämningsår": "",

        "Beskrivning artbestämning": "",

        "Bekräftad av": "",

        "Bekräftad av (fritext)": "",

        "Bekräftelseår": "",

        "Länk till BOLD/GenBank": "",

        # ----------------------------------------------------
        # EXTERNID
        #
        # Prefixet "iNaturalist:" läggs framför ID:t.
        # ----------------------------------------------------
        "Externid": (
            "iNaturalist: "
            + observation_id
        ),

        "Ej funnen": "",
    })

    return data, observer


# ============================================================
# SKRIV ARTPORTALEN-TSV
# ============================================================

def write_tsv(converted):

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        writer = csv.writer(
            f,
            delimiter="\t",
            quotechar='"',
            lineterminator="\n"
        )

        # ----------------------------------------------------
        # RUBRIKER
        # ----------------------------------------------------

        writer.writerow(
            ARTPORTAL_FIELDS
        )

        # ----------------------------------------------------
        # DATA
        # ----------------------------------------------------

        for data, observer in converted:

            output = []

            observer_written = False

            for field in ARTPORTAL_FIELDS:

                # Artportalen har 10 kolumner med
                # samma rubrik "Med-observatör".
                #
                # Observatören skrivs i första.
                # Resten lämnas tomma.
                if field == "Med-observatör":

                    if not observer_written:

                        output.append(
                            observer
                        )

                        observer_written = True

                    else:

                        output.append("")

                else:

                    output.append(
                        data.get(
                            field,
                            ""
                        )
                    )

            writer.writerow(
                output
            )


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print(
        "=" * 60
    )

    print(
        " iNaturalist -> Artportalen"
    )

    print(
        " WGS84 -> SWEREF 99 TM"
    )

    print(
        " ALLA BILDLÄNKAR"
    )

    print(
        "=" * 60
    )

    print()

    # --------------------------------------------------------
    # HTTP SESSION
    # --------------------------------------------------------

    session = requests.Session()

    session.headers.update({
        "User-Agent": (
            "iNaturalist-Artportalen-import/1.0 "
            "(personal biodiversity data import)"
        )
    })

    # --------------------------------------------------------
    # LÄS FIL
    # --------------------------------------------------------

    try:

        observations, read_warnings = (
            read_inaturalist()
        )

    except FileNotFoundError:

        print(
            "❌ Hittar inte:",
            INPUT_FILE
        )

        print()

        print(
            "Kontrollera att filen heter:"
        )

        print(
            INPUT_FILE
        )

        return

    except Exception as error:

        print()

        print(
            "❌ Fel vid läsning:"
        )

        print(
            error
        )

        return

    print()

    print(
        "Observationer lästa:",
        len(observations)
    )

    print()

    # --------------------------------------------------------
    # KONVERTERA
    # --------------------------------------------------------

    converted = []

    validation_warnings = []

    total_photos = 0

    for index, (line_number, row) in enumerate(
        observations,
        start=1
    ):

        observation_id = clean(
            row.get("id")
        )

        print(
            f"[{index}/{len(observations)}] "
            f"Hämtar bilder för iNaturalist "
            f"{observation_id}..."
        )

        # ----------------------------------------------------
        # HÄMTA ALLA BILDER
        # ----------------------------------------------------

        photo_urls, photo_warning = (
            get_all_photo_urls(
                observation_id,
                row.get("image_url"),
                session
            )
        )

        if photo_warning:

            validation_warnings.append(
                "Rad "
                + str(line_number)
                + ": "
                + observation_id
                + ": "
                + photo_warning
            )

        print(
            "    Antal bilder:",
            len(photo_urls)
        )

        total_photos += len(
            photo_urls
        )

        # ----------------------------------------------------
        # KONVERTERA
        # ----------------------------------------------------

        data, observer = (
            convert_observation(
                row,
                photo_urls
            )
        )

        missing = []

        if not data["Artnamn"]:

            missing.append(
                "Artnamn"
            )

        if not data["Lokalnamn"]:

            missing.append(
                "Lokalnamn"
            )

        if not data["Startdatum"]:

            missing.append(
                "Startdatum"
            )

        if not data["Ost"]:

            missing.append(
                "Ost"
            )

        if not data["Nord"]:

            missing.append(
                "Nord"
            )

        if missing:

            validation_warnings.append(
                "Rad "
                + str(line_number)
                + ": saknar "
                + ", ".join(missing)
            )

        converted.append(
            (data, observer)
        )

        time.sleep(
            API_DELAY
        )

    # --------------------------------------------------------
    # SKRIV TSV
    # --------------------------------------------------------

    try:

        write_tsv(
            converted
        )

    except Exception as error:

        print()

        print(
            "❌ Kunde inte skapa TSV:"
        )

        print(
            error
        )

        return

    # --------------------------------------------------------
    # SKRIV LOGG
    # --------------------------------------------------------

    with open(
        ERROR_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        for warning in read_warnings:

            f.write(
                warning
                + "\n"
            )

        for warning in validation_warnings:

            f.write(
                warning
                + "\n"
            )

        if (
            not read_warnings
            and not validation_warnings
        ):

            f.write(
                "Inga varningar.\n"
            )

    # --------------------------------------------------------
    # RESULTAT
    # --------------------------------------------------------

    print()

    print(
        "=" * 60
    )

    print(
        "KLART"
    )

    print(
        "=" * 60
    )

    print()

    print(
        "Skapad fil:",
        OUTPUT_FILE
    )

    print(
        "Antal observationer:",
        len(converted)
    )

    print(
        "Antal bildlänkar:",
        total_photos
    )

    print()

    # --------------------------------------------------------
    # VISA FÖRSTA OBSERVATIONEN
    # --------------------------------------------------------

    if converted:

        first_data, first_observer = (
            converted[0]
        )

        print(
            "Första observationen:"
        )

        print(
            "  Artnamn:    ",
            first_data["Artnamn"]
        )

        print(
            "  Lokalnamn:  ",
            first_data["Lokalnamn"]
        )

        print(
            "  Ost:        ",
            first_data["Ost"],
            "(SWEREF 99 TM)"
        )

        print(
            "  Nord:       ",
            first_data["Nord"],
            "(SWEREF 99 TM)"
        )

        print(
            "  Startdatum: ",
            first_data["Startdatum"]
        )

        print(
            "  Foto:"
        )

        print(
            first_data["Publik kommentar"]
        )

        print(
            "  Externid:   ",
            first_data["Externid"]
        )

        print(
            "  Observatör: ",
            first_observer
        )

    print()

    # --------------------------------------------------------
    # VARNINGAR
    # --------------------------------------------------------

    total_warnings = (
        len(read_warnings)
        + len(validation_warnings)
    )

    if total_warnings:

        print(
            "⚠️ Antal varningar:",
            total_warnings
        )

        print()

        print(
            "Se:",
            ERROR_FILE
        )

    else:

        print(
            "✅ Alla obligatoriska uppgifter finns."
        )

        print(
            "✅ Alla bildlänkar hämtades utan varningar."
        )

    print()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
