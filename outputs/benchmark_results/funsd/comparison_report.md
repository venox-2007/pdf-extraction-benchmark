# FUNSD Reading-Order Validation Report

## What was checked

- OCR text is compared exactly as the benchmark concatenates it: PaddleOCR line order, joined with spaces after whitespace normalization.
- FUNSD ground truth is compared exactly as the benchmark concatenates it: `form` entries in JSON order, using `text` or fallback `words[*].text`.
- The sample below checks whether token overlap stays high even when CER/WER are high, which is a sign of reading-order or layout mismatch rather than pure OCR failure.

## Sample summary

- Documents sampled: 10
- Random seed: 42
- Average CER: 0.445558
- Average WER: 0.655377
- Average token precision: 0.691063
- Average token recall: 0.524882
- Average token F1: 0.592571
- Average order-insensitive token overlap accuracy (multiset Jaccard): 0.435208

## Category counts
- actual_ocr_errors: 6
- mixed: 4

## Per-document comparison

### 87147607

- Category: mixed
- CER: 0.342187
- WER: 0.465686
- Token precision: 0.856383
- Token recall: 0.789216
- Token F1: 0.821429
- Order-insensitive token overlap accuracy: 0.696970
- Reading-order gap: 0.162656
- GT tokens: 204
- Pred tokens: 188

**Ground truth**

```text
VENDOR TERMS CODE DESCRIPTION QUANTITY DEPARTMENT USE ONLY NC DATE Prev. UNIT PRICE 4111 8700 87147607 FOR PURCHASING ☐
PURCHASING ☐ STATIONARY PURCHASE REQUISITION PLEASE INCLUDE ONLY ONE TYPE OF MATERIAL ON THIS REQUISITION P. O. 1534
LT-1979 April 19, 1988 Piedmont Research Laboratory 2748 Patterson Ave., Greensboro, ORDER NO or Recommended Supplier
Lorillard Research Center N. A. Thaggard As required DATE WANTED SHIP TO (DEPT BRANCH) 27407 NET 15 F. O. B. N/A VIA N/A
420 English St., Greensboro, NC 27405 This is your authorization to prepare cigarette smoke condensate according to the
protocol "Standard Operating Procedure før the Preparation of Smoke Condensate for Mouse Skin Bioassay," for the period
April 1, 1988 through December 31, 1988. Condensate will be prepared acording to a time schedule provided by Lorillard.
The fixed price for condensate collection will be at a rate of $1, 750/10, 000 cigarettes smoked. Piedmont will pay the
cost of consumable supplies. This work is to be conducted in accordance with the December 10, 1984 formal agreement
between Piedmont Reseach Laboratories and Lorillard. All work is to be coordinated with our Mr. Neil Thaggard (919)
373-6628 FOLLOW UP DATE BUDGET NO. REQUISITION NO. ISSUED BY APPROVED BY DEPT. NO. ACCT. NO.
```

**OCR output**

```text
PURCHASING PURCHASE REQUISITION P.O.1534REV.10/79 DATE STATIONARY PLEASE INCLUDE ONLY ONE TYPE OF MATERIAL ON THIS
REQUISITION LT-10-79 April 19, 1988 VENDOR Piedmont Research FOR PURCHASING DEPARTMENT USE ONLY Laboratory 2748
Patterson Ave., Greensboro,NC ORDER NO. 27407 NET 15 N/A N/A Prev. or Recommended Supptier TERMS F.O.B. VIA SHIPTO
(OEPT.BRANCH) Lorillard Research Center N.A. Thaggard DATE WANTEO As required 420 English St., Greensboro,NC 27405
QUANTITY CODE DESCRIPTION UNIT PRICE This is your autho:ization to prepare cigarette smoke conensate according the
protocol "Standard Operating Procedure fpr the Preparation of Smoke Condensate for Mouse Skin Bioassay, for the period
April 1,1988 through December 31 1988. Condensate will be prepared acqording to a time schedule provided by Lorillard.
The fixed price for condensate collection will be at a rate o $1,750/10,0q0 cigarettes smoked. Piedmont will pay the
cpst of consumable supplies. This work is to be conducted in accordance with the Dedember 10, l984 formal agreement
between Piedmont Reseach Laboratories and Lorillard. All work is to be coordinate with our Mr. Neil Thaggard (919)
373-6628. FOLLOW UP DATE REQUISITION NO. ISSUED BY BUDGET NO. ACCT.NO. DEPT.NO. APPROVED BY 4111 8700 Hf.Minemeypr
87147607
```

