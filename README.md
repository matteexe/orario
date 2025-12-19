# Orario PDf a XML

Un'applicazione web Flask per convertire orari scolastici in formato PDF in file XML strutturati.

## 📋 Descrizione

Orario è un tool che permette di caricare un file PDF contenente l'orario delle lezioni scolastiche e convertirlo automaticamente in un file XML ben strutturato. L'applicazione estrae informazioni come classi, giorni, ore, materie, docenti, compresenze e aule.

**Nota:** L'HTML e una piccola parte del parser sono stati realizzati con l'aiuto dell'intelligenza artificiale. 

## ✨ Funzionalità

- 📤 Upload di file PDF contenenti orari scolastici
- 🔍 Parsing automatico delle tabelle degli orari
- 📊 Estrazione di informazioni strutturate (classi, giorni, ore, materie, docenti, aule)
- 🤝 Gestione delle compresenze tra docenti
- 📥 Download del file XML generato
- 🌐 Interfaccia web semplice e intuitiva

## 🚀 Installazione

1. Clona la repository:
```bash
git clone https://github.com/matteexe/orario.git
cd orario
```

2. Installa le dipendenze: 
```bash
pip install -r requirements.txt
```

## 💻 Utilizzo

1. Avvia l'applicazione:
```bash
python main.py
```

2. Apri il browser e vai su `http://localhost:8000`

3. Carica un file PDF contenente l'orario scolastico

4. Scarica il file XML generato

## 🛠️ Tecnologie Utilizzate

- **Flask**: Framework web per Python
- **pdfplumber**:  Libreria per l'estrazione di dati da PDF
- **XML ElementTree**: Generazione di file XML strutturati

## 📁 Struttura del Progetto

```
orario/
├── main. py              # Applicazione Flask principale
├── parser_orario. py     # Logica di parsing del PDF
├── requirements.txt     # Dipendenze Python
├── templates/          # Template HTML
└── static/             # File statici (CSS, JS, immagini)
```

## 📝 Formato XML Output

Il file XML generato ha la seguente struttura:

```xml
<classi>
  <classe nome="1A">
    <giorno nome="1">
      <lezione>
        <ora>1</ora>
        <materia>Matematica</materia>
        <docente>Rossi</docente>
        <compresenza1>no</compresenza1>
        <aula>Aula 101</aula>
      </lezione>
    </giorno>
  </classe>
</classi>
```

## 🌐 Deployment

L'applicazione è configurata per il deployment su piattaforme cloud.  La porta può essere configurata tramite la variabile d'ambiente `PORT`.

## 📌 Versione

Versione corrente: **v0.2.0**

## 👤 Autore

**matteexe**

## 📄 Licenza

Questo progetto è disponibile su [GitHub](https://github.com/matteexe/orario).
