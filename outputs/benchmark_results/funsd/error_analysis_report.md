# FUNSD Error Analysis Report

## Scope
- Dataset size: 50 documents
- Sampled documents: 5 best-performing and 5 worst-performing by CER
- Metrics shown: CER, WER, token precision, token recall, token F1
- The benchmark flattens each document to a single text stream before scoring.

## High-Level Read
- The best documents are still penalized by label/value reordering and field grouping.
- The worst documents are often form/table heavy, so CER/WER are inflated by order sensitivity as much as by OCR mistakes.
- Numeric fields and short labels are the most fragile tokens in this sample.

## Sample-Level Root Causes
- OCR failure: 2 of 10 sampled documents
- Layout mismatch: 3 of 10 sampled documents
- Table/form structure issue: 5 of 10 sampled documents
- Annotation mismatch: 0 of 10 sampled documents

## Estimated Error Split
- Estimated true OCR mistakes: ~40%
- Estimated benchmark-methodology/layout effects: ~60%
- Annotation mismatch: not clearly evidenced in this sample; if present, it looks minor compared with OCR and ordering issues.

## Document Examples
### Best 5
#### 1. 82250337_0338
- CER: 0.175676 | WER: 0.415888 | Precision: 0.786458 | Recall: 0.705607 | F1: 0.743842
- Root cause: Table/form structure issue ? Form-like content is present, but flattening the layout changes the effective reading order.
- Missing words: TO:, FROM:, DATE:, MANUFACTURER:, BRAND:, Oct., Dec., Jan., Nov., X
- Incorrect words: All ? DATE:, Packings ? 2-Dec-97, D. ? All, J. ? Packings, wisconsin ? W,sconsi, FULLS ? FULL, P/ ? PIV$, V ? Indicate, Carton) ? Carton, crew- ? crew-worked
- Extra words: TT., MANUFACTURER:, B&W, FROM:, D.J.Landro, BRAND:, Oct., Nov., X, Dec.
- Numeric errors: Packings ? 2-Dec-97, off ? off/$4.00, ADVERTISING ? 8, O. ? 2, New ? 2

**Ground Truth**
```text
TO: FROM: DATE: MANUFACTURER: BRAND: Oct. Dec. Jan. Nov. X B&W 82250337 COMPETITIVE PRODUCT INTRODUCTION
PROGRESS REPORT Sam Zolot Kool Waterfall All Packings TYPE OF PACKINGS: D. J. Landro 2- Dec- 97 REPORTING
PERIODS: TEST MARKET GEOGRAPHY: Divisions 621 and 627 wisconsin PRICE POINT: FULLS $ P/ V $ (Indicate
Distributor's Cost Per Carton) SALES FORCE INVOLVEMENT: They have crew- worked distribution, and it is
reported that they may crew- work it again Sales force has been busy promoting old style backs to clean up
inventory. All POS is being converted to "B" Kool. DISTRIBUTORS ACCEPTANCE INTRO TERMS INTRO DEALS
INVOLVEMENT: All accounts have the new packaging. It was not a problem obtaining new distribution. All
accounts appear to have 100% distribution of new packings. CHAINS ACCEPTANCE/ MERCHANDISING: This has not been
a problem. New packaging is just following on the old "packaging". INDEPENDENTS ACCEPTANCE/ MERCHANDISING:
Very well received. The packs are peing consolidated and promoted in select retail locations at 40 off $4 00
off cartons. ADVERTISING EFFECTIVENESS OF P. O. S.: The theme "B" Kool has replaced all previous POS. They
have effectively replaced all old POS. New door signage, hour signs, poster mats, and clocks have the new
design. "B" Kool also appears on billboards in llinois. PAGE 1 OF 2
```
**OCR Output**
```text
COMPETITIVE PRODUCT INTRODUCTION PROGRESS REPORT TT. Sam Zolot MANUFACTURER: B&W FROM: D.J.Landro BRAND: Kool
Waterfall DATE: 2-Dec-97 TYPE OF PACKINGS: All Packings REPORTING PERIODS: Oct. Nov. X Dec. Jan. TEST MARKET
GEOGRAPHY: Divisions 621 and 627 W,sconsi PRICE POINT: FULL $ PIV$ Indicate Distributor's Cost Per Carton
SALES FORCE INVOLVEMENT: They have crew-worked distribution, and it is reported that they may crew-work it
again.Sales force has been busy promoting old style packs to clean up inventory. All POS is being converted to
BKool. DISTRIBUTORS -ACCEPTANCEANTRO TERMS/INTRO DEALS/INVOLVEMENT: All accounts have the new packaging. It
was not a problem obtaining new distribution. All accounts appear to have 100% distribution of new packings
CHAINS-ACCEPTANCE/MERCHANDISING: This has not been a problem. New packaging is just following up on the old
"packaging INDEPENDENTS-ACCEPTANCE/MERCHANDISING: Very well received. The old packs are being consolidated and
promoted in select retail locatons at 40 off/$4.00 off cartons. 8 ADVERTISING-EFFECTIVENESS OF P.O.S.: 2 The
theme BKool has replaced all previous POs.They have effectively replaced all old POs.New 2 5 door signage,hour
signs,poster mats,and clocks have the new design. BKool also appears on billboards 3 in Illinois. 3 PAGE 1 OF
2
```