**Notes:** missing: NC, ☐, ☐, P., O., 1534, LT-1979, Greensboro,; extra: P.O.1534REV.10/79, LT-10-79, Greensboro,NC, Supptier, F.O.B., SHIPTO, (OEPT.BRANCH), N.A.; classified as mixed

### 82253362_3364

- Category: actual_ocr_errors
- CER: 0.574013
- WER: 0.828947
- Token precision: 0.718750
- Token recall: 0.605263
- Token F1: 0.657143
- Order-insensitive token overlap accuracy: 0.489362
- Reading-order gap: 0.318309
- GT tokens: 228
- Pred tokens: 192

**Ground truth**

```text
TO: FROM: SUBJECT: ☑ GEOGRAPHY REGION: FULL X DIVISION: FULL PARTIAL PARTIAL DISTRIBUTION 20 15 29 44 17 34 15 20 22 27
15 37 Chevron Exxon Walgreen's ? ? ? ? ? ? ? 115 38 217 38 27 70 177 82253362 MAVPROGO K. A. Sparrow SUBMISSION DATE MAY
19 ☐ JUN 30 ☐ AUG 11 ☐ SEP 22 J. L. McGinnis MAVERICK SPECIALS MENTHOL - PROGRESS REPORT (ONLY IF PARTIAL REGION
CONTINUE WITH DIVISION (S) SCOPE) DIVISION NAME: DIVISION NAME: DIVISION NAME: DIVISION NAME: DIVISION NAME: DIVISION
NAME: # REPS # REPS # REPS DIRECT ACCOUNTS AND CHAINS HEADQUARTERED WITHIN THE REGION (15+ STORES) STOCKING NO MAVERICK
SPECIALS MENTHOL NAME OF ACCOUNT IND/ LOR VOLUME NO. OF STORES NAME OF ACCOUNT IND/ LOR VOLUME NO. OF STORES Sac N Pac
ACO Texaco Lone Star 75/ 2 95/ 3 76/ 3 26/ 2 42/ 2 106 /4 62/ 2 78/ 4 319/ 16 65/ 3 69/ 3 80/ 4 Shopper Mart Neal One
Stop Mini Mart Albertson's -Houston Valley Shamrock Get Go Speedy Stop Western Beverage Don & Bens DIRECT ACCOUNTS AND
CHAINS HEADQUARTERED OUTSIDE THE REGION (15+ STORES) STOCKING NO MAVERICK SPECIALS MENTHOL NAME OF ACCOUNT IND/ LOR
VOLUME NO. OF STORES NAME OF ACCOUNTS IND/ LOR VOLUME NO. OF STORES Brookshire Bro's Eckerd Drugs S. Texas Philip's 66
Star Enterprise Page 1 of 3 Pages
```

**OCR output**

```text
TO K. A. Sparrow SUBMISSIONDATE FROM: J. L. McGinnis MAY19 AUG11 JUN30 SEP22 SUBJECT: MAVERICK SPECIALS MENTHOL-PROGRESS
REPORT SGEOGRAPHY REGION: FULL_X PARTIAL (ONLY IF PARTIAL REGION CONTINUE WITH DIVISION(S) SCOPE) DIVISION: FULL PARTIAL
DIVISION NAME: DIVISION NAME: #REPS DIVISION NAME: DIVISION NAME: #REPS DIVISION NAME: DIVISION NAME: #REPS DISTRIBUTION
_QIRECT ACCOUNTS AND CHAINS HEADQUARTERED WITHIN THE REGION 15+STORES)STOCKING NO MAVERICK SPECIALS MENTHOL AND/LOR
IND/LOR NO.OF NAME OF ACCOUNT VOLUME STORES NAME OF ACCOUNT VOLUME: STORES Don & Bens 26/2 20 Sac N Pac 75/2 27 Western
Beverage 42/2 15 ACO/Texaco 95/3 15 Speedy Stop 106/4 29 Lone Star 76/3 37 Got-N-GO 62/2 44 Valley Shamrock 78/4 17
Albertson's - Houston 319/16 34 Mini Mart 65/3 15 Neal's One Stop 69/3 20 Shopper Mart 80/4 22 DIRECT ACCOUNTS AND
CHAINS HEADQUARTERED OUTSIDE THE_REGION (15+STORES) STOCKING NO MAVERICK SPECIALS MENTHOL INDLOR NAME OF ACCOUNT NO.OF
INDILOR NO.OR SVOLUME STORES NAME OFACCOUNT VOLOME STORES Chevron ? 115 Brookshire Bro.'s ? 38 Eckerd Drugs - S, Texas ?
217 Exxon ? 38 Phll's 66 ? 27 Star Erterprise ? 70 Walgreen's ? 177 2 8 2 L 3 3 9 2 MAVPROG9.XLS Page1 of 3 Pages
```

