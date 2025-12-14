from flask import Flask,request,Response
import tempfile,os
from parser_orario import leggi_pdf_orario,genera_xml
import os

app=Flask(__name__)
xml_mem=None

form_html="""
<!doctype html><html><head><meta charset="utf-8"><title>Da PDF a XML</title></head>
<body>
<h1>Converti Orario</h1>
<form method="post" enctype="multipart/form-data">
<input type="file" name="pdf" accept="application/pdf" required>
<button type="submit">Converti</button>
</form>
</body></html>
"""

def pagina_ok(n):
    return f"""
<!doctype html><html><head><meta charset="utf-8"><title>OK</title></head>
<body>
<h1>Parsing completato</h1>
<p>Lezioni trovate: <b>{n}</b></p>
<p><a href="/download">Scarica XML</a></p>
</body></html>
"""

@app.route("/",methods=["GET","POST"])
def index():
    global xml_mem
    if request.method=="GET": return form_html
    if "pdf" not in request.files: return "Nessun file",400
    f=request.files["pdf"]
    if not f.filename: return "File non valido",400
    with tempfile.TemporaryDirectory() as tmp:
        p=os.path.join(tmp,"orario.pdf")
        f.save(p)
        lez=leggi_pdf_orario(p)
        if not lez: return "Nessuna lezione trovata",400
        xml_mem=genera_xml(lez)
    return pagina_ok(len(lez))

@app.route("/download")
def download():
    global xml_mem
    return Response(xml_mem,mimetype="application/xml",
                    headers={"Content-Disposition":"attachment; filename=orario.xml"})

if __name__=="__main__":
    port=int(os.environ.get("PORT",8000))
    app.run(host="0.0.0.0",port=port)
