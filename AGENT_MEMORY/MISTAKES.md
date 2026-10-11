# MISTAKES.md - Galtiyan jo hui hain + unke fixes

YE DOBARA MAT KARNA. Har entry: kya galti hui, kyun hui, kaise fix hui, aur aage kaise bachna hai.

---

## 1. Bash se PDF download karne ki koshish (WASTED)

Galti: curl/urllib se shiksha ki PDF download karne ki koshish ki.
Kyun galat: sandbox ka internet SIRF github/npm/pypi tak hai. Baaki sab blocked (TLS connection closed / 000).
Fix: fetch_page use karo (uska apna internet hai).
Aage se: kabhi bash se external site se download ki koshish mat karo. Seedha fetch_page.

## 2. fetch_page se badi PDF ke aage wale pages padhne ki koshish (WASTED)

Galti: shiksha ki 48-page booklet PDF ko baar-baar fetch kiya socha shayad aage wale pages mil jayein.
Kyun galat: fetch_page PDFs ko hard 30 pages tak hi parse karta hai - same URL dobara fetch karne se kuch naya nahi milta.
Fix: r.jina.ai trick - "https://r.jina.ai/<PDF_URL>" se POORI PDF parse hoti hai (49 pages, 84 pages tested).
Aage se: badi PDF = seedha r.jina.ai lagao. Wahi URL dobara mat fetch karo.

## 3. Chat me bheji file ka wait karna (CONFUSION)

Galti: user ne "ctet paper 1 aug 2023.pdf" attach ki thi - wo /home/user/uploads me baar-baar dhoondhta raha.
Kyun galat: chat attachments sandbox me sync nahi hoti.
Fix: user se PDF ka URL maanga (shiksha link mil gaya).
Aage se: attachment ka wait mat karo, turant URL maango ya online source dhoondho.

## 4. Third-party answer key par bharosa (GALAT ANSWERS)

Galti: theexampillar ki EVS key use ki (Q86-88 = 4,1,4). Baad me CBSE Final Key me Q86-88 = 1,4,1 nikla.
Kyun galat: third-party sites ki keys me transcription errors ho sakti hain ya purani (provisional) key hoti hai.
Fix: Answer-Key.txt CBSE Final Key se banaya. Q88 = 1 ("A ग़लत, B सही") - bamboo stilt houses Assam me hote hain, Manali me nahi - bilkul sahi hai official key.
Aage se: answer key HAMESHA CBSE official final key PDF se. Third-party se sirf cross-check.

## 5. Pehle "missing sections" ka galat andaza (WRONG ASSUMPTION)

Galti: pehle laga paper me sirf Hindi-1 + Eng-2 hai (theexampillar par wahi thi). README me "Hindi-2, Eng-1 nahi mile" likh diya.
Kyun galat: ek source dekh ke conclusion nikaal diya. Booklet ki instruction nahi padhi thi.
Fix: user ne full booklet PDF diya - instructions padhi - pata chala booklet me ENGLISH + HINDI dono ke 4 sections hote hain. Dono add kiye.
Aage se: paper ki INSTRUCTION PAGE zaroor padho (kitne parts, languages, supplement booklet). Ek source ke basis par "nahi hai" mat likho.

## 6. Garbled Hindi PDF text ko seedha copy karna (ERROR-PRONE)

Galti: shiksha booklet ki Hindi text layer double-corrupted hai (legacy font + broken Unicode) - "िीिन" = जीवन, "स्ग् ि भाि" = स्वभाव type. Seedha copy = galat paper.
Fix: (a) decode patterns banaye (neeche), (b) parallel English section se cross-check kiya (Q91-105/136-150 translations hain), (c) testbook par unique phrase search se clean text liya, (d) answer key se verify kiya ki reconstruction consistent hai.
Aage se: garbled Hindi kabhi seedha mat likho. Clean HTML source ya testbook dhoondho, warna decode + verify karo.

### Garbled Hindi decode patterns (shiksha PDF ke liye)

- Legacy font words: "narjm"=परीक्षा, "ghr"=सही, "CÎma"=उत्तर, "àíZ"=प्रश्न, "ZX}e"=निर्देश, "~m°Q>_"=बॉटम, "_m°S>b"=मॉडल, "nR>Z"=रीडिंग, "CX²Jm_r"=उद्गामी/उदीयमान, "dmbo"=दिए, "H$m"=का etc.
- ि-matra -> ड preposed: किस->डकस, मित्रों->डमत्रों, लिए->डलए, किया->डकया
- Kuch X+ि -> "डि": विशेषण->डिशेषण, जिस->डिस, धर्म->? (mixed)
- {ज,द,व,ड,ल,ट,फ,ध,क्ष,ठ} -> "ि" (context se samjho): जीवन->िीिन, दुख->िुख, तनाव->तनाि, फल->िल, टीपीआर->िीपीआर, इंफाल->इंिाल
- र्+X -> "Xा": अर्थ->अथा, कार्य->काया, वर्ग->िगा, कोर्स->कोसा, महत्त्वपूर्ण->महत्त्िपूणा
- न्/ं -> "ह": भिन्न->डभहन, अन्य->अहय, परन्तु->परहतु, संन्यास->संहयास, चिन्तन->डचहतन
- व in conjuncts -> "ग्ि": स्वभाव->स्ग्िभाि, स्थानीय->स्ग्थानीय, स्कूल-type -> "स्ग्क"
- र्+य -> "या": शिक्षार्थियों->डशक्षाडथायों, क्षमता-type words
- Spacing/OCR noise bahut hai - words ke beech space galat aati hai ("डचहत न करने" = "चिन्तन करने"!)

## 7. awk/sed me unescaped parentheses (WRONG COUNT)

Galti: awk pattern '^[A-Za-z].*\(Q' me socha "\(" literal paren hai, par section headers "(Language I..." me "(Q" nahi tha - galat counts aaye (0 aur 150).
Fix: grep -cE '^[0-9]+\. ' jaise simple patterns use kiye. Counts manually verify kiye (7 x 30 = 210).
Aange se: verification ke liye SIMPLE patterns rakho. Weird count aaye to haath se 2-3 lines dekho, tool pe blind trust mat karo.

---

## 8. Language sections ko hamesha translation samajhna (WRONG ASSUMPTION)

Galti: Aug 2023 Set A ke pattern se yeh maan lena ki har CTET paper me English aur Hindi ke same-numbered language questions translations hain.
Kyun galat: Jan 2024 Set I booklet me English L1 Q91-105 ka drug-store passage Hindi L1 ke cleanliness passage se alag hai; L2 Q121-135 ke English passages aur Hindi passages bhi alag hain. Official answer-key tables me inke answers bhi alag hain.
Fix: Har language section ko Set I booklet se alag transcribe kiya aur usi language ki CBSE final-key table se answer liya.
Aage se: Booklet me actual alignment verify kiye bina parallel translation ya same-answer assumption mat karo. Har language ka official key independently check karo.

## Naya mistake mila? Yahan add karo (format):

N. Title (SHORT)
Galti: kya hua
Kyun galat: reason
Fix: kaise sudhara
Aage se: kaise bachenge