#### 2. 85240939
- CER: 0.198980 | WER: 0.428571 | Precision: 0.758065 | Recall: 0.610390 | F1: 0.676259
- Root cause: OCR failure ? Dominated by spelling/character substitutions and merged tokens.
- Missing words: Lorillard, SHERATON-, CARLTON, TOBACCO, INSTITUTE, FIFTH, ANNUAL, COLLEGE, 1980, GEORGE
- Incorrect words: NAME: ? THETOBACCO, TITLE: ? INSTITUTI, COMPANY: ? SHERATON-CARLTON, ADDRESS: ? FIPTH, PHONE: ? ANNUAL, WASHINGTON, ? FEBRUAR, D. ? WASHINGTON.DC, C. ? COLLEOE, THE ? OF, FEBRUARY ? NAME:
- Extra words: TITLE:, ...
- Numeric errors: 19-21 ? GEORGBR, 666 ? COMPANY:Lorillard, (212) ? PHONE:, 841- ? 212841-8787, 8787 ? CHECKONE:, TIME: ? TIME:2/18/80, 2/18/80 ? 700P.M., TIME: ? TIME:2/21/80, 2/21/80 ? 400P.M, 800/424- ? 800/424-9876

**Ground Truth**
```text
NAME: TITLE: COMPANY: ADDRESS: PHONE: Lorillard SHERATON- CARLTON HOTEL WASHINGTON, D. C. THE TOBACCO
INSTITUTE FIFTH ANNUAL COLLEGE TOBACCO KNOWLEDGE REGISTRATION FORM FEBRUARY 19-21 1980 GEORGE R. TELFORD Brand
Manager 666 Fifth Avenue, New York, NY 10019 (212) 841- 8787 CHECK ONE: Please reserve a room for me at the
Sheraton- Carlton X I will my own housing arrangements. ARRIVAL DATE AND TIME: 2/18/80 7:00 P. M. DEPARTURE
DATE AND TIME: 2/21/80 4:00 P. M. Please attach a brief (50 words or so) autobiographical sketch. Note your
first name or nickname, your current professional re- sponsibilities, employment background and whatever
personal in- formation you feel would be helpful in giving your fellow students an idea of your activities and
interests. The sketches will be assembled and provided at the opening class session. Any questions? Call
Connie Drath or Carol Musgrave at 800/424- 9876. **PLEASE RETURN IN SELF- ADDRESSED ENVELOPE BY FRIDAY,
JANUARY 18, 1980**
```
**OCR Output**
```text
THETOBACCO INSTITUTI SHERATON-CARLTON FIPTH ANNUAL HOTEL FEBRUAR WASHINGTON.DC COLLEOE OF TOBACCO KNOWLEDGE
REGISTRATION FORM NAME: GEORGBR TELFORD TITLE: Brand Manager COMPANY:Lorillard 10019 PHONE: 212841-8787
CHECKONE: Please reserve a room for me at the Sheraton-Carlt XI willmake my own housing arrangements. ARRIVAL
DATE AND TIME:2/18/80 700P.M. DEPARTURE DATE AND TIME:2/21/80 400P.M Please attach a brief (50 words or so)
autobiographical sketch. Note your first,name or nickname, your current professional re
sponsibilities,.employment background and whatever personal.in- formation you feel would be helpful in giving
your fellow students. ... an idea of your activities and interests. The sketches will be assembled and
provided at the opening class session. Any questions? Call Connie Drath or Carol Musgrave at 800/424-9876
PLEASE RETURN IN SELF-ADDRESSED ENVELOPE BY PRIDAYJANUARY 18, 19
```

