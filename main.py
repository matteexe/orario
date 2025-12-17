from flask import Flask,request,Response,render_template
import tempfile,os
from parser_orario import leggi_pdf_orario,genera_xml

app=Flask(__name__)
LEZIONI=[]
VERSIONE="v0.1.0"

def _salva_pdf(fs,tmpdir,filename):
    if not fs or not fs.filename:
        return None
    if not fs.filename.lower().endswith(".pdf"):
        return None
    try:
        pos=fs.stream.tell()
        head=fs.stream.read(5)
        fs.stream.seek(pos)
    except Exception:
        return None
    if head!=b"%PDF-":
        return None
    path=os.path.join(tmpdir,filename)
    fs.save(path)
    if not os.path.exists(path) or os.path.getsize(path)==0:
        return None
    return path

@app.route("/",methods=["GET","POST"])
def index():
    global LEZIONI
    if request.method=="GET":
        return render_template("index.html",versione=VERSIONE)

    f1=request.files.get("pdf1")
    f2=request.files.get("pdf2")

    with tempfile.TemporaryDirectory() as tmp:
        p1=_salva_pdf(f1,tmp,"orario1.pdf")
        p2=_salva_pdf(f2,tmp,"orario2.pdf")

        if not p1 and not p2:
            return "Carica almeno un PDF valido",400

        lezioni1=leggi_pdf_orario(p1) if p1 else []
        lezioni2=leggi_pdf_orario(p2) if p2 else []

    lezioni=lezioni1+lezioni2
    if not lezioni:
        return "Nessuna lezione trovata",400

    LEZIONI=lezioni
    classi=sorted({l["classe"] for l in LEZIONI if l.get("classe")})
    return render_template("seleziona.html",classi=classi,versione=VERSIONE)

@app.route("/download",methods=["POST"])
def download():
    if not LEZIONI:
        return "Nessun orario in memoria, carica prima i PDF.",400

    tutte=request.form.get("tutte")
    selezionate=request.form.getlist("classi")

    if tutte:
        classi=None
    else:
        classi=[c for c in selezionate if c]
        if not classi:
            return "Nessuna classe selezionata.",400

    xml_str=genera_xml(LEZIONI,classi)
    return Response(
        xml_str,
        mimetype="application/xml",
        headers={"Content-Disposition":"attachment; filename=orario.xml"}
    )

@app.route("/materie.txt")
def materie_txt():
    if not LEZIONI:
        return "Nessun orario in memoria, carica prima i PDF.",400
    materie=sorted({l["materia"] for l in LEZIONI if l.get("materia")})
    testo="\n".join(materie)
    return Response(
        testo,
        mimetype="text/plain",
        headers={"Content-Disposition":"attachment; filename=materie.txt"}
    )

if __name__=="__main__":
    port=int(os.environ.get("PORT",8000))
    app.run(host="0.0.0.0",port=port)
