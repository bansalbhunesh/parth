# 40 CFR Part 98, Subpart A, Table A-1 — Global Warming Potentials (100-Year)

**Status: PRIMARY SOURCE, verbatim, not team-authored.** Everything below is
the official EPA regulatory table used for the Greenhouse Gas Reporting
Program, retrieved unmodified (markup stripped, table restructured to
markdown) from the eCFR.

- **License basis: U.S. Government edict — not subject to copyright.**
  Same basis as `40_CFR_60_Subpart_IIII.md` in this directory — see that
  file's header for the full citation.
- **Retrieved:** 2026-07-11, via the eCFR Versioner API:
  `curl "https://www.ecfr.gov/api/versioner/v1/full/2026-07-01/title-40.xml?part=98&subpart=A"`
  — extract the `Table A-1 to Subpart A of Part 98` appendix element.
- **Honesty note — this table does NOT match the GWP values already cited
  elsewhere in this repo, and that is disclosed rather than smoothed over.**
  `../PROVENANCE.md` cites AR4 (IPCC Fourth Assessment Report) GWP values
  for HFC-134a (1,430) and HFC-227ea/FM-200 (3,220), sourced from the EPA's
  general GWP reference page. **This table** — the actual current 40 CFR
  Part 98 regulatory table — lists **HFC-134a = 1,300** and **HFC-227ea =
  3,350** (rows below). Both figures are legitimate; they differ because
  GWP-100 values are assessment-report-vintage-dependent (AR4 vs. the
  AR5-aligned values EPA's GHG Reporting Program now uses under 40 CFR Part
  98 — EPA's own general GWP page confirms UNFCCC reporting has moved to
  AR5 values). Neither this repo's existing AR4 citations nor this table are
  wrong; they answer "GWP under which assessment report," a distinction the
  original citations did not make explicit. **This is disclosed as an open
  reconciliation item, not silently resolved** — a future pass should
  decide which vintage the benchmark's "GWP <= 750" design-basis threshold
  is meant to be checked against, and say so explicitly in the design-basis
  documents themselves.
- R-410A (used in `../submittal_stulz_cyberair.md`, Pair 2) is a zeotropic
  blend of HFC-32 and HFC-125, not a single listed compound in this table
  — its blend GWP is not a simple average of the pure-component rows below
  and is not asserted here; the existing `2,088` (AR4) citation in
  `../PROVENANCE.md` for R-410A is unchanged by this addition.

---

### Table A-1 to Subpart A of Part 98—Global Warming Potentials, 100-Year Time Horizon

Footnote markers (`^a` `^b` `^c` `^d` `^e`) reference the source table's own
explanatory footnotes (covering things like measurement basis and IPCC
report versioning per substance); this extraction captured the table body
but not the footnote text block. The numeric GWP values themselves are
captured in full and are what this file exists to source. Full footnote
text: <https://www.ecfr.gov/current/title-40/chapter-I/subchapter-C/part-98/subpart-A/appendix-Table%20A-1%20to%20Subpart%20A%20of%20Part%2098>

| Chemical / substance | CAS No. | Chemical formula | GWP (100-yr) |
|---|---|---|---|


