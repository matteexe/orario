import pdfplumber
import xml.etree.ElementTree as ET
from collections import defaultdict
import re

GIORNI=["LUN","MAR","MER","GIO","VEN","SAB"]
GIORNI_NUM={"LUN":1,"MAR":2,"MER":3,"GIO":4,"VEN":5,"SAB":6}

RE_PAREN=re.compile(r"^(.*?)\((.*?)\)\s*$")
RE_DOCENTE=re.compile(r"^[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ''\-]+(?:\s+[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ''\-]+)*\s+[A-Z](?:\.[A-Z])*\.$")
RE_SIGLA=re.compile(r"([A-Za-z])\s*-\s*(\d)")

def pulisci(t):
    return (t or "").strip()

def normalizza_classe(nome):
    nome=pulisci(nome)
    if " - " in nome:
        nome=nome.split(" - ",1)[0].strip()
    nome=RE_SIGLA.sub(r"\1\2",nome)
    return nome

##attualmente non utilizzato
def split_cognome_nome(nominativo):
    nominativo=pulisci(nominativo)
    if not nominativo:
        return "",""
    parti=nominativo.split()
    if len(parti)<2:
        return nominativo,""
    return " ".join(parti[:-1]),parti[-1]

def docente_valido(s):
    s=pulisci(s)
    return bool(RE_DOCENTE.match(s))

def scegli_docente_sostituto(docente_raw):
    s=pulisci(docente_raw)
    m=RE_PAREN.match(s)
    if not m:
        return s
    fuori=pulisci(m.group(1))
    dentro=pulisci(m.group(2))
    segnali_ore=any(x in dentro.lower() for x in ["h","+","ore","lab","mobile"]) or any(ch.isdigit() for ch in dentro)
    if not segnali_ore and docente_valido(dentro):
        return dentro
    return fuori if fuori else s

def separa_docenti(docente_raw):
    s=pulisci(docente_raw)
    if not s:
        return []

    m=re.search(r"\(([^()]*)\)",s)
    if m:
        interno=pulisci(m.group(1))
        if docente_valido(interno):
            principale=interno
            dopo=s[m.end():]
            compresenze=[]
            for parte in dopo.split(" - "):
                nome=pulisci(parte)
                if nome and docente_valido(nome):
                    compresenze.append(nome)
            if compresenze:
                return [principale]+compresenze
            return [principale]

    base=scegli_docente_sostituto(s)
    if not base:
        return []
    if " - " in base:
        return [p.strip() for p in base.split(" - ") if p.strip()]
    return [base]

def pulisci_aula(aula_raw):
    if not aula_raw:
        return ""
    aula=pulisci(aula_raw)
    if "Lab. Mobile" in aula:
        parts=aula.split(" - ")
        if len(parts)>1:
            aula=parts[-1].strip()
        else:
            aula=re.sub(r'Lab\.\s*Mobile\s*\d*','',aula).strip()
    if " - " in aula:
        aula=aula.split(" - ")[0].strip()
    aula=RE_SIGLA.sub(r"\1\2",aula)
    return aula

def leggi_pdf_orario(percorso):
    lezioni=[]
    parziali={}

    with pdfplumber.open(percorso) as pdf:
        for pagina in pdf.pages:
            tabelle=pagina.extract_tables()
            if not tabelle:
                continue

            for tabella in tabelle:
                intestazione=tabella[0]
                nomi_classi=[]

                for i,c in enumerate(intestazione):
                    if i<2:
                        nomi_classi.append(None)
                    else:
                        nome=normalizza_classe(c)
                        nomi_classi.append(nome if nome else None)

                for idx_riga,riga in enumerate(tabella[1:],start=1):
                    giorno_raw=pulisci(riga[0])
                    if giorno_raw not in GIORNI:
                        continue

                    giorno=GIORNI_NUM[giorno_raw]
                    testo_orari=riga[1]
                    if not isinstance(testo_orari,str):
                        continue

                    orari=[x.strip() for x in testo_orari.split("\n") if x.strip()]

                    for i_ora in range(len(orari)):
                        riga_idx=idx_riga+i_ora
                        if riga_idx>=len(tabella):
                            break

                        ora=i_ora+1
                        riga_ora=tabella[riga_idx]

                        for col in range(2,len(riga_ora)):
                            classe=nomi_classi[col]
                            if not classe:
                                continue

                            testo=pulisci(riga_ora[col])
                            if not testo:
                                continue

                            linee=[x.strip() for x in testo.split("\n") if x.strip()]
                            chiave_prec=(classe,giorno,ora-1)

                            if ora>1 and chiave_prec in parziali:
                                linee=parziali[chiave_prec]+linee

                            materia=linee[0] if len(linee)>=1 else ""
                            docente_raw=linee[1] if len(linee)>=2 else ""
                            aula_raw=" ".join(linee[2:]) if len(linee)>=3 else ""

                            if len(linee)==1:
                                parziali[(classe,giorno,ora)]=linee
                                continue
                            else:
                                parziali.pop((classe,giorno,ora),None)

                            docenti=separa_docenti(docente_raw)
                            docente_principale=docenti[0] if len(docenti)>=1 else ""
                            compresenze=docenti[1:] if len(docenti)>1 else []

                            aula=pulisci_aula(aula_raw)

                            dati={
                                "classe":classe,
                                "giorno":giorno,
                                "ora":ora,
                                "materia":materia,
                                "docente":docente_principale,
                                "compresenze":compresenze,
                                "aula":aula
                            }
                            lezioni.append(dati)

                            if ora>1 and chiave_prec in parziali:
                                dup=dati.copy()
                                dup["ora"]=ora-1
                                lezioni.append(dup)
                                parziali.pop(chiave_prec,None)

    return lezioni

