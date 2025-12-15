from flask import Flask, request, Response, render_template
import tempfile, os
from parser_orario import leggi_pdf_orario, genera_xml

app = Flask(__name__)
xml_mem = None
VERSIONE = "v0.0.5"

@app.route("/", methods=["GET", "POST"])
def index():
    global xml_mem
    if request.method == "GET":
        return render_template("index.html", versione=VERSIONE)

    if "pdf" not in request.files:
        return "Nessun file", 400

    f = request.files["pdf"]
    if not f.filename:
        return "File non valido", 400

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "orario.pdf")
        f.save(path)

        lezioni = leggi_pdf_orario(path)
        if not lezioni:
            return "Nessuna lezione trovata", 400

        xml_mem = genera_xml(lezioni)

    return render_template("ok.html", n=len(lezioni), versione=VERSIONE)

@app.route("/download")
def download():
    global xml_mem
    return Response(
        xml_mem,
        mimetype="application/xml",
        headers={"Content-Disposition": "attachment; filename=orario.xml"}
    )

if __name__=="__main__":
    #riga che server solo per l'host 
    port=int(os.environ.get("PORT",8000))
    
    app.run(host="0.0.0.0",port=port)
