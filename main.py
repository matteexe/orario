from flask import Flask,request,Response,render_template
import tempfile,os
from parser_orario import leggi_pdf_orario,genera_xml,leggi_pdf_potenziamento,genera_xml_sostegno


app=Flask(__name__)
LEZIONI=[]
XML_SOSTEGNO=None
VERSIONE="v0.2.0"

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
    global LEZIONI,XML_SOSTEGNO
    if request.method=="GET":
        return render_template("index.html",versione=VERSIONE)

    f1=request.files.get("pdf1")
    f2=request.files.get("pdf2")
    f_pot=request.files.get("pdf_potenziamento")

    has_normale=(f1 and f1.filename) or (f2 and f2.filename)
    has_pot=f_pot and f_pot.filename

    if not has_normale and not has_pot:
        return render_template("index.html",versione=VERSIONE,errore="Carica almeno un PDF.")

    XML_SOSTEGNO=None
    classi=[]  

    with tempfile.TemporaryDirectory() as tmp:
        if has_normale:
            if f1 and f1.filename:
                p1=os.path.join(tmp,"orario1.pdf")
                f1.save(p1)
                lez1=leggi_pdf_orario(p1)
            else:
                lez1=[]
            if f2 and f2.filename:
                p2=os.path.join(tmp,"orario2.pdf")
                f2.save(p2)
                lez2=leggi_pdf_orario(p2)
            else:
                lez2=[]
            LEZIONI=lez1+lez2

            
            classi=sorted({l["classe"] for l in LEZIONI if l.get("classe")})

            risultato=genera_xml(LEZIONI)
            if isinstance(risultato,tuple):
                xml_classi,xml_materie=risultato
            else:
                xml_classi=risultato
                xml_materie=None
        else:
            xml_classi=None
            xml_materie=None

        if has_pot:
            p_pot=os.path.join(tmp,"potenziamento.pdf")
            f_pot.save(p_pot)
            dati_pot=leggi_pdf_potenziamento(p_pot)
            if dati_pot:
                XML_SOSTEGNO=genera_xml_sostegno(dati_pot)

        ha_orario=xml_classi is not None
        has_materie=xml_materie is not None
        has_sostegno=XML_SOSTEGNO is not None

        print("DEBUG has_normale/has_pot:",has_normale,has_pot)
        print("DEBUG xml_classi is not None:",xml_classi is not None)
        print("DEBUG XML_SOSTEGNO is not None:",XML_SOSTEGNO is not None)
        print("DEBUG classi:",classi)

        return render_template(
            "seleziona.html",
            versione=VERSIONE,
            classi=classi,          
            has_orario=ha_orario,
            has_materie=has_materie,
            has_sostegno=has_sostegno
        )


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
@app.route("/download_orario")
def download_orario():
    return download()

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

@app.route("/download_sostegno")
def download_sostegno():
    global XML_SOSTEGNO
    if not XML_SOSTEGNO:
        return "Nessun file di sostegno generato.",400
    return Response(
        XML_SOSTEGNO,
        mimetype="application/xml",
        headers={"Content-Disposition":"attachment; filename=sostegno.xml"}
    )

if __name__=="__main__":
    port=int(os.environ.get("PORT",8000))
    app.run(host="0.0.0.0",port=port)