**Notes:** missing: TO:, ☑, GEOGRAPHY, X, 82253362, MAVPROGO, SUBMISSION, DATE; extra: TO, SUBMISSIONDATE, MAY19, AUG11, JUN30, SEP22, MENTHOL-PROGRESS, SGEOGRAPHY; classified as actual_ocr_errors

### 82200067_0069

- Category: actual_ocr_errors
- CER: 0.608383
- WER: 0.820359
- Token precision: 0.535354
- Token recall: 0.317365
- Token F1: 0.398496
- Order-insensitive token overlap accuracy: 0.248826
- Reading-order gap: 0.069186
- GT tokens: 167
- Pred tokens: 99

**Ground truth**

```text
TO: FROM: x SUBJECT: DIVISION: DIVISION: DIVISION: DIVISION: REGION: DIVISION: DIVISION: DIVISION: 225 27 15 31 18 19 20
82200067 09/ 17/ 97 10: 55 603 841 1898 LORILLARD PTLD ☑ 001 K. A. Sparrow T. D. Blachly OLD GOLD MENTHOL LIGHTS & ULTRA
LIGHTS 100'S PROGRESS REPORT AUG 4 SEP 15 MAY 12 JUN 23 (ONLY IF PARTIAL REGION CONTINUE WITH DIVISION (S) SCOPE)
Portland # REPS: 6 Boise # REPS: 2. 5 Eugene # REPS: 5 Seattle South # REPS: 7 Seattle North # REPS: 4 Helena # REPS: 4
DIRECT ACCOUNTS AND CHAINS HEADQUARTERED WITHIN THE REGION (15 + STORES) STOCKING NO OLD GOLD MENTHOL LIGHTS OR ULTRA
LIGHTS 100'S NAME OF ACCOUNT VOLUME NO. OF STORES NAME OF ACCOUNT VOLUME NO. OF STORES Texaco Seattle Texaco Portland
Maid -O Clover Dari Mart Zip Trip Maverick Astro Gas 105 / 5 61 / 3 20 / 2 125 / 5 106 / 4 77 / 1 600 / 7 Page 1 of 3
Pages
```

**OCR output**

```text
09/17/97 10:55 5038411898 LORILLARD PTLD 001 TO: K.A.Sparraw FROM: T.D.Blachly MAY12 AUG4 JUN23 SEP15 SUBJECT: QLD
GOLDMENTHOLLGHTS &ULTRA LIGHTS TOOS-PROGRESS REPORT REGION: (ONLY IF PARTIAL REGION CONTINUE WITH DIVISION(S} SCOPE)
DIVISION: DIVISION: Partland RE 6 DIVISION:Seatte South #REPS7 DIVISION: Boise #REPS2.5 DIVISION:Seattle North REPS4
DIVISION: Eugene REPS:5 DIVISION:Helena #REPS4 15 + STORES) STOCKING NO OLD GOLD MENTHOL LIGHTS OR ULTRA LIGHTS 1OO'S
NDIZOR. ADRROR JOLUME BA YOEME Taxaco -Scattle 105/5 225 Texaco -Portland 61/3 27 Maid-O-Clover 20/2 15 Dari-Mart 125/5
31 Zip Trip 106/4 18 Maverick 77/1 19 Astro Gas 600/7 20 32200067 8 R-1OGMUS-15 Page1 of 3 Pages
```

**Notes:** missing: x, 82200067, 09/, 17/, 97, 10:, 55, 603; extra: 09/17/97, 10:55, 5038411898, K.A.Sparraw, T.D.Blachly, MAY12, AUG4, JUN23; classified as actual_ocr_errors

### 83594639

