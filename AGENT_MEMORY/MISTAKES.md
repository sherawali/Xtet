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

Galti: theexampillar ki EVS key use ki (Q86-88 = 4,1,4). Baad me CBSE Final Key me Q86-88 = 1,4,1 nikla. January 2021 Set I me Studyfry ke suggested answers bhi official key se EVS Q90, English Language II Q145 aur Hindi Language I Q106 par alag the.
Kyun galat: third-party sites ki keys me transcription errors ho sakti hain ya purani (provisional) key hoti hai.
Fix: Answer-Key.txt CBSE Final Key se banaya. Q88 = 1 ("A ग़लत, B सही") - bamboo stilt houses Assam me hote hain, Manali me nahi - bilkul sahi hai official key. January 2021 Set I discrepancies ko bhi official CBSE table se settle kiya.
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

## 9. Saaf Unicode ko saaf Hindi ya verified transcription samajhna (LANGUAGE QA GAP)

Galti: January 2024 Set I ke Hindi blocks readable Devanagari mein the, par kuch phrasing literal/awkward thi aur kuch grammatical agreement issues bache hue the.
Kyun hua: PDF ka Hindi text layer legacy-font encoded/garbled tha; Unicode scan encoding ke liye tha, Hindi proofreading ya source-fidelity check nahi.
Fix: CPD, Maths, EVS, Hindi-1 aur Hindi-2 ke Hindi blocks ko line-by-line spelling, grammar, punctuation, agreement aur terminology ke liye manually proofread kiya. Clear issues sudhaare; answer choices/key nahi badle. Hindi-1 Q94 ke jaan-boojhkar galat spelling distractors preserve kiye.
Aage se: Transcription, Unicode/script validation, Hindi proofreading aur source-level verification ko alag steps samjho. Clean Hindi scan/source na ho to sirf saaf language corrections karo aur exact booklet wording verified hone ka daava na karo. Answer choices ya official key ko bina evidence mat badlo.

## 10. Third-party text ka option/question ORDER booklet jaisa nahi hota

Galti: Hindi sections (Hindi-1/Hindi-2) ka order/position clean third-party source (adda247 solution PDF) ke hisaab se likh diya tha. Hindi-1 Q97 me options 3 aur 4 ulte the (official key Q97 = 3 = "शुद्ध विचार, अच्छे कर्म", par file me woh option 4 par tha). Us PDF ka question numbering bhi shifted hai (unka Q107 = booklet ka Q106).
Kyun galat: Solution books apne numbering/order me saawaal ghuma dete hain; official key ke digits BOOKLET ke printed option numbers hote hain - agar order galat ho to poora file key se mismatch ho jata hai.
Fix: prepp CDN booklet ka legacy Hindi text padhne layak hai (Chanakya mapping consistent) - order + wording wahin se liya; adda247 sirf spelling cross-check ke liye. Phir har Hindi question ka official digit semantically verify kiya (digit wale option ka matlab question ke hisaab se sahi hona chahiye).
Aage se: Option/question ORDER sirf booklet (ya official paper) se lo; third-party clean text sirf wording polish/cross-check ke liye. Har section me 10-15 questions ka official-digit semantic spot-check zaroor karo.

## 11. Purani base wali branch + papers/memory ko replace karne wala restructure (c983b097 "pickle" task; UNMERGED)