def genera_xml(lezioni,classi=None):
    root=ET.Element("classi")
    raggr=defaultdict(lambda:defaultdict(list))

    for l in lezioni:
        if classi and l["classe"] not in classi:
            continue
        raggr[l["classe"]][l["giorno"]].append(l)

    for classe in sorted(raggr.keys()):
        nodo_classe=ET.SubElement(root,"classe",{"nome":classe})

        for giorno in sorted(raggr[classe].keys()):
            nodo_giorno=ET.SubElement(nodo_classe,"giorno",{"nome":str(giorno)})
            lista=raggr[classe][giorno]
            lista.sort(key=lambda x:x["ora"])

            for l in lista:
                nodo_lez=ET.SubElement(nodo_giorno,"lezione")

                n=ET.SubElement(nodo_lez,"ora")
                n.text=str(l["ora"])

                n=ET.SubElement(nodo_lez,"materia")
                n.text=l["materia"]

                n=ET.SubElement(nodo_lez,"docente")
                n.text=l["docente"]

                for i in range(1,5):
                    if i-1<len(l["compresenze"]):
                        valore=l["compresenze"][i-1]
                    else:
                        valore="NO"
                    n=ET.SubElement(nodo_lez,f"compresenza{i}")
                    n.text=valore

                n=ET.SubElement(nodo_lez,"aula")
                n.text=l["aula"]

    return ET.tostring(root,encoding="utf-8",xml_declaration=True).decode("utf-8")

def leggi_pdf_potenziamento(percorso_pdf):
    import pdfplumber
    potenziamenti={}
    with pdfplumber.open(percorso_pdf) as pdf:
        for page in pdf.pages:
            tables=page.extract_tables()
            if not tables:
                continue
            tab=tables[0]
            if len(tab)<3:
                continue
            header_times=tab[1]
            time_indices=[i for i,c in enumerate(header_times) if c and "8.15" in c]
            if not time_indices:
                continue
            giorno_idx_by_col={}
            ora_by_col={}
            for day_idx,start_col in enumerate(time_indices,start=1):
                for offset in range(6):
                    col=start_col+offset
                    if col>=len(header_times):
                        break
                    giorno_idx_by_col[col]=day_idx
                    ora_by_col[col]=offset+1
            for row in tab[2:]:
                docente=row[0]
                if not docente:
                    continue
                if "(Sost.)" in docente:
                    continue
                docente=docente.strip()
                for col_idx,cell in enumerate(row[1:],start=1):
                    if col_idx not in giorno_idx_by_col:
                        continue
                    if not cell or "Potenz." not in cell:
                        continue
                    giorno_idx=giorno_idx_by_col[col_idx]
                    ora=ora_by_col[col_idx]
                    lines=[l.strip() for l in cell.split("\n") if l and l.strip()]
                    aula=None
                    for l in lines:
                        if "Aula" in l:
                            aula=l
                            break
                    if aula is None:
                        aula="Aula Potenziamento"
                    d_pot=potenziamenti.setdefault(docente,{})
                    d_giorno=d_pot.setdefault(giorno_idx,[])
                    d_giorno.append({"ora":ora,"classe":"Potenz.","aula":aula})
    return potenziamenti

def genera_xml_sostegno(potenziamenti):
    import xml.etree.ElementTree as ET
    root=ET.Element("docenti")
    for docente in sorted(potenziamenti.keys()):
        docente_el=ET.SubElement(root,"docente",{"nome":docente})
        giorni=potenziamenti[docente]
        for giorno_idx in sorted(giorni.keys()):
            giorno_el=ET.SubElement(docente_el,"giorno",{"nome":str(giorno_idx)})
            lezioni=sorted(giorni[giorno_idx],key=lambda x:x["ora"])
            for lez in lezioni:
                lez_el=ET.SubElement(giorno_el,"lezione")
                ora_el=ET.SubElement(lez_el,"ora")
                ora_el.text=str(lez["ora"])
                classe_el=ET.SubElement(lez_el,"classe")
                classe_el.text=lez["classe"]
                aula_el=ET.SubElement(lez_el,"aula")
                aula_el.text=lez["aula"]
    return ET.tostring(root,encoding="utf-8",xml_declaration=True).decode("utf-8")