- Category: actual_ocr_errors
- CER: 0.507576
- WER: 0.666667
- Token precision: 0.653846
- Token recall: 0.586207
- Token F1: 0.618182
- Order-insensitive token overlap accuracy: 0.447368
- Reading-order gap: 0.114035
- GT tokens: 87
- Pred tokens: 78

**Ground truth**

```text
Date: To: Company: From: 3 Lorillard 83594639 ☑001 89/ 22/ 97 MON 15: 35 FAX 12124554900 ROPER STARCH WORLDWIDE ROPER
STARCH TURNING DATA INTO INTELLIGENCE WORLDWIDE Fax Fax Fax Fax Fax Fax Fax Fax Fax Ron Milstein (910) 335 7707 Pages
(Including cover page): "JJ" Klein Fax Number: Roper Starch Worldwide nc 205 East 42nd Street New York NY 0017 212 599
0700 212 887 7008 Fax Roper Marketing and Public Option Research Search Advertising and Media Research Frederen
Marketing Services INRA World Headquarters September 22, 1997
```

**OCR output**

```text
09/22/97 MON 15:35 FAX 12124554900 ROPER STARCH WORLDWIDE 001 ROPER STARCH TURNING DATA IMTO INTELLIGENCE WOALDWIDE" Fax
Fax Fax Fax Fax Fax Fax Fax Fax Date: September 22,1997 To: Ron Milsteln From: "JJKlein Company: Lorillard Fax Number:
(910335-7707 Pages (Including cover page): 3 8 3 694639 5 Roper Starch Woridwido Inc. NwYok NY 10017 205 Est42nd Sboet
Roper Marketing and Public Opinion Research Starch Advertising and Media Research 2125590700 Tel Frisdinan Marketing
Services 2128877008 Fax NRA Word Headquarters
```

**Notes:** missing: 83594639, ☑001, 89/, 22/, 97, 15:, 35, INTO; extra: 09/22/97, 15:35, 001, IMTO, WOALDWIDE", 22,1997, Milsteln, "JJKlein; classified as actual_ocr_errors

### 83553333_3334

- Category: actual_ocr_errors
- CER: 0.567831
- WER: 0.818627
- Token precision: 0.504274
- Token recall: 0.289216
- Token F1: 0.367601
- Order-insensitive token overlap accuracy: 0.225191
- Reading-order gap: 0.043818
- GT tokens: 204
- Pred tokens: 117

**Ground truth**

```text
Sender Date To Reference November 12, 1999 6 Message: 8355333 11/ 12/ 99 19: 32 FAA 212 450 4800 DPW 1048 UUZ/ DUS DAVIS
POLK & WARDWELL Fax Transmittal 450 Lexington Avenue New York, NY 10017 212- 450- 4000 Charles Duggan Number of Pages
(this page included) Sender Voice Number If problems receiving this fax, call 212- 450- 4785 212- 450- 4785 Sender Fax
Number 212- 450- 3785 17555 002 Fax Number Company Recipient Phone Number Thomas M. Sobol 617- 439- 3278 Brown Rudnick
Freed & Gesmer 617- 330- 9000 843- 720 9000 Ness, Motley, Loadholt, Richardson & Poole 843- 720- 9290 Joseph F. Rice
Robert V. Costello Jeffrey D. Woolf 617- 722- 0286 415- 956- 1008 Richard M. Heimann Michael P. Thornton 617- 720- 2445
Thomton, Early & Naumes 617- 720- 1333 415- 956- 1000 617- 227- 7500 Schneider, Reilly, Zabin & Costello Lieff, Cabraser
& Heimann Confidentiality Note This only for the person or entity may besi pavilegedal of otherwis protected from
disclosos. Disscnlation, distribution popying of the facile the information herein by anyone other than the poupil,
waployee responsible for delivering the message the prohibited. You thisfacsimile in error please notify as immediately
by telephone and return the facsimile by mail.
```

**OCR output**