| Chemical-Specific GWPs |
| Carbon dioxide | 124-38-9 | CO_2 | 1 |
| Methane | 74-82-8 | CH_4 | ^a ^d 28 |
| Nitrous oxide | 10024-97-2 | N_2 O | ^a ^d 265 |
| Fully Fluorinated GHGs |
| Sulfur hexafluoride | 2551-62-4 | SF_6 | ^a ^d 23,500 |
| Trifluoromethyl sulphur pentafluoride | 373-80-8 | SF_5 CF_3 | ^d 17,400 |
| Nitrogen trifluoride | 7783-54-2 | NF_3 | ^d 16,100 |
| PFC-14 (Perfluoromethane) | 75-73-0 | CF_4 | ^a ^d 6,630 |
| PFC-116 (Perfluoroethane) | 76-16-4 | C_2 F_6 | ^a ^d 11,100 |
| PFC-218 (Perfluoropropane) | 76-19-7 | C_3 F_8 | ^a ^d 8,900 |
| Perfluorocyclopropane | 931-91-9 | c-C_3 F_6 | ^d 9,200 |
| PFC-3-1-10 (Perfluorobutane) | 355-25-9 | C_4 F_10 | ^a ^d 9,200 |
| PFC-318 (Perfluorocyclobutane) | 115-25-3 | c-C_4 F_8 | ^a ^d 9,540 |
| Perfluorotetrahydrofuran | 773-14-8 | c-C_4 F_8 O | ^e 13,900 |
| PFC-4-1-12 (Perfluoropentane) | 678-26-2 | C_5 F_12 | ^a ^d 8,550 |
| PFC-5-1-14 (Perfluorohexane, FC-72) | 355-42-0 | C_6 F_14 | ^a ^d 7,910 |
| PFC-6-1-12 | 335-57-9 | C_7 F_16; CF_3 (CF_2)_5 CF_3 | ^b 7,820 |
| PFC-7-1-18 | 307-34-6 | C_8 F_18; CF_3 (CF_2)_6 CF_3 | ^b 7,620 |
| PFC-9-1-18 | 306-94-5 | C_10 F_18 | ^d 7,190 |
| PFPMIE (HT-70) | NA | CF_3 OCF(CF_3)CF_2 OCF_2 OCF_3 | ^d 9,710 |
| Perfluorodecalin (cis) | 60433-11-6 | Z-C_10 F_18 | ^b ^d 7,240 |
| Perfluorodecalin (trans) | 60433-12-7 | E-C_10 F_18 | ^b ^d 6,290 |
| Perfluorotriethylamine | 359-70-6 | N(C_2 F_5)_3 | ^e 10,300 |
| Perfluorotripropylamine | 338-83-0 | N(CF_2 CF_2 CF_3)_3 | ^e 9,030 |
| Perfluorotributylamine | 311-89-7 | N(CF_2 CF_2 CF_2 CF_3)_3 | ^e 8,490 |
| Perfluorotripentylamine | 338-84-1 | N(CF_2 CF_2 CF_2 CF_2 CF_3)_3 | ^e 7,260 |
| Saturated Hydrofluorocarbons (HFCs) With Two or Fewer Carbon-Hydrogen Bonds |
| (4s,5s)-1,1,2,2,3,3,4,5-octafluorocyclopentane | 158389-18-5 | trans-cyc (-CF2CF2CF2CHFCHF-) | ^e 258 |
| HFC-23 | 75-46-7 | CHF_3 | ^a ^d 12,400 |
| HFC-32 | 75-10-5 | CH_2 F_2 | ^a ^d 677 |
| HFC-125 | 354-33-6 | C_2 HF_5 | ^a ^d 3,170 |
| HFC-134 | 359-35-3 | C_2 H_2 F_4 | ^a ^d 1,120 |
| HFC-134a | 811-97-2 | CH_2 FCF_3 | ^a ^d 1,300 |
| HFC-227ca | 2252-84-8 | CF_3 CF_2 CHF_2 | ^b 2,640 |
| HFC-227ea | 431-89-0 | C_3 HF_7 | ^a ^d 3,350 |
| HFC-236cb | 677-56-5 | CH_2 FCF_2 CF_3 | ^d 1,210 |
| HFC-236ea | 431-63-0 | CHF_2 CHFCF_3 | ^d 1,330 |
| HFC-236fa | 690-39-1 | C_3 H_2 F_6 | ^a ^d 8,060 |
| HFC-329p | 375-17-7 | CHF_2 CF_2 CF_2 CF_3 | ^b 2360 |
| HFC-43-10mee | 138495-42-8 | CF_3 CFHCFHCF_2 CF_3 | ^a ^d 1,650 |
| Saturated Hydrofluorocarbons (HFCs) With Three or More Carbon-Hydrogen Bonds |
| 1,1,2,2,3,3-hexafluorocyclopentane | 123768-18-3 | cyc (-CF_2 CF_2 CF_2 CH_2 CH_2-) | ^e 120 |
| 1,1,2,2,3,3,4-heptafluorocyclopentane | 15290-77-4 | cyc (-CF_2 CF_2 CF_2 CHFCH_2-) | ^e 231 |
| HFC-41 | 593-53-3 | CH_3 F | ^a ^d 116 |
| HFC-143 | 430-66-0 | C_2 H_3 F_3 | ^a ^d 328 |
| HFC-143a | 420-46-2 | C_2 H_3 F_3 | ^a ^d 4,800 |
| HFC-152 | 624-72-6 | CH_2 FCH_2 F | ^d 16 |
| HFC-152a | 75-37-6 | CH_3 CHF_2 | ^a ^d 138 |
| HFC-161 | 353-36-6 | CH_3 CH_2 F | ^d 4 |
| HFC-245ca | 679-86-7 | C_3 H_3 F_5 | ^a ^d 716 |
| HFC-245cb | 1814-88-6 | CF_3 CF_2 CH_3 | ^b 4,620 |
| HFC-245ea | 24270-66-4 | CHF_2 CHFCHF_2 | ^b 235 |
| HFC-245eb | 431-31-2 | CH_2 FCHFCF_3 | ^b 290 |
| HFC-245fa | 460-73-1 | CHF_2 CH_2 CF_3 | ^d 858 |
| HFC-263fb | 421-07-8 | CH_3 CH_2 CF_3 | ^b 76 |
| HFC-272ca | 420-45-1 | CH_3 CF_2 CH_3 | ^b 144 |
| HFC-365mfc | 406-58-6 | CH_3 CF_2 CH_2 CF_3 | ^d 804 |
| Saturated Hydrofluoroethers (HFEs) and Hydrochlorofluoroethers (HCFEs) With One Carbon-Hydrogen Bond |
| HFE-125 | 3822-68-2 | CHF_2 OCF_3 | ^d 12,400 |
| HFE-227ea | 2356-62-9 | CF_3 CHFOCF_3 | ^d 6,450 |
| HFE-329mcc2 | 134769-21-4 | CF_3 CF_2 OCF_2 CHF_2 | ^d 3,070 |
| HFE-329me3 | 428454-68-6 | CF_3 CFHCF_2 OCF_3 | ^b 4,550 |
| 1,1,1,2,2,3,3-Heptafluoro-3-(1,2,2,2-tetrafluoroethoxy)-propane | 3330-15-2 | CF_3 CF_2 CF_2 OCHFCF_3 | ^b 6,490 |
| Saturated HFEs and HCFEs With Two Carbon-Hydrogen Bonds |
| HFE-134 (HG-00) | 1691-17-4 | CHF_2 OCHF_2 | ^d 5,560 |
| HFE-236ca | 32778-11-3 | CHF_2 OCF_2 CHF_2 | ^b 4,240 |
| HFE-236ca12 (HG-10) | 78522-47-1 | CHF_2 OCF_2 OCHF_2 | ^d 5,350 |
| HFE-236ea2 (Desflurane) | 57041-67-5 | CHF_2 OCHFCF_3 | ^d 1,790 |
| HFE-236fa | 20193-67-3 | CF_3 CH_2 OCF_3 | ^d 979 |
| HFE-338mcf2 | 156053-88-2 | CF_3 CF_2 OCH_2 CF_3 | ^d 929 |
| HFE-338mmz1 | 26103-08-2 | CHF_2 OCH(CF_3)_2 | ^d 2,620 |
| HFE-338pcc13 (HG-01) | 188690-78-0 | CHF_2 OCF_2 CF_2 OCHF_2 | ^d 2,910 |
| HFE-43-10pccc (H-Galden 1040x, HG-11) | E1730133 | CHF_2 OCF_2 OC_2 F_4 OCHF_2 | ^d 2,820 |
| HCFE-235ca2 (Enflurane) | 13838-16-9 | CHF_2 OCF_2 CHFCl | ^b 583 |
| HCFE-235da2 (Isoflurane) | 26675-46-7 | CHF_2 OCHClCF_3 | ^d 491 |
| HG-02 | 205367-61-9 | HF_2 C-(OCF_2 CF_2)_2-OCF_2 H | ^b ^d 2,730 |
| HG-03 | 173350-37-3 | HF_2 C-(OCF_2 CF_2)_3-OCF_2 H | ^b ^d 2,850 |
| HG-20 | 249932-25-0 | HF_2 C-(OCF_2)_2-OCF_2 H | ^b 5,300 |
| HG-21 | 249932-26-1 | HF_2 C-OCF_2 CF_2 OCF_2 OCF_2 O-CF_2 H | ^b 3,890 |
| HG-30 | 188690-77-9 | HF_2 C-(OCF_2)_3-OCF_2 H | ^b 7,330 |
| 1,1,3,3,4,4,6,6,7,7,9,9,10,10,12,12,13,13,15,15-eicosafluoro-2,5,8,11,14-Pentaoxapentadecane | 173350-38-4 | HCF_2 O(CF_2 CF_2 O)_4 CF_2 H | ^b 3,630 |
| 1,1,2-Trifluoro-2-(trifluoromethoxy)-ethane | 84011-06-3 | CHF_2 CHFOCF_3 | ^b 1,240 |
| Trifluoro(fluoromethoxy)methane | 2261-01-0 | CH_2 FOCF_3 | ^b 751 |
| Saturated HFEs and HCFEs With Three or More Carbon-Hydrogen Bonds |
| HFE-143a | 421-14-7 | CH_3 OCF_3 | ^d 523 |
| HFE-245cb2 | 22410-44-2 | CH_3 OCF_2 CF_3 | ^d 654 |
| HFE-245fa1 | 84011-15-4 | CHF_2 CH_2 OCF_3 | ^d 828 |
| HFE-245fa2 | 1885-48-9 | CHF_2 OCH_2 CF_3 | ^d 812 |
| HFE-254cb1 | 425-88-7 | CH_3 OCF_2 CHF_2 | ^d 301 |
| HFE-263fb2 | 460-43-5 | CF_3 CH_2 OCH_3 | ^d 1 |
| HFE-263m1; R-E-143a | 690-22-2 | CF_3 OCH_2 CH_3 | ^b 29 |
| HFE-347mcc3 (HFE-7000) | 375-03-1 | CH_3 OCF_2 CF_2 CF_3 | ^d 530 |
| HFE-347mcf2 | 171182-95-9 | CF_3 CF_2 OCH_2 CHF_2 | ^d 854 |
| HFE-347mmy1 | 22052-84-2 | CH_3 OCF(CF_3)_2 | ^d 363 |
| HFE-347mmz1 (Sevoflurane) | 28523-86-6 | (CF_3)_2 CHOCH_2 F | ^c 216 |
| HFE-347pcf2 | 406-78-0 | CHF_2 CF_2 OCH_2 CF_3 | ^d 889 |
| HFE-356mec3 | 382-34-3 | CH_3 OCF_2 CHFCF_3 | ^d 387 |
| HFE-356mff2 | 333-36-8 | CF_3 CH_2 OCH_2 CF_3 | ^b 17 |
| HFE-356mmz1 | 13171-18-1 | (CF_3)_2 CHOCH_3 | ^d 14 |
| HFE-356pcc3 | 160620-20-2 | CH_3 OCF_2 CF_2 CHF_2 | ^d 413 |
| HFE-356pcf2 | 50807-77-7 | CHF_2 CH_2 OCF_2 CHF_2 | ^d 719 |
| HFE-356pcf3 | 35042-99-0 | CHF_2 OCH_2 CF_2 CHF_2 | ^d 446 |
| HFE-365mcf2 | 22052-81-9 | CF_3 CF_2 OCH_2 CH_3 | ^b 58 |
| HFE-365mcf3 | 378-16-5 | CF_3 CF_2 CH_2 OCH_3 | ^d 0.99 |
| HFE-374pc2 | 512-51-6 | CH_3 CH_2 OCF_2 CHF_2 | ^d 627 |
| HFE-449s1 (HFE-7100) Chemical blend | 163702-07-6 | C_4 F_9 OCH_3 | ^d 421 |
|  | 163702-08-7 | (CF_3)_2 CFCF_2 OCH_3 |
| HFE-569sf2 (HFE-7200) Chemical blend | 163702-05-4 | C_4 F_9 OC_2 H_5 | ^d 57 |
|  | 163702-06-5 | (CF_3)_2 CFCF_2 OC_2 H_5 |
| HFE-7300 | 132182-92-4 | (CF_3)_2 CFCFOC_2 H_5 CF_2 CF_2 CF_3 | ^e 405 |
| HFE-7500 | 297730-93-9 | n-C_3 F_7 CFOC_2 H_5 CF(CF_3)_2 | ^e 13 |
| HG′-01 | 73287-23-7 | CH_3 OCF_2 CF_2 OCH_3 | ^b 222 |
| HG′-02 | 485399-46-0 | CH_3 O(CF_2 CF_2 O)_2 CH_3 | ^b 236 |
| HG′-03 | 485399-48-2 | CH_3 O(CF_2 CF_2 O)_3 CH_3 | ^b 221 |
| Difluoro(methoxy)methane | 359-15-9 | CH_3 OCHF_2 | ^b 144 |
| 2-Chloro-1,1,2-trifluoro-1-methoxyethane | 425-87-6 | CH_3 OCF_2 CHFCl | ^b 122 |
| 1-Ethoxy-1,1,2,2,3,3,3-heptafluoropropane | 22052-86-4 | CF_3 CF_2 CF_2 OCH_2 CH_3 | ^b 61 |
| 2-Ethoxy-3,3,4,4,5-pentafluorotetrahydro-2,5-bis[1,2,2,2-tetrafluoro-1-(trifluoromethyl)ethyl]-furan | 920979-28-8 | C_12 H_5 F_19 O_2 | ^b 56 |
| 1-Ethoxy-1,1,2,3,3,3-hexafluoropropane | 380-34-7 | CF_3 CHFCF_2 OCH_2 CH_3 | ^b 23 |
| Fluoro(methoxy)methane | 460-22-0 | CH_3 OCH_2 F | ^b 13 |
| 1,1,2,2-Tetrafluoro-3-methoxy-propane; Methyl 2,2,3,3-tetrafluoropropyl ether | 60598-17-6 | CHF_2 CF_2 CH_2 OCH_3 | ^b ^d 0.49 |
| 1,1,2,2-Tetrafluoro-1-(fluoromethoxy)ethane | 37031-31-5 | CH_2 FOCF_2 CF_2 H | ^b 871 |
| Difluoro(fluoromethoxy)methane | 461-63-2 | CH_2 FOCHF_2 | ^b 617 |
| Fluoro(fluoromethoxy)methane | 462-51-1 | CH_2 FOCH_2 F | ^b 130 |
| Saturated Chlorofluorocarbons (CFCs) |
| E-R316c | 3832-15-3 | trans-cyc (-CClFCF_2 CF_2 CClF-) | ^e 4,230 |
| Z-R316c | 3934-26-7 | cis-cyc (-CClFCF_2 CF_2 CClF-) | ^e 5,660 |
| Fluorinated Formates |
| Trifluoromethyl formate | 85358-65-2 | HCOOCF_3 | ^b 588 |
| Perfluoroethyl formate | 313064-40-3 | HCOOCF_2 CF_3 | ^b 580 |
| 1,2,2,2-Tetrafluoroethyl formate | 481631-19-0 | HCOOCHFCF_3 | ^b 470 |
| Perfluorobutyl formate | 197218-56-7 | HCOOCF_2 CF_2 CF_2 CF_3 | ^b 392 |
| Perfluoropropyl formate | 271257-42-2 | HCOOCF_2 CF_2 CF_3 | ^b 376 |
| 1,1,1,3,3,3-Hexafluoropropan-2-yl formate | 856766-70-6 | HCOOCH(CF_3)_2 | ^b 333 |
| 2,2,2-Trifluoroethyl formate | 32042-38-9 | HCOOCH_2 CF_3 | ^b 33 |
| 3,3,3-Trifluoropropyl formate | 1344118-09-7 | HCOOCH_2 CH_2 CF_3 | ^b 17 |
| Fluorinated Acetates |
| Methyl 2,2,2-trifluoroacetate | 431-47-0 | CF_3 COOCH_3 | ^b 52 |
| 1,1-Difluoroethyl 2,2,2-trifluoroacetate | 1344118-13-3 | CF_3 COOCF_2 CH_3 | ^b 31 |
| Difluoromethyl 2,2,2-trifluoroacetate | 2024-86-4 | CF_3 COOCHF_2 | ^b 27 |
| 2,2,2-Trifluoroethyl 2,2,2-trifluoroacetate | 407-38-5 | CF_3 COOCH_2 CF_3 | ^b 7 |
| Methyl 2,2-difluoroacetate | 433-53-4 | HCF_2 COOCH_3 | ^b 3 |
| Perfluoroethyl acetate | 343269-97-6 | CH_3 COOCF_2 CF_3 | ^b ^d 2 |
| Trifluoromethyl acetate | 74123-20-9 | CH_3 COOCF_3 | ^b ^d 2 |
| Perfluoropropyl acetate | 1344118-10-0 | CH_3 COOCF_2 CF_2 CF_3 | ^b ^d 2 |
| Perfluorobutyl acetate | 209597-28-4 | CH_3 COOCF_2 CF_2 CF_2 CF_3 | ^b ^d 2 |
| Ethyl 2,2,2-trifluoroacetate | 383-63-1 | CF_3 COOCH_2 CH_3 | ^b ^d 1 |
| Carbonofluoridates |
| Methyl carbonofluoridate | 1538-06-3 | FCOOCH_3 | ^b 95 |
| 1,1-Difluoroethyl carbonofluoridate | 1344118-11-1 | FCOOCF_2 CH_3 | ^b 27 |
| Fluorinated Alcohols Other Than Fluorotelomer Alcohols |
| Bis(trifluoromethyl)-methanol | 920-66-1 | (CF_3)_2 CHOH | ^d 182 |
| 2,2,3,3,4,4,5,5-Octafluorocyclopentanol | 16621-87-7 | cyc (-(CF_2)_4 CH(OH)-) | ^d 13 |
| 2,2,3,3,3-Pentafluoropropanol | 422-05-9 | CF_3 CF_2 CH_2 OH | ^d 19 |
| 2,2,3,3,4,4,4-Heptafluorobutan-1-ol | 375-01-9 | C_3 F_7 CH2OH | ^b ^d 34 |
| 2,2,2-Trifluoroethanol | 75-89-8 | CF_3 CH_2 OH | ^b 20 |
| 2,2,3,4,4,4-Hexafluoro-1-butanol | 382-31-0 | CF_3 CHFCF_2 CH_2 OH | ^b 17 |
| 2,2,3,3-Tetrafluoro-1-propanol | 76-37-9 | CHF_2 CF_2 CH_2 OH | ^b 13 |
| 2,2-Difluoroethanol | 359-13-7 | CHF_2 CH2OH | ^b 3 |
| 2-Fluoroethanol | 371-62-0 | CH_2 FCH_2 OH | ^b 1.1 |
| 4,4,4-Trifluorobutan-1-ol | 461-18-7 | CF_3 (CH_2)_2 CH_2 OH | ^b 0.05 |
| Non-Cyclic, Unsaturated Perfluorocarbons (PFCs) |
| PFC-1114; TFE | 116-14-3 | CF_2 = CF_2; C_2 F_4 | ^b 0.004 |
| PFC-1216; Dyneon HFP | 116-15-4 | C_3 F_6; CF_3 CF = CF_2 | ^b 0.05 |
| Perfluorobut-2-ene | 360-89-4 | CF_3 CF = CFCF_3 | ^b 1.82 |
| Perfluorobut-1-ene | 357-26-6 | CF_3 CF_2 CF = CF_2 | ^b 0.10 |
| Perfluorobuta-1,3-diene | 685-63-2 | CF_2 = CFCF = CF_2 | ^b 0.003 |
| Non-Cyclic, Unsaturated Hydrofluorocarbons (HFCs) and Hydrochlorofluorocarbons (HCFCs) |
| HFC-1132a; VF2 | 75-38-7 | C_2 H_2 F_2, CF_2 = CH_2 | ^b 0.04 |
| HFC-1141; VF | 75-02-5 | C_2 H_3 F, CH_2 = CHF | ^b 0.02 |
| (E)-HFC-1225ye | 5595-10-8 | CF_3 CF = CHF(E) | ^b 0.06 |
| (Z)-HFC-1225ye | 5528-43-8 | CF_3 CF = CHF(Z) | ^b 0.22 |
| Solstice 1233zd(E) | 102687-65-0 | C_3 H_2 ClF_3; CHCl = CHCF_3 | ^b 1.34 |
| HCFO-1233zd(Z) | 99728-16-2 | (Z)-CF_3 CH = CHCl | ^e 0.45 |
| HFC-1234yf; HFO-1234yf | 754-12-1 | C_3 H_2 F_4; CF_3 CF = CH_2 | ^b 0.31 |
| HFC-1234ze(E) | 1645-83-6 | C_3 H_2 F_4; trans-CF_3 CH = CHF | ^b 0.97 |
| HFC-1234ze(Z) | 29118-25-0 | C_3 H_2 F_4; cis-CF_3 CH = CHF; CF_3 CH = CHF | ^b 0.29 |
| HFC-1243zf; TFP | 677-21-4 | C_3 H_3 F_3, CF_3 CH = CH_2 | ^b 0.12 |
| (Z)-HFC-1336 | 692-49-9 | CF_3 CH = CHCF_3 (Z) | ^b 1.58 |
| HFO-1336mzz(E) | 66711-86-2 | (E)-CF_3 CH = CHCF_3 | ^e 18 |
| HFC-1345zfc | 374-27-6 | C_2 F_5 CH = CH_2 | ^b 0.09 |
| HFO-1123 | 359-11-5 | CHF=CF_2 | ^e 0.005 |
| HFO-1438ezy(E) | 14149-41-8 | (E)-(CF_3)_2 CFCH = CHF | ^e 8.2 |
| HFO-1447fz | 355-08-8 | CF_3 (CF_2)_2 CH = CH_2 | ^e 0.24 |
| Capstone 42-U | 19430-93-4 | C_6 H_3 F_9, CF_3 (CF_2)_3 CH = CH_2 | ^b 0.16 |
| Capstone 62-U | 25291-17-2 | C_8 H_3 F_13, CF_3 (CF_2)_5 CH = CH_2 | ^b 0.11 |
| Capstone 82-U | 21652-58-4 | C_10 H_3 F_17, CF_3 (CF_2)_7 CH = CH_2 | ^b 0.09 |
| (e)-1-chloro-2-fluoroethene | 460-16-2 | (E)-CHCl = CHF | ^e 0.004 |
| 3,3,3-trifluoro-2-(trifluoromethyl)prop-1-ene | 382-10-5 | (CF_3)_2 C = CH_2 | ^e 0.38 |
| Non-Cyclic, Unsaturated CFCs |
| CFC-1112 | 598-88-9 | CClF=CClF | ^e 0.13 |
| CFC-1112a | 79-35-6 | CCl_2=CF_2 | ^e 0.021 |
| Non-Cyclic, Unsaturated Halogenated Ethers |
| PMVE; HFE-216 | 1187-93-5 | CF_3 OCF = CF_2 | ^b 0.17 |
| Fluoroxene | 406-90-6 | CF_3 CH_2 OCH = CH_2 | ^b 0.05 |
| Methyl-perfluoroheptene-ethers | N/A | CH_3 OC_7 F_13 | ^e 15 |
| Non-Cyclic, Unsaturated Halogenated Esters |
| Ethenyl 2,2,2-trifluoroacetate | 433-28-3 | CF_3 COOCH=CH_2 | ^e 0.008 |
| Prop-2-enyl 2,2,2-trifluoroacetate | 383-67-5 | CF_3 COOCH_2 CH=CH_2 | ^e 0.007 |
| Cyclic, Unsaturated HFCs and PFCs |
| PFC C-1418 | 559-40-0 | c-C_5 F_8 | ^d 2 |
| Hexafluorocyclobutene | 697-11-0 | cyc (-CF=CFCF_2 CF_2-) | ^e 126 |
| 1,3,3,4,4,5,5-heptafluorocyclopentene | 1892-03-1 | cyc (-CF_2 CF_2 CF_2 CF=CH-) | ^e 45 |
| 1,3,3,4,4-pentafluorocyclobutene | 374-31-2 | cyc (-CH=CFCF_2 CF_2-) | ^e 92 |
| 3,3,4,4-tetrafluorocyclobutene | 2714-38-7 | cyc (-CH=CHCF_2 CF_2-) | ^e 26 |
| Fluorinated Aldehydes |
| 3,3,3-Trifluoro-propanal | 460-40-2 | CF_3 CH_2 CHO | ^b 0.01 |
| Fluorinated Ketones |
| Novec 1230 (perfluoro (2-methyl-3-pentanone)) | 756-13-8 | CF_3 CF_2 C(O)CF (CF3)_2 | ^b 0.1 |
| 1,1,1-trifluoropropan-2-one | 421-50-1 | CF_3 COCH_3 | ^e 0.09 |
| 1,1,1-trifluorobutan-2-one | 381-88-4 | CF_3 COCH_2 CH_3 | ^e 0.095 |
| Fluorotelomer Alcohols |
| 3,3,4,4,5,5,6,6,7,7,7-Undecafluoroheptan-1-ol | 185689-57-0 | CF_3 (CF_2)_4 CH_2 CH_2 OH | ^b 0.43 |
| 3,3,3-Trifluoropropan-1-ol | 2240-88-2 | CF_3 CH_2 CH_2 OH | ^b 0.35 |
| 3,3,4,4,5,5,6,6,7,7,8,8,9,9,9-Pentadecafluorononan-1-ol | 755-02-2 | CF_3 (CF_2)_6 CH_2 CH_2 OH | ^b 0.33 |
| 3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,11-Nonadecafluoroundecan-1-ol | 87017-97-8 | CF_3 (CF_2)_8 CH_2 CH_2 OH | ^b 0.19 |
| Fluorinated GHGs With Carbon-Iodine Bond(s) |
| Trifluoroiodomethane | 2314-97-8 | CF_3 I | ^b 0.4 |
| Remaining Fluorinated GHGs with Chemical-Specific GWPs |
| Dibromodifluoromethane (Halon 1202) | 75-61-6 | CBr_2 F_2 | ^b 231 |
| 2-Bromo-2-chloro-1,1,1-trifluoroethane (Halon-2311/Halothane) | 151-67-7 | CHBrClCF_3 | ^b 41 |
| Heptafluoroisobutyronitrile | 42532-60-5 | (CF_3)_2 CFCN | ^e 2,750 |
| Carbonyl fluoride | 353-50-4 | COF_2 | ^e 0.14 |
| Default GWPs for Compounds for Which Chemical-Specific GWPs Are Not Listed Above |
| Fully fluorinated GHGs ^g | 9,200 |
| Saturated hydrofluorocarbons (HFCs) with 2 or fewer carbon-hydrogen bonds ^g | 3,000 |
| Saturated HFCs with 3 or more carbon-hydrogen bonds ^g | 840 |
| Saturated hydrofluoroethers (HFEs) and hydrochlorofluoroethers (HCFEs) with 1 carbon-hydrogen bond ^g | 6,600 |
| Saturated HFEs and HCFEs with 2 carbon-hydrogen bonds ^g | 2,900 |
| Saturated HFEs and HCFEs with 3 or more carbon-hydrogen bonds ^g | 320 |
| Saturated chlorofluorocarbons (CFCs) ^g | 4,900 |
| Fluorinated formates | 350 |
| Cyclic forms of the following: unsaturated perfluorocarbons (PFCs), unsaturated HFCs, unsaturated CFCs, unsaturated hydrochlorofluorocarbons (HCFCs), unsaturated bromofluorocarbons (BFCs), unsaturated bromochlorofluorocarbons (BCFCs), unsaturated hydrobromofluorocarbons (HBFCs), unsaturated hydrobromochlorofluorocarbons (HBCFCs), unsaturated halogenated ethers, and unsaturated halogenated esters ^g | 58 |
| Fluorinated acetates, carbonofluoridates, and fluorinated alcohols other than fluorotelomer alcohols ^g | 25 |
| Fluorinated aldehydes, fluorinated ketones, and non-cyclic forms of the following: unsaturated perfluorocarbons (PFCs), unsaturated HFCs, unsaturated CFCs, unsaturated HCFCs, unsaturated BFCs, unsaturated BCFCs, unsaturated HBFCs, unsaturated HBCFCs, unsaturated halogenated ethers and unsaturated halogenated esters ^g | 1 |
| Fluorotelomer alcohols ^g | 1 |
| Fluorinated GHGs with carbon-iodine bond(s) ^g | 1 |
| Other fluorinated GHGs ^g | 1,800 |
| ^a The GWP for this compound was updated in the final rule published on November 29, 2013 [78 FR 71904] and effective on January 1, 2014. |
| ^b This compound was added to table A-1 in the final rule published on December 11, 2014, and effective on January 1, 2015. |
| ^c The GWP for this compound was updated in the final rule published on December 11, 2014, and effective on January 1, 2015. |
| ^d The GWP for this compound was updated in the final rule published on April 25, 2024 and effective on January 1, 2025. |
| ^e The GWP for this compound was added to table A-1 in the final rule published on April 25, 2024 and effective on January 1, 2025. |
| ^f For electronics manufacturing (as defined in § 98.90), the term “fluorinated GHGs” in the definition of each fluorinated GHG group in § 98.6 shall include fluorinated heat transfer fluids (as defined in § 98.6), whether or not they are also fluorinated GHGs. |
| ^g The GWP for this fluorinated GHG group was updated in the final rule published on April 25, 2024 and effective on January 1, 2025. |
