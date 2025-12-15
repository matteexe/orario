import pdfplumber
import xml.etree.ElementTree as ET
from collections import defaultdict
import re

GIORNI=["LUN","MAR","MER","GIO","VEN","SAB"]
GIORNI_NUM={"LUN":1,"MAR":2,"MER":3,"GIO":4,"VEN":5,"SAB":6}

RE_PAREN=re.compile(r"^(.*?)\((.*?)\)\s*$")
RE_DOCENTE=re.compile(r"^[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ''\-]+(?:\s+[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ''\-]+)*\s+[A-Z](?:\.[A-Z])*\.$")

def pulisci(t):
    return (t or "").strip()

def normalizza_classe(nome):
    nome=pulisci(nome)
    if " - " in nome:
        nome=nome.split(" - ",1)[0].strip()
    return nome

def split_cognome_nome(nominativo):
    """Divide un nominativo in cognome e nome. Es: 'Rossi M.' -> ('Rossi', 'M.')"""
    nominativo=pulisci(nominativo)
    if not nominativo:
        return "",""
    parti=nominativo.split()
    if len(parti)<2:
        return nominativo,""
    # Cognome: tutte le parti tranne l'ultima
    # Nome: ultima parte (di solito iniziale)
    return " ".join(parti[:-1]),parti[-1]

def docente_valido(s):
    s=pulisci(s)
    return bool(RE_DOCENTE.match(s))

def scegli_docente_sostituto(docente_raw):
    """Gestisce docenti con parentesi per sostituzioni"""
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
    """Separa il docente principale dai docenti in compresenza"""
    base=scegli_docente_sostituto(docente_raw)
    if not base:
        return []
    if " - " in base:
        parti=[p.strip() for p in base.split(" - ") if p.strip()]
        return parti
    return [base]

def pulisci_aula(aula_raw):
    """Pulisce il nome dell'aula rimuovendo Lab. Mobile e parti dopo trattini"""
    if not aula_raw:
        return ""

    aula = pulisci(aula_raw)

    # Rimuove "Lab. Mobile" seguito da numero o spazi
    # Es: "Lab. Mobile 1 - T5" -> "T5"
    if "Lab. Mobile" in aula:
        parts = aula.split(" - ")
        if len(parts) > 1:
            aula = parts[-1].strip()
        else:
            aula = re.sub(r'Lab\.\s*Mobile\s*\d*', '', aula).strip()

    # Rimuove tutto dopo il trattino
    # Es: "S6 - Palestra" -> "S6"
    if " - " in aula:
        aula = aula.split(" - ")[0].strip()

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

                            cogn_doc,nome_doc=split_cognome_nome(docente_principale)
                            aula=pulisci_aula(aula_raw)

                            dati={
                                "classe":classe,
                                "giorno":giorno,
                                "ora":ora,
                                "materia":materia,
                                "cognome_docente":cogn_doc,
                                "nome_docente":nome_doc,
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

                n=ET.SubElement(nodo_lez,"cognome_docente")
                n.text=l["cognome_docente"]

                n=ET.SubElement(nodo_lez,"nome_docente")
                n.text=l["nome_docente"]

                # Aggiungi sempre 4 compresenze (con 0 se non presenti)
                for i in range(1, 5):
                    if i-1 < len(l["compresenze"]):
                        cogn, nome = split_cognome_nome(l["compresenze"][i-1])
                    else:
                        cogn, nome = "0", "0"

                    n=ET.SubElement(nodo_lez,f"cognome_compresenza{i}")
                    n.text=cogn
                    n=ET.SubElement(nodo_lez,f"nome_compresenza{i}")
                    n.text=nome

                n=ET.SubElement(nodo_lez,"aula")
                n.text=l["aula"]

    return ET.tostring(root,encoding="utf-8",xml_declaration=True).decode("utf-8")