```text
AR/ZT/TT 3ZFAAZ1245U48UU UUZ/UUS DAVISPOLK&WARDWELL Fax Transmittal Sender 450 Lexington Avenue Charles Duggan New
YorkNY 10017 Date Nurnber of Pages (this page included) 212-450-4000 November12,1999 6 Sender Voice Number If problems
receiving this fax,call 212-450-4785 212-450-4785 Sender Fax Number Reference 212-450-3785 17555-002 To Fax Number
Company Recipient Phonc Number Thomas M.Sobol 617-439-3278 Brown RudnickFreed617-330-9000 &Gesmer Joseph F.Rice
843-720-9290 Ness,Motley, 843-720-9000 Loadholt, Richardson & Poole Robert V.Costello 617-722-0286 SchneiderReilly
617-227-7500 Jeffrey D.Woolf Zabin & Costello Richard M.Heimann 415-956-1008 Lieff,Cabraser & 415-956-1000 Heimann
Michael P.Thornton 617-720-2445 ThontonEarly & 617-720-1333 Naumes Message: 8 3 5 5 3 3 3 3 Conldeatiality
NoteThisfaczinios ntendod only forthopeson cr eouly walseddrossedapdmsy eoataininfornstiontbatipervieged,condetial
piease motify us immediately by telehone and retu the facsinile by i.
```

**Notes:** missing: November, 12,, 1999, 8355333, 11/, 12/, 99, 19:; extra: AR/ZT/TT, 3ZFAAZ1245U48UU, UUZ/UUS, DAVISPOLK&WARDWELL, YorkNY, Nurnber, 212-450-4000, November12,1999; classified as actual_ocr_errors

### 83443897

- Category: mixed
- CER: 0.306965
- WER: 0.497436
- Token precision: 0.777027
- Token recall: 0.589744
- Token F1: 0.670554
- Order-insensitive token overlap accuracy: 0.504386
- Reading-order gap: 0.001822
- GT tokens: 195
- Pred tokens: 148

**Ground truth**

```text
DATE: COMPANY: PHONE: FROM: PHONE: MESSAGE: YES NO 2 X 83443897 JAN 11 '99 16: 29 FR 8220 TO 3212128557HC02N P. 01
DICKSTEIN SHAPIRO MORING OSHINSKY FAX TRANSMISSION January 11, 1999 L8557 002 Dewey Tedder Lorillard Tobacco Company
336/ 373- 6917 336/ 373- 6750 Andy Zausner and Rob Mangas 202/ 828- 2259 and 202/ 828 2241 CLIENT NO.: MESSAGE TO: FAX
NUMBER: PAGES (including Cover Sheet): HARD COPY TO FOLLOW JAN 1 2 1999 The following is for your review If your receipt
of this transmission is in error, please notify this firm immediately by collect call to our Facsimile Department at
202- 861- 9106, and send the original transmission to us by return mail at the address below. This transmission is
intended for the sole use of the individual and entity to whom it is addressed, and may contain information that is
privileged, confidential and exempt from disclosure under applicable law. You are hereby notified that any
dissemination, distribution or duplication of this transmission by someone other than the intended addressee or its
designated agent is strictly prohibited. 2101 L Street NW Washington, DC 20037- 1526 Tel 202- 785 9700 Fax 202- 887 0689
```

**OCR output**

```text
JAN 119916:29FR8220 TO3212#128557#002#P.01 FAX TRANSMISSION DICKSTEIN SHAPIRO MORIN OSHINSKY DATE: January 111999 CLIENT
NO L8557.002 MESSAGE TO:Dewey Tedder COMPANY: Lorillard Tobacco Company FAX NUMBER: 336/373-6917 PHONE: 336/373-6750
FROM: Andy Zausner and Rob Mangas PHONE: 202/828-2259 and202/828-2241 PAGES including Cover Shoet2HARD COPYTO FOLLOW YES
XNO MESsAGE: The following is for your review. AN121999 If your receipt of this transmission is in error, please notify
this firm immcdiately by collect call to our Facsimile Dcpartment at 202-861-9106,and send thc original transmission to
us by return mail at the address below This transmission is intended for the sole use of the individual and entity to
whom it is addressed, and may contain information zhat is privileged, confidential and excmpt from disclosure undcr
applicablc Iaw.You are hereby notified that any disscmination, distribution or duplication of this transmission by
83443897. somcone other than the intendcd addressce or its designatcd agent is strictly prohibited.
```

**Notes:** missing: MESSAGE:, 2, X, 83443897, 11, '99, 16:, 29; extra: 119916:29FR8220, TO3212#128557#002#P.01, MORIN, 111999, L8557.002, TO:Dewey, 336/373-6917, 336/373-6750; classified as mixed

### 82254765