#### 3. 82251504
- CER: 0.203160 | WER: 0.481982 | Precision: 0.724324 | Recall: 0.603604 | F1: 0.658477
- Root cause: Table/form structure issue ? Form-like content is present, but flattening the layout changes the effective reading order.
- Missing words: 17, cc:, :, From:, Area:, Region:, 5, X, Chains:, Independents:
- Incorrect words: 11: ? 11:03, 03 ? 8138840863, TAMPA ? TAXPA, 0002/ ? 002/003, by/ ? by/to:, to: ? (), R ? R.W.C.10th, W. ? Septernber, C. ? 30), 10th ? CCD.O.S.
- Extra words: July, 31, August, 29, (), To:, R.W.Caldarella, Area:5Region:1Z, Acceptance/Response:, we
- Numeric errors: 11: ? 11:03, 03 ? 8138840863, 0002/ ? 002/003, R ? R.W.C.10th, C. ? 30), 10th ? CCD.O.S., 28 ? From:, 30 ? B.Mills, Acceptance/ ? Ncvember28, Response: ? December30

**Ground Truth**
```text
17 cc: : From: Area: Region: 5 X Chains: Independents: 82251504 11/05/97 11: 03 813 384 0683 LORILLARD TAMPA
GREENSBOR 0002/ 003 Retail Excel Progress Report Submission for: Distribution by/ to: DM to RSM 1st of Month
RSM to R W. C. 10th D. O. S. R. W. Caldarella Kent B. Mills July 31 August 29 September 30 October 31 November
28 December 30 Acceptance/ Response: What is the retailers response to Lorillard's Excel Merchandising plan?
This program has been successful to date with chains where our "Flex Payment". was not place. The chains where
were using the "Flex Payment" system we have not been las successful. The P. O. S. requirements of the P- 1
Plan with Oil Companies is difficult to obtain. Additional P. V. merchandising is being secured quickly,
Additional monies have assisted Region 17 in fighting PM Exclusives and PM/ RJR co-existence situations.
Hardware Evaluation/ Effectiveness: Comment on the assembly of displays and application of shields: The
displays are easily assembled and durable. Some questions have been raised conceming the inability to be flush
with the counter and/ or against the register. As well as the ability to place this or the Back Bar if the
settlement goes through Pemanent Advertising Evaluation/ Effectiveness/ Acceptance: (P- 1/ P- 5 & C 5 Plans
Only: Not available at this time
```
**OCR Output**
```text
11/05/97 11:03 8138840863 LORILLARD TAXPA GREENSBOR 002/003 Retail Excel Progress Report Submission for: July
31 Distribution by/to: () DM to RSM 1st of Month August 29 () To: R.W.Caldarella RSM to R.W.C.10th Septernber
30) CCD.O.S. October 31 X From: Kent B.Mills Ncvember28 December30 Area:5Region:1Z Acceptance/Response: What
is the retailers response to Lorillard's Excel Merchandising plan? Chains:This program has been successfulto
date with chains where our Flex Payment was not in place.The chains where we were using the Flex Payment
system we have not been as successful. The P.Q.S.requirements of the P-1 Plan with Qil Companies is difficult
to obtain Independents: AdditionalP.V.merchandising ls being.secured quickly Additional monies have assisted
Region 17 in fighting PM Exclusives and PM/RJR co-existence situations. Hardware Evaluation/Effectiveness:
Comment on the assembly of displays and application of shields: The displays are easily assembled and durable.
Some questions have been raised concening the inabiity to be fush with the.counter and/or uo against the
register. As.wellas the ability to place this on the Back Bar if the settlement goes through. Permanent
Advertising Evaluation/Fffectiveness/Acceptance:P-1/P-5 & C-5 Plans Only: Not available at this time 8 2251 5
```

