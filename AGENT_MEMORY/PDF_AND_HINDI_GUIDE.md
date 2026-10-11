# PDF_AND_HINDI_GUIDE.md - PDF se text + Hindi decode ka FASTEST tareeka

Ye file Session 1 ki sabse badi learning hai - isse next paper AADHE se bhi kam time me banega.
Padho, follow koro, aur nayi cheez mile to add karo.

---

## 1. PDF se text nikalne ka DECISION TREE (fastest se fastest)

### Step 1 (0 min) - Pehle socho: PDF ki zarurat hi hai?

HTML source (theexampillar/testbook jaisa) available hai? -> USI se karo. PDF ko chhodo.
HTML = saaf text, no garbled fonts, no parse limits. Hamesha first choice.

### Step 2 - Badi PDF (30+ pages) hai?

SEEDHA r.jina.ai lagao - normal fetch_page MAT karo (wahi 30-page limit aayegi):

  https://r.jina.ai/<PDF_KA_POORA_URL>

- Ye POORI PDF parse kar deta hai (49 pages, 84 pages tested - sab chala).
- Chunks me milta hai (15-22) - fetch_page me chunkIndex 0,1,2... se padho.
- Chunks kabhi beech sentence me kat-te hain - ek ka end "...समृद्ध हो" aur agle ka shuru "ती है, ..." - chunks ko jodte waqt ye dhyan rakho. Chunk map (kaunse chunk me kya hai) MEMORY.md me note kar lo - dobara fetch nahi karna padega.

### Step 3 - Sirf chhoti PDF hai (30 pages se kam)?

To normal fetch_page se bhi ho jayega. Phir bhi r.jina.ai safe hai.

### Step 4 - PDF scanned hai (text layer nahi)?

fetch_page/r.jina.ai dono fail/faltu text denge. Tab:
- User se HTML source ya image screenshots maango (images read_file se padhi jaati hain).
- Ya PDF ko git repo me push karwao (user ke paas hai to) - phir local tools (neeche) use karo.

---

## 2. Advanced Tools (jo shayad tumhe nahi pate)

### r.jina.ai ke saath jaane wale pro tricks

- r.jina.ai Reader API headers support karta hai (API key ke saath): X-Return-Format: text/markdown, X-Target-Selector, X-With-Links-Summary. Hum fetch_page se plain URL use karte hain - wo bhi kaafi hai.
- Google Drive links bhi chalte hain: https://drive.google.com/uc?export=download&id=FILE_ID - fetch_page ya r.jina.ai dono se.
- Dead links ke liye: https://web.archive.org/web/2023/<URL> - wayback machine se purana version mil jata hai.

### Local PDF tools (jab PDF workspace me ho - git se ya download)

bash ka internet sirf github/npm/pypi tak hai - PDF khud download NAHI hogi.
Par agar PDF repo me commit ho ya github par ho to ye tools BEST hain (pip install kaam karta hai):

- pdftotext (poppler) - sabse fast plain text
- PyMuPDF (pip install pymupdf) - fastest Python extractor; page-wise/block-wise text; layout control
- pdfplumber (pip install pdfplumber) - TABLES ke liye best (answer key ki tables isi se nikal sakti hain!)
- tabula-py - tables ke liye alternative
- OCR jab text layer NAHI ho: tesseract (hin+eng languages) ya OCRmyPDF (pip install ocrmypdf) - scanned booklets ke liye
- Legacy Hindi fonts (Chanakya/Kruti Dev) ke liye online converters hain par offline decode table (neeche) zyada reliable hai.

### Sabse advanced reality-check

In sab se FASTEST hai: CLEAN HTML SOURCE DHOONDHNA. 
Ek web_search (unique phrase se) = 10 second me testbook/exampillar ka clean page.
PDF decode me ghanta lagta hai. Search pehle, decode last resort.

---

## 3. HINDI FONT CORRUPTION - decode ka FAST workflow

### Pehle samjho - 2 tarah ki corruption hoti hai (shiksha/CTET booklets me)

Layer 1 - Legacy font (Chanakya/Kruti Dev) strings seedha aa jate hain:
  "narjm"=परीक्षा, "ghr"=सही, "CÎma"=उत्तर, "àíZ"=प्रश्न, "ZX}e"=निर्देश,
  "~m°Q>_"=बॉटम, "_m°S>b"=मॉडल, "nR>Z"=रीडिंग, "CX²Jm_r"=उद्गामी, "dmbo"=दिए

Layer 2 - Unicode text bhi garbled (font ki ToUnicode map tooti hai):
  "िीिन"=जीवन, "स्ग् ि भाि"=स्वभाव, "डकस"=किस

### FAST WORKFLOW (order me - time bachega)

1. CLEAN SOURCE DHOONDHO (1-2 min): garbled text ka koi unique phrase web_search me daalo
   (jaise "संगाई महोत्सव" ya "जीवन में" "अभाव का दुख"). testbook.com/question-answer par
   exact question+passage clean mil jata hai. MIL GAYA? -> DECODE KI ZARURAT NAHI.

2. PARALLEL ENGLISH (2 min): English ko Hindi decode ka cross-check tabhi banao jab booklet me
   question alignment visibly same ho. Har paper me language sections translation nahi hote.
   Jan 2024 Set I me L1 Q91-105 (English drug-store passage vs Hindi cleanliness passage) aur
   L2 Q121-135 (English passages vs Hindi El Nino / moral passage) alag hain; unke answers bhi
   alag key tables se lene hain. Is paper me pedagogy ranges Q106-120 aur Q136-150 align hoti hain.
   Pehle booklet verify karo, phir hi parallel English use karo.