- Category: actual_ocr_errors
- CER: 0.496855
- WER: 0.801724
- Token precision: 0.558442
- Token recall: 0.370690
- Token F1: 0.445596
- Order-insensitive token overlap accuracy: 0.286667
- Reading-order gap: 0.088391
- GT tokens: 116
- Pred tokens: 77

**Ground truth**

```text
TO: FROM: 1/24/97 2 1 1 1 ITEMS zbulan 82254765 01/17/97 REQFORM 1500 500 K. A. SPARROW DATE TO NYO: S. Reindel Nassau/
107 DIV. NAME/ NO: 1997 SPECIAL EVENT REQUEST FORM NAME OF EVENT: "DATE OF EVENT: 3/18/97 H. Levinson Tradeshow SAMPLE
10'S (400 PACKS PER CASE) SAMPLES/ ITEMS REQUIRED: NEWPORT K. S. NEWPORT 100's NEWPORT LTS K. S. NEWPORT LTS. 100 KENT
III K. S. # CASES KENT GL LTS K. S. GL 100 KENT III 100 TRUE K. S. KENT K. S. KENT 100 QUANTITY REQUIRED BASEBALL CAP
WATER BOTTLES SHIP TO: CUSTOMER SHIPPING NUMBER 198- 1160006 NYO ONLY: DATE FORWARDED TO PROMOTION SERVICES: PLEASE
ALLOW 6 WEEKS FOR PROCESSING OF YOUR REQUEST
```

**OCR output**

```text
TO: K.A.SPARROW DATE TONYO: 1/24/97 FROM: S. Reindel DIV.NAME/NO Nassau /107 1997 SPECIALEVENT REQUESTFORM NAME OFEVENT:
H. Levinson Tradeshow *DATEOFEVENT 3/18/97 SAMPLES/ITEMS REQUIRED: SAMPLE10'S 400 PACKS PERCASE #CASES NEWPORTK.S.
KENTIIIKS. KENT GLLTSKS NEWPORT 100'S KENTI100 KENTGL100 NEWPORT LTS.K.S. TRUEKS. NEWPORTLTS.100 KENTK.S. KENT100 ITEMS
QUANTITYREQUIRED BASEBALL CAP 1500 WATER BOTTLES 500 SHIP TO CUSTOMER SHIPPINGNUMBER 198-1160006 8 2 NYO ONLY: 2 5
DATEFORWARDEDTO PROMOTION SERVICES: 4 476 PLEASE ALLOW 6 WEEKS FOR PROCESSING OF YOUR REQUEST REQFORM 01/17/97
```

**Notes:** missing: 1, 1, 1, zbulan, 82254765, K., A., SPARROW; extra: K.A.SPARROW, TONYO:, DIV.NAME/NO, Nassau, /107, SPECIALEVENT, REQUESTFORM, OFEVENT:; classified as actual_ocr_errors

### 82253245_3247

- Category: mixed
- CER: 0.343535
- WER: 0.538462
- Token precision: 0.753927
- Token recall: 0.615385
- Token F1: 0.677647
- Order-insensitive token overlap accuracy: 0.512456
- Reading-order gap: 0.050917
- GT tokens: 234
- Pred tokens: 191

**Ground truth**

```text
TO: FROM: SUBJECT: X PRE- SELL DISTRIBUTION Sheetz 18 150 183 21 82 106 87 5 23 35 43 Kroger cvs 82253245 K. A. Sparrow
R. E. Lane SUBMISSION DATE JUNE 30 AUG 11 SEP 22 NOV 10 STYLE LOW PRICE PROGRESS REPORT EFFECTIVENESS OF: Transition
Plan (Report on June 30 only) Overall pre- sell efforts were successful Retail accounts that previously stocked Style
Full Price accepted the introduction of the low price BIGIF 2 FOR 1: Proved to be an excellent tool for pulling the
balance of Style Full Price packs through the system. This aided the field greatly during the transition $ 7.00 CARTON
COUPON/ BUYDOWN: Effective in those retail calls that we could not exchange product out of. Those situations were
limited. DIRECT ACCOUNTS AND CHAINS HEADQUARTERED WITHIN THE REGION (15+ STORES) STOCKING NO LOW PRICE STYLE NAME OF
ACCOUNT IND/ LOR VOLUME NO. OF STORES NAME OF ACCOUNT IND/ LOR VOLUME NO. OF STORES M. Maskos & Sons Pollock Candy and
Cigar McKeesport Candy Co. Sicc Serva Thrift/ Eckerd 104/ 22 521/ 42 137/ 20 DIRECT ACCOUNTS AND CHAINS HEADQUARTERED
OUTSIDE THE REGION (15+ STORES) STOCKING NO LOW PRICE STYLE NAME OF ACCOUNT IND/ LOR VOLUME NO OF STORES NAME OF ACCOUNT
IND/ LOR VOLUME NO OF STORES Rich Oil Super America W H Smith 7- 11 318 Zon Dairy Marts Widman Drugs STYLE XLS Page 1 of
3 Pages
```