#### 4. 86236474_6476
- CER: 0.208071 | WER: 0.338983 | Precision: 0.857143 | Recall: 0.711864 | F1: 0.777778
- Root cause: Layout mismatch ? Content mostly matches, but field order and grouping differ substantially.
- Missing words: ☑, Mrs., K., A., Sparrow, R., G., Ryan, SUBMISSION, DATE:
- Incorrect words: 8623474 ? R.G.Ryan, ACCOUNT/ ? ACCOUNT/WHOLESALERS:, DIRECT ? DIRECTACCOUNT, ACCOUNT ? CHAINS, NON- ? NON-DIRECT, CHAINS: ? CHAINS, purchase. ? purchase, (1 ? 1.00OFF, Reps. ? Reps, PACK- ? PACK~
- Extra words: Mrs.K.A.Sparrow, SUBMISSION, DATE:, X, 86236474, 8
- Numeric errors: 8623474 ? R.G.Ryan, (1 ? 1.00OFF

**Ground Truth**
```text
TO: FROM: 8623474 ☑ Mrs. K. A. Sparrow R. G. Ryan JUNE7 AUG.2 OCT.7 SUBMISSION DATE: NEWPORT LIGHTS HEAVY UP
PROGRESS REPORT EFFECTIVENESS OF DISTRIBUTION ALLOWANCE: DIRECT ACCOUNT/ WHOLESALERS: Distribution allowance
was very effective in accomplishing our objectives. All accounts have purchased introductory products. DIRECT
ACCOUNT CHAINS: Eagle Foods is the only Void. NON- DIRECT ACCOUNT CHAINS: Reception from these accounts is
most positive with a solid incentitive to purchase. EFFECTIVENESS OF THE RETAIL (1 00 OFF CARTON) DISTRIBUTION
ALLOWANCE: Has been most helpful in acquiring desireable distribution when needed by Sales Reps. PROMOTIONAL
ACTIVITY 40c OFF PACK- GENERAL MARKET: The 40c off promotions continue to be well received at the retail
stores and by consumers, as well.
```
**OCR Output**
```text
TO: Mrs.K.A.Sparrow SUBMISSION DATE: FROM: R.G.Ryan JUNE7 X AUG.2 OCT.7 NEWPORT LIGHTS HEAVY UP PROGRESS
REPORT EFFECTIVENESS OF DISTRIBUTION ALLOWANCE: DIRECT ACCOUNT/WHOLESALERS: have purchased introductory
products. DIRECTACCOUNT CHAINS Eagle Foods is the only Void. NON-DIRECT ACCOUNT CHAINS Reception from these
accounts is most positive with a solid incentitive to purchase EFFECTIVENESS OF THE RETAIL 1.00OFF CARTON)
DISTRIBUTION ALLOWANCE: Has been most helpful in acquiring desireable distribution when needed by Sales Reps
PROMOTIONAL ACTIVITY 86236474 8 40c OFF PACK~ GENERAL MARKET: The 40c off promotions continue to be well
received at the retail stores and by consumers, as well.
```

#### 5. 87125460
- CER: 0.228311 | WER: 0.402778 | Precision: 0.786885 | Recall: 0.666667 | F1: 0.721805
- Root cause: OCR failure ? Dominated by spelling/character substitutions and merged tokens.
- Missing words: APPROVALS, DATE, STUDY, DIRECTOR, FINAL, I-, 7016., 401, 27,, 1986
- Incorrect words: 87125460 ? PINAL, STUDY ? STUDy, Hepatic ? lepatic, Enzymes ? Enzynes, rats ? Rats, (B202) ? B202, NUMBER ? NUMBERI-7016.401, DATE ? DATEOctober, October ? 27,1986, 26, ? 261987
- Extra words: DATE
- Numeric errors: 87125460 ? PINAL, (B202) ? B202, NUMBER ? NUMBERI-7016.401, October ? 27,1986, 26, ? 261987, 8/ ? APPROVALS, 7/ ? 87125460, 87 ? 8/7/87, 08/ ? DATE, 14/ ? QIRECTOR

**Ground Truth**
```text
87125460 APPROVALS DATE DATE STUDY DIRECTOR FINAL REPORT AMENDMENT STUDY NAME Induction of Hepatic Enzymes in
rats (B202) STUDY NUMBER I- 7016. 401 INITIATION DATE October 27, 1986 DATE OF FINAL REPORT February 26, 1987
PART OF FINAL REPORT TO BE AMENDED (EXACT LOCATION) Page 14 and Table 4 REASON FOR THE AMENDMENT Request from
sponsor AMENDMENT (Attach additional sheets as necessary) see attached 8/ 7/ 87 08/ 14/ 87 QUALITY ASSURANCE
```
**OCR Output**
```text
PINAL REPORT AMENDMENT STUDy NAME Induction of lepatic Enzynes in Rats B202 STUDY NUMBERI-7016.401 INITIATION
DATEOctober 27,1986 DATE OF FINAL REPORT February 261987 PART OF FINAL REPORT TO BE AMENDED (EXACT LOCATION)
Page 14 and Table 4 REASON FOR THE AMENDMENT Request from sponsor AMENDMENT (Attach additional sheets as
necessary) see attached APPROVALS 87125460 8/7/87 DATE QIRECTOR t8|h/g0 DATE QUALITY ASSURANCE
```

### Worst 5
#### 1. 82504862
- CER: 0.786036 | WER: 0.936508 | Precision: 0.660714 | Recall: 0.587302 | F1: 0.621849
- Root cause: Layout mismatch ? Content mostly matches, but field order and grouping differ substantially.
- Missing words: COURT:, Asbestos, JUDGE:, LORILLARD, ENTITIES, DATE, FILED, SERVED, CASE, TYPE:
- Incorrect words: J. ? J.Sellers, Raybestos ? Raybestos-Manhattan,
- Extra words: COURT:, San, Francisco, Superior, Court-No.996382, LORILLARD, ENTITIES:, Lorillard, Tobacco, Company
- Numeric errors: None obvious

**Ground Truth**
```text
COURT: Asbestos JUDGE: CASE FORM CASE NAME: LORILLARD ENTITIES DATE FILED DATE SERVED CASE TYPE: PLAINTIEE'S
COUNSEL: LORILLARD COUNSEL: TRIAL DATE: 82504862 946225115 Wartnick Chaber, Harowitz, Smith& Tigerman
StephenM. Tigerman 101 California Street Suite 2200 San Francisco California 94111 August 3, 1998 Lorillard
Tobacco Company San Francisco Superior Court- No. 996382 Donald D. Sellers and Robin J. Sellers v. Raybestos
Manhattan et al.
```
**OCR Output**
```text
CASE FORM CASE NAME: Donald D. Sellers and Robin J.Sellers v. Raybestos-Manhattan, et al. COURT: San Francisco
Superior Court-No.996382 LORILLARD ENTITIES: Lorillard Tobacco Company DATE FILED: DATE SERVED: August 3,1998
CASE TYPE: Asbestos PLAINTIFF'S COUNSEL: Wartnick,Chaber, Harowitz,Smith& Tigerman StephenM.Tigerman 101
California Street, Suite 2200 San Francisco,California 94111 415/986-5566 LORILLARD COUNSEL: JUDGE: TRIALDATE:
94625115 2504862 8 2
```

#### 2. 82491256
- CER: 0.775681 | WER: 0.943662 | Precision: 0.719298 | Recall: 0.577465 | F1: 0.640625
- Root cause: Layout mismatch ? Content mostly matches, but field order and grouping differ substantially.
- Missing words: COURT:, JUDGE:, Asbestos, LORILLARD, COUNSEL:, TRIAL, DATE:, &, 101, California
- Incorrect words: CASE ? CASENAME, NAME: ? Wanda, PLAINTIFF ? Asbestos, Smith ? Smith&, J. ? J.Chaber, Chaber ? 101California, Francisco, ? Francisco,California, 415 ? 415/986-5566, 986- ? LORILLARD, 5566 ? COUNSEL:
- Extra words: G.Robinson, and, Carroll, Robinson, v.Raybestos-Manhattan,et, al., COURT:, San, Francisco, Superior
- Numeric errors: Chaber ? 101California, 415 ? 415/986-5566, 986- ? LORILLARD, 5566 ? COUNSEL:, 3, ? TRIAL, 1998 ? DATE:, July ? 824912

**Ground Truth**
```text
COURT: JUDGE: Asbestos CASE FORM CASE NAME: LORILLARD ENTITIES: DATE FILED: DATE SERVED: CASE TYPE: PLAINTIFF
COUNSEL: LORILLARD COUNSEL: TRIAL DATE: Wartnick, Chaber, Harowitz, Smith & Tigerman Madelyn J. Chaber 101
California Street, Suite 2200 San Francisco, California 94111 415 986- 5566 August 3, 1998 July 23, 1998
Lorillard Tobacco Company San Francisco Superior Court - No. 996378 Wanda G. Robinson and Carroll Robinson v
Raybestos- Manhattan, et al. 82491256 94624999
```
**OCR Output**
```text
CASE FORM CASENAME Wanda G.Robinson and Carroll Robinson v.Raybestos-Manhattan,et al. COURT: San Francisco
Superior Court-No.996378 LORILLARD ENTITIES: Lorillard Tobacco Company DATE FILED: July 23,1998 DATE SERVED:
Angust 3,1998 CASE TYPE: Asbestos PLAINTIFF'S COUNSEL: Wartnick, Chaber, Harowitz, Smith& Tigerman Madelyn
J.Chaber 101California Street, Suite 2200 San Francisco,California 94111 415/986-5566 LORILLARD COUNSEL:
JUDGE: TRIAL DATE: 824912 94624999 5 9
```

#### 3. 87093315_87093318
- CER: 0.756162 | WER: 0.860825 | Precision: 0.825000 | Recall: 0.680412 | F1: 0.745763
- Root cause: Table/form structure issue ? Form-like content is present, but flattening the layout changes the effective reading order.
- Missing words: Cigarettes, Maker, Length, Circumference, Weight, Paper, Kind, Plast., 3/14/90, Attached
- Incorrect words: Date: ? Date:3/14/90, on ? 90-B-1, BLEND ? Sample, CASTING ? No.1194-90, RECASING ? Type, MENIHOL ? of, Filters ? Cigarette, J. ? J.H., B- ? B-451, C. ? C.w.
- Extra words: Batch, Size, on, BLEND, CASING, RECASING, MENTHOL, Attached, None, NUme
- Numeric errors: Date: ? Date:3/14/90, on ? 90-B-1, CASTING ? No.1194-90, B- ? B-451, 78.0 ? OG, 100 ? 78.0g/100, 81- ? Rod, 01- ? Length, 07 ? 108, 25- ? m

**Ground Truth**
```text
Date: on BLEND CASTING RECASING MENIHOL Filters Cigarettes Maker Length Circumference Weight Paper Kind
Circumference Weight Plast. 3/14/90 Attached None Attached None None mm 430 G White Blue White White James
James MFG. Wrapping Responsibility Closures Labels Cartons Markings Shipping Requirements Laboratory Analysis:
87093315 90- B- 1 1194- 90 100 mm Filter 47.5 lbs. Original Request Made By J. H. Bell 2/15/90 Purpose of
Sample Cigarette Modification B- 451 Sample Specifications Written By C. W. Lassiter FINAL FLAVOR MK 8 99.0 mm
27 mm 24.8 mm 78.0 g / 100 81- 01- 07 25- 04- 07 67 mm White Sample No. Type of Cigarette Batch Size Filter
Length Tip. Paper Tip. Paper Por. Glue Roller Air Dilution 13.0 % Section A Section B 27 mm 3.3/ 35,000 OG Lt.
108 mm 400 mm 24.45 mm 75.3 30g / 100 7 % Kent 84- 52- 28 655 Rod Length Pressure Drop Plug Wrap Plug Wrap
Por. Comb. Wrap Comb. Wrap Por. Tobacco Blend Filter Production Making & Packing Sample Requistion (Form 02:
20: 06) Lassiter/ Douglas Tear Tape Sample No. on each Carton Laboratory Other 1 Tray Mainstream Smoke
Analysis Special Requirements Director, Product Development
```
**OCR Output**
```text
Date:3/14/90 90-B-1 Sample No.1194-90 Type of Cigarette 100 mm Filter Batch Size 47.5 lbs. Original Request
Made By J.H. Bell on 2/15/90 Purpose of Sample Cigarette Modification B-451 Sample Specifications Written By
C.w. Lassiter BLEND CASING RECASING FINAL FLAVOR MENTHOL Attached None Attached NUme None Cigarettes Filters
Maker MK 8 Section A Section B Length 99.0 mm 27 mm mm Filter Length 27 mm Kind 3.3/35,000 Circumference 24.8
mm OG Lt. Weight 78.0g/100 Rod Length 108 m Paper 81-01-07 Pressure Drop 400 mm Tip.Paper 25-04-07
Circumference 24.45 m 67 nm White Weight 75.3g/100 Tip. Paper Por. 430 Plast. 78Kent Glue Roller G Plug Wrap
84-52-28 Air Dilution 13.0 Plug Wrap Por. 655 C Comb.Wrap Camb.Wrap Por. Responsibility Labels White Tobacco
Blend Lassiter/Douglas Closures Blue Filter Production MFG. Teaeape White Making & Packing James Cartons White
Shipping Markings Sanple No. on Sample Requistion James each Carton Form022006 Requirements Laboratory
Analysis: Laboratory 1 Tray Mainstream Smoke Analysis Mi Other Special Requirements 87093315
```

#### 4. 86230203_0206
- CER: 0.693548 | WER: 0.912409 | Precision: 0.760000 | Recall: 0.693431 | F1: 0.725191
- Root cause: Table/form structure issue ? Form-like content is present, but flattening the layout changes the effective reading order.
- Missing words: DIVISION:, x, FULL, PARTIAL, DISTRIBUTION, Seyle, Dantzlen, Econ, 180, 130
- Incorrect words: X ? MAVERICK, DIVISION ? #REPS, (15+ ? 15+, STORES) ? STORES, MAVERICK ? MAVEAICK, Aurry ? 36, Bayou ? 3, Foods ? MAVPROG, Compac ? Pago10f4, Foods ? 11-Dec-96
- Extra words: 12/12/96, 08:33, 5047348616, LORILLARD, TOB, +NYO1, 001/004, SUBMISSIONDATE, K.A.Sperrow, DEC13X
- Numeric errors: (15+ ? 15+, Aurry ? 36, Bayou ? 3, Compac ? Pago10f4, Foods ? 11-Dec-96

**Ground Truth**
```text
TO: FROM: SUBJECT: X GEOGRAPHY REGION: DIVISION: FULL PARTIAL x FULL PARTIAL DISTRIBUTION Seyle Dantzlen Econ
180 130 20 19 18 18 17 16 K&B Delchamps Litco 85 39 36 36 23 23 22 86230203 Page 1 of 4 MAVPROG 11-Dec-96
12/12/96 08:33 204 7348616 LORILLARD TOB NYO 1 0001/ 004 K. A. Sparrow F. Strickland MAVERICK SPECIALS-
PROGRESS REPORT SUBMISSION DATE DEC 13 JAN 25 FEB 24 APR 4 (ONLY IF PARTIAL REGION CONTINUE WITH DIVISION(S)
SCOPE) DIVISION NAME: DIVISION NAME: DIVISION NAME: # REPS # REPS # REPS DIVISION: DIVISION NAME: DIVISION
NAME: DIRECT ACCOUNTS AND CHAINS HEADQUARTERED WITHIN THE REGION (15+ STORES) STOCKING NO MAVERICK SPECIALS
NAME OF ACCOUNT NO. OF STORES NAME OF ACCOUNT NO OF STORES Winn Dixie Schwegmann Aurry Greer Double Huber Oil
Morris Corp Bayou Foods Compac Foods Southeast Foods
```
**OCR Output**
```text
12/12/96 08:33 5047348616 LORILLARD TOB +NYO1 001/004 SUBMISSIONDATE TO: K.A.Sperrow DEC13X FE824 FROM:
F.Strickland JAN 25 APR 4 SUBJECT: MAVERICK SPECIALS -PROGRESS REPORT GEOGRAPHY REGION: FULL X PARTIAL (ONLY
IF PARTIAL REGION CONTINUE WITH DIVISION(S) SCOPE) DIVISION: FULL PARTIAL DIVISION NAME: DIVISION NAME: #REPS
DIVISION NAME: DIVISION NAME: #REPS DIVISION NAME: DIVISION NAME: .#REPS DISTRIBUTION DIRECT ACCOUNTS AND
CHAINS HEADQUARTERED WITHIN THE REGION 15+ STORES STOCKING NO MAVEAICK SPECIALS NO.OF NOOF. NAME OF ACCOUNT
STORES NAME OF ACCOUNT STORES 180 Sayle Oil 20 K&B 130 Dantzler 19 Delchamps Winn Dixie 85 Southeast Foods 18
39 Compac Foods 18 Schwegmann 36 Bayou Foods 17 Autry Greer 36 Econ 16 Double Quick 80 Litco 23 2 23 30203
Huber Oil 22 Morris Corp 3 MAVPROG Pago10f4 11-Dec-96
```

#### 5. 86075409_5410
- CER: 0.681440 | WER: 0.808000 | Precision: 0.761364 | Recall: 0.536000 | F1: 0.629108
- Root cause: Table/form structure issue ? Form-like content is present, but flattening the layout changes the effective reading order.
- Missing words: To:, CC:, Circulation(#), 86075409, Tiers, II,, &, IV, Tesh, C.
- Incorrect words: S. ? C.Ni, *Space/ ? +Space/Color, and/ ? and, Title. ? Titie, Requirements ? Requirements:, * ? 86075409
- Extra words: 01, Don, Kisling, Newport, Parent., Lights.&, 120's, Direct, Mail, Competitive
- Numeric errors: * ? 86075409

**Ground Truth**
```text
From: To: CC: Circulation(#) 86075409 Tiers II, & IV Lynnette Stevens Kelli Scruggs Vincent Losito George
Baroody S. Tesh C. Hill Don Kisling Brand(s) Applicable Media Type Media Name Issue Frequency/ Year *Space/
Color Coupon Issue Date Coupon Expiration Date Geographical Area(s) Coupon Value Pack and/ or Carton?
Advertising Creative Title. Signature of Initiator Date Initiated Analytical Requirements Newport Parent,
Lights. & 120's Direct Mail Competitive 21- 34 years 4/ 14/ 00 9 /30 00 APPROX 600. 000 AR. AZ.A K CA CO FL ID
IA. CT, ME, MASS, MN, MT, NE, NV, NM, NY ND, DK, OR, RL, SD, WA, DC, WY $1. 50 OFF PACK 21- Jan 00 FOR CONTROL
USE ONLY Code Assigned Job Number Est. Redemption 05787 13% * Where Applicable
```
**OCR Output**
```text
From: Lynnette Stevens 01 Kelli Scruggs Vincent Losito Don Kisling George Baroody C.Ni Brand(s) Applicable
Newport Parent. Lights.& 120's Media Type Direct Mail Media Name Competitive 21 - 34 years Issue Frequency/
Year +Space/Color Coupon Issue Date 4/14/00 Coupon Expiration Date 9/30/00 Circulation (#) APPROX. 600.000
AR.AZ.AK.CA,CO.FL.ID.IA,CT,ME.MASS.MN,MT,NE. Geographical Area(s) Tiers II & IV
NV.NM.NY,ND.OK.OR.RI.SD.IFF.WA.D.C..WY Coupon Value $1.50OFF Pack and / or Carton? PACK Advertising Creative
Titie Signature of Initiator Date Initiated Analytical Requirements: FOR CONTROL USE ONLY Code Assigned 05787
Job Number Est. Redemption 13% 86075409 Where Applicable
```

## Conclusion
- CER/WER are informative, but on FUNSD they are noticeably sensitive to reading order and field grouping.
- Token precision/recall/F1 better separate content capture from layout sequencing.
- The main inflation sources in this sample are form/table structure and layout mismatch, not only raw OCR mistakes.
