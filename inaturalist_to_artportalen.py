#!/usr/bin/env python3

import csv
import re
from pyproj import Transformer


# ============================================================
# FILER
# ============================================================

INPUT_FILE = "inaturalist_observations.csv"
OUTPUT_FILE = "artportalen.tsv"
ERROR_FILE = "artportalen_fel.log"


# ============================================================
# KOORDINATSYSTEM
#
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

def convert_observation(row):

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
        row.get("time_observed_at")
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

    try:

        if noggrannhet:

            noggrannhet = str(
                int(
                    round(
                        float(
                            noggrannhet.replace(
                                ",",
                                "."
                            )
                        )
                    )
                )
            )

    except ValueError:

        noggrannhet = ""


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
    # FOTO
    #
    # Endast image_url används.
    #
    # Publik kommentar blir:
    #
    # Foto: https://static.inaturalist.org/...
    #
    # Ingen taxon_id
    # Ingen observations-URL
    # Ingen beskrivning
    # --------------------------------------------------------

    image_url = clean(
        row.get("image_url")
    )

    if image_url:

        public_comment = (
            "Foto: "
            + image_url
        )

    else:

        public_comment = ""


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
        #
        # Endast:
        # Foto: + image_url

        "Publik kommentar": public_comment,


        "Intressant kommentar": "",


        # Privat kommentar
        #
        # Licensen ligger fortfarande här,
        # inte i publik kommentar.

        "Privat kommentar": (
            "iNaturalist licens: "
            + license_name
            if license_name
            else ""
        ),


        # Övriga fält

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


        # iNaturalist ID

        "Externid": observation_id,


        "Ej funnen": "",
    }


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
        "=" * 60
    )

    print()


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

        print(
            "❌ Fel vid läsning:"
        )

        print(error)

        return


    print()

    print(
        "Observationer lästa:",
        len(observations)
    )


    # --------------------------------------------------------
    # KONVERTERA
    # --------------------------------------------------------

    converted = []

    validation_warnings = []


    for line_number, row in observations:

        data, observer = (
            convert_observation(row)
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

        print(error)

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
            "  Foto:       ",
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
            "Se:"
        )

        print(
            ERROR_FILE
        )

    else:

        print(
            "✅ Alla obligatoriska uppgifter finns."
        )


    print()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()