**OCR output**

```text
K.A.Sparrow SUBMISSION DATE FROM: R. E. Lane JUNE 30 X SEP22 AUG11 NOV10 - SUBJECT. STYLE LOW PRICE - PROGRESS REPORT
EFFECTIVENESS OETransition Plan (Report on June 30 only) PRE-SELL Style Full Price accepted the introduction of the Iow
price. BIGIF/2FOR1 Proved to be an excellent tool for pulling the balance of Style Full Price packs through the system.
This aided the field greatly during the transition. $7.00 CARTON COUPON/BUYDOWN: Effective in those retail calls that we
could not exchange product out of.. Those situations were limited DISTRIBUTION DIRECT ACCOUNTS AND CHAINS HEADQUARTERED
WITHIN THE REGION 15 + STORES) STOCKING NO LOW PRICE STYLE IND/LORNO.OF IND/LOR NOOF NAME OF ACCOUNT VOLUME STORES NAME
OFACCOUNT VOLUME STORES M.Maskos &Sons Pollock Candy and Cigar McKeesport Candy Co. Sico Serve 104/22 18 Sheetz 521/42
150 Thrift/Eckerd 137/20 183 DIRECT ACCOUNTS AND CHAINS HEADQUARTERED OUTSIDE THE REGION 15 +STORESSTOCKING NO LOW PRICE
STYLE IND/LORNOOF IND/LOR NO.OF NAMEOFACCOUNT VOLUME STORES NAMEOFACCOUNT VOLUME STORES Kroger 21 Rich Oil 82 Super
America 106 CVS 87 5 8 WH Smith 7-11 318 Zon 23 Dairy Marts 35 5 Widman Drugs 43 3 2 4 STYLE.XLS Page1 of 3 Pages
```

**Notes:** missing: TO:, SUBJECT:, PRE-, SELL, cvs, 82253245, K., A.; extra: K.A.Sparrow, SEP22, AUG11, NOV10, -, SUBJECT., -, OETransition; classified as mixed

### 86263525

- Category: actual_ocr_errors
- CER: 0.468468
- WER: 0.666667
- Token precision: 0.750000
- Token recall: 0.433333
- Token F1: 0.549296
- Order-insensitive token overlap accuracy: 0.378641
- Reading-order gap: 0.045307
- GT tokens: 90
- Pred tokens: 52

**Ground truth**

```text
DATE DATE DATE DATE DATE DATE 141 N /A N /A 2051119008 RECORDS RETENTION SCHEDULE RECONCILIATION RECORDS MANAGEMENT
DEPARTMENT - M /C DEPARTMENT NAME SCIENCE & TECHNOLOGY COST CENTER NUMBER INDEX BINDERS CONSOLIDATED BY: N /A INDEX
BINDER RE- LABELED BY: Mallery 2 /15 /90 RETENTION & RECOMMENDATION FILE REORGANIZED AND RE- LABELED BY: RECORDS
RETENTION SCHEDULE PLACED IN INDEX BINDER AND IN FILE BY: Wayne Boughan 4 /18 /90 BOXES CREATED FOR HARD COPY PERMANENT
RETENTION RECORDS BY: RECORDS TRANSFER INVENTORY FORMS UPDATED BY: Wayne Baughan 7 /25 /90
```

**OCR output**

```text
RECORDS RETENTION SCHEDULE RECONCILIATION RECORDS MANAGEMENT DEPARTMENT -M/C DEPARTMENT NAME SCIENCE & TECHNOLOGY COST
CENTER NUMBER 141 INDEX BINDERS CONSOLIDATED BY: N/A DATE INDEX BINDER RE-LABELED BY: Ma DATE 2/15/90 N/A DATE Wane
Bauehan DATE 4/18/90 0 0 BOXES CREATED FOR HARD COPY PERMANENT RETENTION RECORDS BY: N/A DATE 2051119008 DATE 7/25/90
```

