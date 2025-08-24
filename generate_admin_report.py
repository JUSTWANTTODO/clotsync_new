import json
from reports import generate_ai_report

# Read the HTML template
with open("templates/report.html", "r", encoding="utf-8") as f:
    html = f.read()

# Generate the report
report = generate_ai_report("donors_data.csv")

# Inject the JSON into the template
html_out = html.replace("__REPORT_JSON__", json.dumps(report, ensure_ascii=False))

# Write the output file
with open("admin_report.html", "w", encoding="utf-8") as f:
    f.write(html_out)

print("admin_report.html generated. Open it in your browser.")