Galti: `arena/c983b097-xtet` branch (base = Initial commit `52c95fc`, main se 4 session peeche) ne repo ko "CTET Paper-I hub" me badal diya - root README replace, `sessions/*/meta.json` + `practice/set-01` JSON + `schema/`/`ingest/` pipeline add, aur `sessions/README.md` me likh diya ki actual papers "copyright" hone ki wajah se yahan copy nahi kiye jayenge. Uska section mapping bhi GALAT tha: "CDP Q1-30, Language I Q31-60, Language II Q61-90, Maths Q91-120, EVS Q121-150" (sahi: CDP 1-30, Maths 31-60, EVS 61-90, Language I 91-120, Language II 121-150).
Kyun galat: (a) Repo ka CORE product = actual papers ka text (year/paper/section `.txt`) + AGENT_MEMORY; usse metadata/JSON hub se badalna = repo ka maqsad hi khatam. (b) Branch purani base par thi - agar merge hoti to main ke saare papers + AGENT_MEMORY "delete" ho jate (diff me 7729 deletions). (c) Galat section mapping future sessions ko bhatka deti.
Fix: Branch unmerged chhodi. Session 5 ka kaam main ke latest (`eb4dcc3`) se nayi branch (`arena/27af2acc-xtet`) par kiya; papers + AGENT_MEMORY intact rakhe.
Aage se: (1) Kaam shuru karne se pehle merge-base check karo (`git merge-base HEAD origin/main`) - purani base ho to pehle rebase/merge. (2) Papers ya AGENT_MEMORY ko DELETE/REPLACE karne wala restructure kabhi mat karo. (3) Schema/pipeline/app banani ho to papers ke UPAR add-on folder me banao (coexist), replacement nahi. (4) Section mapping sirf AGENT_MEMORY/PLAYBOOK se lo - khud se andaaza mat lagao.

## 12. Official key table ki manual transcription me grouping error (PAKDA GAYA, FIX HUA)

Galti: key PDF ke chunk text se MAIN table padhte waqt digits ko galat groups me baant diya - semantic check out-of-place aaya (Q60 aur Q70 confuses: socha Q70 = 2, actual 3; socha Q60 = 3, actual 2).
Kyun galat: table 5-column hai (Q1-25 | Q26-50 | Q51-75 | Q76-90) par row me 3 pairs dikh sakte hain; chunk boundary table ke beech aati hai; aankh se grouping error-prone hai.
Fix: Table dobara fetch karke COLUMN-BY-COLUMN padha, values 10-10 ke groups me likhe, phir semantic spot-check pass hua (twin primes 1-50 = 6 pairs -> option 4; "two acute angles se reflex nahi banta" -> 2; "paani sabko barabar nahi milta" -> 3). Answer-Key.txt python script se generate ki (5 lists -> file) + count assert (30/30/30/60/60 = 210).
Aage se: (1) Table hamesha column-wise padho, group-of-10 me likho. (2) Answer key file haath se na likho - script + asserts. (3) Har section ke minimum 5 digits semantic check karo. (4) Language tables me Q106-120 & Q136-150 English vs Hindi values identical hone chahiye - mismatch = transcription bug (PLAYBOOK section 11).

## 13. Legacy Hindi me matra (ा/े/ो) lost ho sakti hai - grammar + cross-source se validate karo

Galti/Risk: Chanakya-legacy text me kuch matras drop/merge hoti hain - "बनना चाहता है" text me "’ŸŸ øÊ„ÃÊ „Ò" (बनने jaisa) dikhta hai; "रहा" vs "रहे" ambiguous. Blindly decode karo to Hindi galat chhapti hai.
Fix: (a) Grammar/logic se sahi roop chuno (infinitive aksar "-ना"), (b) us paper ka clean third-party text se validate karo - is paper me askfilo ka Hindi-2 passage EXACT match nikla ("इसे इस रूप में भी समझ सकते हैं..."), testbook ka "कीरम काँटे" phrase confirm hua, (c) poem/passage ki opening line search se canonical text ("सीमित पग डग" - Shivmangal Singh Suman ki kavita; Kalahandi = Jagannath Prasad Das, booklet me truncated extract hai - waisa hi rakho).
Aage se: Matra-ambiguous shabdon par teen-way check: grammar -> third-party clean text -> canonical text. Wording "as-printed" rakho (quirks preserve), sirf matra-level ambiguity theek karo; uncertainty README/MEMORY me note karo.

## Naya mistake mila? Yahan add karo (format):

N. Title (SHORT)
Galti: kya hua
Kyun galat: reason
Fix: kaise sudhara
Aage se: kaise bachenge