**Notes:** missing: N, /A, N, /A, -, M, /C, N; extra: -M/C, N/A, RE-LABELED, Ma, 2/15/90, N/A, Wane, Bauehan; classified as actual_ocr_errors

### 82253058_3059

- Category: mixed
- CER: 0.239766
- WER: 0.449198
- Token precision: 0.802632
- Token recall: 0.652406
- Token F1: 0.719764
- Order-insensitive token overlap accuracy: 0.562212
- Reading-order gap: 0.011410
- GT tokens: 187
- Pred tokens: 152

**Ground truth**

```text
82253058 LORILLARD TO: FROM: DATE: AUG SEPT OCT NOV MANUFACTURER BRAND: X 12/ 10/ 36 09: 51 317 8450977 001/ 002
COMPETITIVE PRODUCT INTRODUCTION PROGRESS REPORT MRS. K. A. SPARROW R. J. Reynolds Camel Menthol Full Flavor Box and
Light Box TYPE OF PACKINGS: R. G. Ryan 12/ 10/ 96 REPORTING PERIODS: (Forward by the 10th of the following month.) TEST
MARKET GEOGRAPHY All of Region 7. PRICE POINT: FULL $ 11.89 P/ V $ (Indicate Distributor's Cost Per Carton)
Merchandising the top tray of permanent counter displays and labeling carton fixtures in the Camel section. Also placing
metal signs and temporary counter displays. SALES FORCE INVOLVEMENT: DISTRIBUTORS - ACCEPTANCE/ INTRO TERMS/ INTRO
DEALS: Product is being introduced to all Direct: Accounts in the Region. Acceptance is spotty at this time. DISTRIBUTOR
INVOLVEMENT: Assembly of promotional products and shipment to retail Indianapolis Direct Accounts are reported to be
receiving B1G1F product. CHAINS - ACCEPTANCE/ MERCHANDISING ALLOWANCE Chain acceptance has been very good. INDEPENDENTS
- ACCEPTANCE/ MERCHANDISING ALLOWANCE Acceptance is better at high volume locations than at lower volume retail calls.
CAMEL WK1/ FMT PAGE 1 OF 2
```

**OCR output**

```text
12/10/36 09:51 3178450971 LORILLARD 002/002 COMPETITIVE PRODUCT INTRODUCTION PROGRESSREPORT TO: MRS.K.A.SPARROW
MANUFACTURER:R.J.Reynolds FROM: R.G.Ryan BRAND:Camel Menthol DATE: 12/10/96 TYPE OF PACKINGS:Full Flavor Box and Light
Box REPORTINGPERIODS: AUG SEPT OCT NOV X (Forward by the 10th ot the following month.) TEST MARKET GEOGRAPHY: All of
Region 7. PRICE POINT: FULL$11.89 PN$ (indicate Distributor's Cost Per Carton SALES FORCE INvOLVEMENT: Merchandising the
top tray of permanent counter displays and labeling carton fixtures in the Camel section. Also placing metai signs and
temporary counter displays. DISTRIBUTORS -ACCEPTANCE/INTRO TERMS/INTRO DEALS: Product is being introduced to all Direct
Accounts in the Region. Acceptance is spotty at this time DISTRIBUTOR INVOLVEMENT Assembly of promotional products and
shipment to retail. Indianapolis Direct Accounts are reported to be receiving B1G1F product. CHAINS
-ACCEPTANCE/MERCHANDISING ALLOWANCE Chain acceptance has been very good. INDEPENDENTS -ACCEPTANCE/MERCHANDISING
ALLOWANCE Acceptance is better at high volume locations than at lower volume retail calls. 82253058 CAMEL.WK1/FMT
PAGE1OF2
```

**Notes:** missing: MANUFACTURER, BRAND:, 12/, 10/, 36, 09:, 51, 317; extra: 12/10/36, 09:51, 3178450971, 002/002, PROGRESSREPORT, MRS.K.A.SPARROW, MANUFACTURER:R.J.Reynolds, R.G.Ryan; classified as mixed

## Interpretation

- High token precision/recall with noticeably worse CER/WER points to ordering and layout effects.
- Low token precision/recall points to genuine OCR mistakes or missing text.
- In this sample, many of the errors are caused by field reordering and line-flattening rather than total OCR failure.
