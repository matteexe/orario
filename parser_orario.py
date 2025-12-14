import pdfplumber
import xml.etree.ElementTree as ET
from collections import defaultdict

GIORNI=["LUN","MAR","MER","GIO","VEN","SAB"]
GIORNI_NUM={"LUN":1,"MAR":2,"MER":3,"GIO":4,"VEN":5,"SAB":6}

def pulisci(t):
    return (t or "").strip()

def separa_compresenza(raw):
    if "-" in raw:
        parti=[p.strip() for p in raw.split("-") if p.strip()]
        if len(parti)>=2:
            return parti[0],parti[1]
    return raw,None

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
                        nome=pulisci(c)
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
                            aula=" ".join(linee[2:]) if len(linee)>=3 else ""

                            docente,doc_comp=separa_compresenza(docente_raw)

                            if len(linee)==1:
                                parziali[(classe,giorno,ora)]=linee
                                continue
                            else:
                                parziali.pop((classe,giorno,ora),None)

                            dati={
                                "classe":classe,
                                "giorno":giorno,
                                "ora":ora,
                                "materia":materia,
                                "docente":docente,
                                "compresenza1":doc_comp if doc_comp else "no",
                                "aula":aula
                            }
                            lezioni.append(dati)

                            if ora>1 and chiave_prec in parziali:
                                dup={
                                    "classe":classe,
                                    "giorno":giorno,
                                    "ora":ora-1,
                                    "materia":materia,
                                    "docente":docente,
                                    "compresenza1":doc_comp if doc_comp else "no",
                                    "aula":aula
                                }
                                lezioni.append(dup)
                                parziali.pop(chiave_prec,None)

    return lezioni

def genera_xml(lezioni):
    root=ET.Element("classi")
    raggr=defaultdict(lambda:defaultdict(list))

    for l in lezioni:
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

                n=ET.SubElement(nodo_lez,"compresenza1")
                n.text=l["compresenza1"]

                n=ET.SubElement(nodo_lez,"aula")
                n.text=l["aula"]

    return ET.tostring(root,encoding="utf-8",xml_declaration=True).decode("utf-8")