3. ABHI BHI garbled hai to DECODE TABLE use karo (neeche) + grammar clean-up (section 4).

4. VERIFY (2 min): ANSWER KEY se check karo - tumhare options ka ek answer key se match karna
   chahiye aur passage se sense banani chahiye. Reconstruction sahi hai iski guarantee ye hi hai.
   (Session 1 me: Hindi-2 Q121-135 ke saare answers reconstruction se align hue - 100% confirmed.)

### DECODE TABLE (shiksha/CTET booklet Hindi ke liye - Session 1 se)

| Garbled pattern | Asli cheez | Example |
| --- | --- | --- |
| X+ि -> "ड"+X (ि preposed) | i-matra restore | डकस=किस, डमत्रों=मित्रों, डलए=लिए |
| X+ि -> "डि" (kuch words) | special ligatures | डिशेषण=विशेषण, डिस=जिस, आडिष्कृत=आविष्कृत |
| ज/द/व/ड/ल/ट/फ/ध/क्ष/ठ -> "ि" | consonant loss | िीिन=जीवन, िुख=दुख, तनाि=तनाव, फल=िल |
| र्+X -> "Xा" | r-halant merge | अथा=अर्थ, काया=कार्य, िगा=वर्ग, कोसा=कोर्स |
| न्/ं -> "ह" | nasal corruption | डभहन=भिन्न, अहय=अन्य, परहतु=परन्तु |
| व in conjunct -> "ग्ि" | v-conjunct | स्ग्िभाि=स्वभाव, स्ग्थानीय=स्थानीय |
| स्क -> "स्ग्क", स्त -> "स्ग्त" | conjunct artifacts | ियस्ग्कों=वयस्कों, पुस्ग्तक=पुस्तक |
| Spaces random | ignore/jodo | "डचहत न करने" = "चिन्तन करने" |

Yaad rakho: ye mapping MANY-TO-ONE hai (lossy) - perfect reverse impossible hai.
Isliye decode hamesha: patterns + meaning + parallel English + answer key - TEENO se confirm karo.

---

## 4. HINDI GRAMMAR CLEAN-UP (jab likh rahe ho)

Galat mat likhna - ye standard forms hain (Session 1 me fix ki thi):

- परन्तु (not "परहतु"/"परंतु" - file style: परन्तु), तर्क (R) (not "कारण"? - dono chalte hain par file style: तर्क)
- केन्द्रित, चिन्तन, ध्वन्यात्मक, अभिन्न - न् forms use karo (file style consistent hai)
- उद्गामी (emergent), अधोमुखी (bottom-up), शीर्ष अधोमुखी (top-down) - CTET standard terms
- समग्र भौतिक प्रतिक्रिया (TPR), संभाषिक पठन (dialogic reading), मॉडल पठन (model reading), साझा पठन (shared reading), सस्वर पठन (aloud reading)
- निपुणता (proficiency), अर्जन (acquisition), अधिगम (language acquisition = भाषा अधिगम)
- मात्राएँ restore karo: "हआए"->हुए, "बडल्कि"->बल्कि, "िागृ त"->जागृत
- Quotes: straight quotes ' use karo (files me unicode quotes nahi), blanks ________ se
- Hindi numbers/words ke beech ek normal space - PDF wali random spaces hata do

---

## 5. TIME TARGETS (kam time, zyada kaam, perfect)

Session 1 (Set A) = exploration zyada tha (tools dhoondhe, limit face ki, decode seekha).
Ab recipe ready hai - targets:

- HTML source available paper: 30-45 min (extract -> format -> key -> checklist -> commit)
- PDF-only paper (r.jina.ai + decode): 45-75 min
- Mixed (jaisa Set A tha): 60 min max
- Ek baar me poora paper set (2-3 sections parallel extract) - separately mat karna

Speed ke liye:
1. Extract chunks PARALLEL fetch karo (ek response me 2-3 fetch_page calls).
2. File likhte waqt hi format final rakho - baad me fix na karna pade.
3. Answer key SAME PDF se (CBSE key me sab sets/languages hote hain) - alag dhoondhna mat.
4. Checklist ek hi baar chalao - PASS -> commit. Faltu me dobara verify mat karo.
5. MEMORY.md me chunk map + notes turant likho - agla session time bachayega.

---

## 6. DUAL-LANGUAGE RULE (USER KA REQUIREMENT - bhoolna mat!)

CTET booklet me CDP, Maths, EVS ke questions BILINGUAL hote hain (Hindi + English dono,
har question ke neeche/pehle dono versions). Language sections (Hindi-1/Eng-1/Hindi-2/Eng-2)
apni-apni bhasha me hote hain (monolingual).

AGLI BAAR se CDP.txt, Maths.txt, EVS.txt DUAL-LANGUAGE banane hain - jaisa paper me chhapa hai:
  Hindi version + English version dono, question ke andar.
Hindi-1/Eng-1/Hindi-2/Eng-2 waise hi rahenge (single language each).
(Set A ke current CPD/Maths/EVS Hindi-only hain - user ne kaha "agli baar" - agar user kahe
to unhe bilingual convert kar sakte hain, English text booklet PDF me already available hai.)
