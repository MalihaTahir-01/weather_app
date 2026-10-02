import csv
import io
import json
from xml.etree import ElementTree as ET


def to_json(records: list) -> str:
    return json.dumps(records, indent=2)


def to_csv(records: list) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow([
        "id", "location", "resolved_name", "country", "latitude", "longitude",
        "start_date", "end_date", "date", "temp_max_c", "temp_min_c",
        "temp_mean_c",
    ])
    # One row per day, so the file opens cleanly in Excel
    for r in records:
        for d in r["temperature_data"]:
            writer.writerow([
                r["id"], r["location_query"], r["resolved_name"], r["country"],
                r["latitude"], r["longitude"], r["start_date"], r["end_date"],
                d["date"], d["temp_max_c"], d["temp_min_c"], d["temp_mean_c"],
            ])
    return out.getvalue()


def to_markdown(records: list) -> str:
    lines = ["# Weather Records", ""]
    for r in records:
        lines += [
            f"## Record {r['id']}: {r['location_query']}",
            f"- **Resolved location:** {r['resolved_name']}",
            f"- **Coordinates:** {r['latitude']}, {r['longitude']}",
            f"- **Date range:** {r['start_date']} to {r['end_date']}",
            "",
            "| Date | Max (°C) | Min (°C) | Mean (°C) |",
            "|---|---|---|---|",
        ]
        for d in r["temperature_data"]:
            lines.append(
                f"| {d['date']} | {d['temp_max_c']} | {d['temp_min_c']} "
                f"| {d['temp_mean_c']} |"
            )
        lines.append("")
    return "\n".join(lines)


def to_xml(records: list) -> str:
    root = ET.Element("weather_records")
    for r in records:
        rec = ET.SubElement(root, "record", id=str(r["id"]))
        for key in ("location_query", "resolved_name", "country", "latitude",
                    "longitude", "start_date", "end_date"):
            ET.SubElement(rec, key).text = str(r[key])
        temps = ET.SubElement(rec, "temperature_data")
        for d in r["temperature_data"]:
            day = ET.SubElement(temps, "day", date=d["date"])
            ET.SubElement(day, "temp_max_c").text = str(d["temp_max_c"])
            ET.SubElement(day, "temp_min_c").text = str(d["temp_min_c"])
            ET.SubElement(day, "temp_mean_c").text = str(d["temp_mean_c"])
    ET.indent(root)
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def to_pdf(records: list) -> bytes:
    from fpdf import FPDF  # imported here so other formats work without it

    def clean(text) -> str:
        # The built-in PDF font only supports Latin-1 characters
        return str(text).encode("latin-1", "replace").decode("latin-1")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Weather Records", new_x="LMARGIN", new_y="NEXT")

    for r in records:
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, clean(f"Record {r['id']}: {r['location_query']}"),
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=10)
        pdf.multi_cell(0, 6, clean(f"Location: {r['resolved_name']}"))
        pdf.cell(0, 6, clean(f"Dates: {r['start_date']} to {r['end_date']}"),
                 new_x="LMARGIN", new_y="NEXT")
        for d in r["temperature_data"]:
            pdf.cell(
                0, 6,
                clean(f"  {d['date']}   max {d['temp_max_c']} C   "
                      f"min {d['temp_min_c']} C   mean {d['temp_mean_c']} C"),
                new_x="LMARGIN", new_y="NEXT",
            )
    return bytes(pdf.output())


FORMATS = {
    "json": (to_json, "application/json"),
    "csv": (to_csv, "text/csv"),
    "md": (to_markdown, "text/markdown"),
    "xml": (to_xml, "application/xml"),
    "pdf": (to_pdf, "application/pdf"),
}