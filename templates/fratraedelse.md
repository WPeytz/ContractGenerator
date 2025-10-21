# Fratrædelsesaftale

---

**{{ C_Name }}**

og

**{{ P_Name }}**

```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```

## Mellem

**{{ C_Name }}**
{{ C_Address }}
CVR-nr. {{ C_CoRegCVR }}

("Selskabet")

&nbsp;

og

&nbsp;

**{{ P_Name }}**
{{ P_Address }}

("Medarbejderen")

&nbsp;

i det følgende hver for sig betegnet en "Part" og i fællesskab "Parterne"

er der

- idet det bemærkes, at Medarbejderen tiltrådte en stilling hos Selskabet den {{ EmploymentStart }} og var ansat i henhold til vilkår i ansættelseskontrakt underskrevet den {{ ContractSignedDate }} ("Ansættelsesaftalen").

- idet Medarbejderen af Selskabet er blevet opsagt den {{ TerminationDate }} til fratræden {{ SeparationDate }}.

Dags dato indgået følgende

&nbsp;

```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```

# Fratrædelsesaftale

##    Fratræden

1.1 Medarbejderen er af Selskabet opsagt til fratræden den {{ SeparationDate }} ("Fratrædelsestidspunktet"). Parterne har i den forbindelse indgået denne aftale om vilkårene for fratræden ("Aftalen").

1.2 Medarbejderen vil blive fritstillet efter en kortere overleveringsperiode og senest den {{ ReleaseDate }} ("Fritstillingstidspunktet"), så Medarbejderen ikke skal give møde hos Selskabet efter Fritstillingstidspunktet, og kan tage anden ansættelse i ikke konkurrerende virksomhed i den resterende del af opsigelsesperioden frem til Fratrædelsestidspunktet ("Fritstillingsperioden").

1.3	Ved "Koncernselskab" forstås i denne aftale ethvert selskab, der indgår i {{ C_Name }}-koncernen.

##    Løn og andre lønandele

2.1 Selskabet betaler løn indtil Fratrædelsestidspunktet månedsvis bagud som sædvanligt svarende til {{ MonthlySalary }} kr. pr. måned. Lønnen reguleres ikke i Fritstillingsperioden.

{% if noOffset %}
2.2 Selskabet har accepteret, at løn fra anden ansættelse ikke skal modregnes i Medarbejderens krav på løn i Fritstillingsperioden fra Selskabet. Dette indebærer, at Medarbejderen har mulighed for dobbeltløn i Fritstillingsperioden.
{% else %}
2.3 Hvis Medarbejderen i Fritstillingsperioden oppebærer løn fra anden ansættelse eller indtægt fra selvstændig virksomhed, skal denne indkomst modregnes i Medarbejderens krav på løn fra Selskabet. Medarbejderen er forpligtet til uden ugrundet ophold skriftligt at orientere Selskabet om enhver sådan indkomst i Fritstillingsperioden.
{% endif %}

{% if HealthInsuranceIncluded %}
2.4 Selskabet opretholder desuden betaling til sundhedsforsikring indtil Fratrædelsestidspunktet.
{% endif %}

{% if PensionIncluded %}
2.5 Selskabet opretholder pensions- og forsikringsordning indtil Fratrædelsestidspunktet, og indbetaler pensionsbidrag ({{ PensionPercentage }}%, i alt {{ PensionAmount }} kr.) som sædvanligt indtil Fratrædelsestidspunktet.
{% endif %}

{% if LunchSchemeIncluded %}
2.6 Medarbejderen udtræder af firmafrokostordningen pr. Fritstillingstidspunktet.
{% endif %}

{% if Bonus1 %}
##    Bonus (STI)

3.1	Medarbejderen er omfattet af en kontant bonusordning benævnt {{ CashBonusProgram }} (“Kontant Bonus Program”). Medarbejderen har ret til bonus i det omfang, betingelserne for opnåelse af bonus i henhold til Selskabets Kontante Bonus Program er opfyldt. Størrelsen af bonussen afhænger af opfyldelsen af de økonomiske og eventuelle øvrige mål, der fremgår af Kontant Bonus Programmet for det pågældende år.

3.2 Ansættelse i hele bonusåret

Idet Medarbejderen har været ansat i hele bonusåret {{ BonusYear1 }}, beregnes bonus fuldt ud i overensstemmelse med Kontant Bonus Programmet for {{ BonusYear1 }}.

{% if BonusYear2 %}
3.3	Ansættelse i en del af bonusåret

Idet Medarbejderen alene har været ansat i en del af bonusåret {{ BonusYear2 }}, beregnes bonus forholdsmæssigt (pro rata) for den periode, Medarbejderen har været ansat i bonusåret, i overensstemmelse med Kontant Bonus Programmet for {{ BonusYear2 }}.
{% endif %}

3.4	Bonus udbetales på det sædvanlige udbetalingstidspunkt for det pågældende bonusår.

{% elif Bonus2 %}

3.5	Medarbejderen er omfattet af en kontant bonusordning benævnt [   ] (“Kontant Bonus Program”). Parterne har i forbindelse med denne Aftale taget konkret stilling til Medarbejderens bonus for bonusårene {{ BonusYear1 }} og {{ BonusYear2 }}.

3.6	For bonusåret {{ BonusYear1 }} har Parterne aftalt, at Medarbejderen er berettiget til en bonus på {{BonusAmount1}} kr. Bonusbeløbet er endeligt fastsat og uafhængigt af, om Selskabet op-fylder de finansielle eller øvrige mål på selskabs- eller koncernniveau, som fremgår af Kontant Bonus Programmet. Bonussen for {{ BonusYear1 }} udbetales på det tidspunkt, der indtræder først af enten det sædvanlige udbetalingstidspunkt for bonus eller sam-men med Medarbejderens sidste månedsløn for bonusåret.

3.7	For bonusåret {{ BonusYear2 }} har Parterne tilsvarende aftalt, at Medarbejderen er berettiget til en bonus på {{BonusAmount2}} kr. Bonusbeløbet er endeligt fastsat og uafhængigt af, om Selskabet opfylder de finansielle eller øvrige mål på selskabs- eller koncernniveau. Bonussen for {{ BonusYear2 }} udbetales sammen med Medarbejderens sidste månedsløn.

3.8	De ovennævnte bonusbeløb udgør fuld og endelig bonus for de respektive bonusår, og Medarbejderen har ikke krav på yderligere bonus eller anden variabel aflønning vedrørende disse år.

{% endif %}

{% if LTIEligible %}
##    Aktiebaseret aflønning (LTI)

4.1	Medarbejderen er omfattet af Selskabets langsigtede aktieaflønningsprogram (LTIP-programmet), der administreres i henhold til de til enhver tid gældende retningslinjer fastsat af Selskabet og/eller Koncernselskaber.

4.2	Deltagelse i LTIP-programmet udgør ikke en del af Medarbejderens faste løn, og Selska-bet kan til enhver tid frit ændre, suspendere eller bringe programmet til ophør. Der kan derfor ikke rejses krav om fortsat deltagelse eller tildeling af yderligere aktiebaserede incita-menter.

4.3	Parterne har i forbindelse med denne Aftale taget konkret stilling til Medarbejderens rettighe-der under LTIP-programmet i forbindelse med fratræden:

{% if LTIRights %}
4.4	Parterne er enige om, at Medarbejderen bevarer samtlige optjente og vestede warrants, stock options og RSU’er frem til fratrædelsestidspunktet. Vesting ophører på Fratrædelsestidspunk-tet, og der optjenes ikke yderligere rettigheder herefter.

4.5	Afregning sker på det sædvanlige tidspunkt til LTIP-programmets bestemmelser, enten ved kontant afregning eller ved overførsel af de relevante aktier til Medarbejderens depot, af-hængigt af programmets struktur og den faktiske udmøntningsform.

{% else %}
4.6	Parterne er enige om, at samtlige optjente, vestede, uoptjente og ikke-vestede warrants, stock options og RSU’er bortfalder uden kompensation, idet Medarbejderen ikke opfylder be-tingelserne i LTIP-programmet for bevarelse af tildelte rettigheder.

4.7	Selskabet forbeholder sig ret til at afregne eventuelle tildelinger i overensstemmelse med de til enhver tid gældende programregler, herunder at foretage reguleringer eller bortfald i til-fælde af væsentlig misligholdelse af ansættelsesforholdet eller denne Aftale.

{% endif %}
{% endif %}

##    Fratrædelsesgodtgørelse

5.1	Medarbejderen har krav på fratrædelsesgodtgørelse i henhold til funktionærlovens § 2a. Godtgørelsen beregnes på grundlag af Medarbejderens aktuelle månedsløn på Fratræ-delsestidspunktet, inklusive alle faste og variable lønandele, herunder fast løn, værdien af Selskabets pensionsbidrag samt eventuel bonus opgjort pro rata for en måned.

{% if years_12 %}
5.2	Idet Medarbejderen på fratrædelsestidspunktet har 12 års anciennitet eller mere, udgør fratrædelsesgodtgørelsen en (1) måneds løn beregnet på ovenstående grundlag.

{% elif years_17 %}
5.3	Idet Medarbejderen på fratrædelsestidspunktet har 17 års anciennitet eller mere, udgør fratrædelsesgodtgørelsen tre (3) måneders løn beregnet på ovenstående grundlag.
{% endif %}

5.4	Da pensionsbidraget allerede indgår i lønberegningen, beregnes der ikke særskilt pensi-onsbidrag af fratrædelsesgodtgørelsen. Beløbet udløser heller ikke krav på feriegodtgørelse, og der optjenes ikke ferie heraf.

5.5	Fratrædelsesgodtgørelsen udbetales sammen med Medarbejderens sidste månedsløn.

##    Aftalt Fratrædelsesgodtgørelse 

6.1	Som et led i denne Aftale har Parterne aftalt, at Selskabet betaler en godtgørelse til Medarbejderen på et beløb svarende til {{ NoCompensationMonths }} måneders fast løn inklusive værdien af pensionsbidrag ({{ PensionPercentage }} %), i alt {{ PensionCompensationAmount }} kr., {% if fixedCompensationAmount %} eller alternativt et fikseret beløb på {{ fixedCompensationNumber }} kr. {% endif %}

6.2	Godtgørelsen beregnes alene på grundlag af Medarbejderens faste løn inklusive vær-dien af Selskabets pensionsbidrag. Der foretages ingen særskilt pensionsindbetaling af beløbet. Godtgørelsen udløser ikke krav på feriegodtgørelse, og der optjenes ikke ferie heraf.

6.3	Godtgørelsen udbetales sammen med Medarbejderens sidste lønudbetaling.

6.4	Betalingen af godtgørelsen er betinget af, at Medarbejderen ikke rejser krav på godtgørelse i medfør af funktionærlovens § 2 b, ligebehandlingsloven, forskelsbe-handlingsloven eller andet tilsvarende grundlag, og at Medarbejderen ikke fremsæt-ter krav på ydelser, der ikke udtrykkeligt er anført i denne Aftale.

##    Ferie

7.1	Medarbejderen er omfattet af ferieloven.

{% if HolidayLeave %}

7.2	Idet Medarbejderen fritstilles helt eller delvist i opsigelsesperioden, er Parterne enige om, at ferie automatisk anses for afviklet i Fritstillingsperioden, i det omfang opsigelses-perioden dækker det nødvendige antal feriedage, og at ferie anses for placeret i over-ensstemmelse med ferielovens regler, og Medarbejderen kan ikke kræve særskilt varsling eller anden kompensation herfor ud over hvad der fremgår af punktet nedenfor vedrøren-de indbetaling til FerieKonto.

{% else %}
7.3	Idet Medarbejderen fortsætter arbejdet i opsigelsesperioden, er Parterne enige om, at ferie afvikles efter nærmere aftale i følgende perioder:
[indsæt konkrete ferieperioder]. 

Parterne er enige om, at ferien dermed anses for korrekt varslet og placeret i henhold til ferielovens bestemmelser.

7.4	Parterne er enige om, at {{ NoHolidayDays }} feriedage ikke kan afvikles inden fratrædelsestidspunktet. Selskabet indbetaler derfor værdien af disse dage til.

7.5	Parterne er enige om, at eventuelle optjente feriefridage afvikles inden fratrædelsestids-punktet. Feriefridage, der ikke afvikles inden fratrædelsestidspunktet, bortfalder uden økonomisk kompensation, medmindre andet udtrykkeligt er aftalt.

{% endif %}

{% if MobileCompIncluded %}
## Telefon

8.1	Medarbejderen skal aflevere alle genstande og dokumenter, som tilhører Selskabet, men som er i Medarbejderens besiddelse, herunder mobiltelefon, nøgler, adgangskort m.v., til Selskabet på Fritstillingstidspunktet.

{% if PhoneComp %}
8.2	Som kompensation for aflevering af mobiltelefon er Medarbejderen berettiget til at modtage den skattemæssige værdi af fri telefon fra [] og indtil Fratrædelsestidspunktet.

8.3	Medarbejderen er berettiget til at overtage det af Medarbejderen under ansættelsen be-nyttede telefonnummer {{ PhoneNumber }}. Medarbejderen varetager selv det praktiske i den for-bindelse og kordinerer det praktiske med {{ ManagerName }}.

{% endif %}
{% endif %}

## Immaterielle rettigheder, know-how m.v.

9.1	Selskabet har ejendomsretten til know-how, opfindelser, værker, produktionsmetoder og øvrige intellektuelle rettigheder, som Medarbejderen har frembragt eller udviklet som led i sit ansættelsesforhold med Selskabet, jf. også i Ansættelseskontrakten. Ligeledes har Selskabet ejendomsretten til know-how, opfindelser, værker, produktionsmetoder og øvrige intellektuelle rettigheder, som Medarbejderen måtte have frembragt eller udviklet under ansættelsen og inden Fritstillingstidspunktet.

## Tavshedspligt 

10.1 Det påhviler Medarbejderen såvel i Fritstillingsperioden som efter Fratrædelsestidspunk-tet at iagttage fuldstændig tavshed om Selskabets forhold og om, hvad Medarbejderen i øvrigt måtte være eller blive bekendt med som følge af sin stilling, der ikke er bestemt for tredjemand, jf. også i Ansættelseskontrakten.

10.2 Medarbejderen er også efter Fratrædelsestidspunktet omfattet af markedsføringslovens § 3 samt lov om forretningshemmeligheder, der blandt andet forhindrer anvendelse af Sel-skabets erhvervshemmeligheder m.v.

10.3 Overtrædelse af tavshedspligten anses som væsentlig misligholdelse af Ansættelsesafta-len og Aftalen og kan resultere i, at ansættelsesforholdet bringes til ophør øjeblikkeligt, uanset denne Aftalen.

##	Loyalitet 
11.1	Medarbejderen er i Fritstillingsperioden fortsat bundet af sin almindelige loyalitetsfor-pligtelse, herunder pligten til ikke at tage ansættelse i eller påbegynde konkurrerende virksomhed, påvirke kunder, forretningsforbindelser eller Selskabets medarbejdere til skade for Selskabet
11.2	Medarbejderen er i Fritstillingsperioden berettiget til at søge og påbegynde andet rele-vant arbejde, herunder selvstændig virksomhed. Medarbejderen er i den forbindelse ikke berettiget til at søge ansættelse i og/eller påbegynde konkurrerende virksomhed uden Selskabets samtykke, idet dette er en del af Medarbejderens almindelige loyalitetspligt under ansættelsen.

##	Kommunikation

12.1	Selskabet varetager al kommunikation om Medarbejderens fratræden både internt og eksternt. Denne Aftalen er indgået i gensidig tillid til loyal kommunikation og optræden fra alle involverede parter.

12.2	Medarbejderen og Selskabet forpligter sig til hverken direkte eller indirekte at fremsæt-te, offentliggøre eller på anden måde kommunikere nedsættende udtalelser om den an-den part i Aftalen, hverken mundtligt eller skriftligt. Dette gælder i kommunikation med kunder, forretningsforbindelser, samarbejdspartnere og medarbejdere i Selskabet eller på anden måde.

12.3	Parterne er i relation til brug af sociale netværkstjenester underlagt de almindelige tavs-heds- og loyalitetsforpligtelser samt krav om ordentlig optræden. Disse forpligtelser er fortsat gældende, og Parterne skal derfor afholde sig fra at udtale sig illoyalt om hinan-den på de sociale medier og i andre offentlige eller halvoffentlige sammenhænge. Med-arbejderen skal ikke senere end på Fratrædelsestidspunktet opdatere eventuelle oplys-ninger om sin ansættelse i Selskabet, så det fremgår, at Medarbejderen er fratrådt sin stilling hos Selskabet.

##   Skat

13.1	Samtlige ydelser udbetalt i henhold til Aftalen udbetales af Selskabet uden nogen skat-temæssige forudsætninger, og Medarbejderens endelige skattemæssige ligning er Sel-skabet uvedkommende. Dette ændrer ikke ved, at Selskabet på sædvanlig vis skal foreta-ge skatteindeholdelse af enhver skattepligtig ydelse, før udbetaling finder sted.  

{% if Tax %}
13.2    Ved udbetaling af fratrædelsesgodtgørelsen indeholder Selskabet skat baseret på en formodning om, at fratrædelsesgodtgørelsen beskattes efter ligningslovens § 7 U, efter hvilken et beløb på 8.000 kr. er skattefrit. Selskabet kan dog ikke garantere, at Skattesty-relsen vil godkende, at Medarbejderen kan beskattes af fratrædelsesgodtgørelsen efter ligningslovens § 7 U.
{% endif %}

##	Fuld og endelig afgørelse 
14.1	Parterne er enige om, at denne Aftale udgør fuld og endelig afgørelse af ethvert mellemværende mellem Medarbejderen, Selskabet og Koncernselskaber i anledning af ansættelsesforholdet og dets ophør. Aftalen har til formål at skabe en endelig og gensidig afklaring af alle økonomiske og ansættelsesretlige spørgsmål, så der ikke efterfølgende kan rejses krav mellem Parterne vedrørende ansættelsesforholdet.

14.2	Aftalen omfatter både aktuelle og potentielle krav, som Medarbejderen måtte have eller kunne tænkes at rejse mod Selskabet eller Koncernselskaber, uanset om kra-vene udspringer af lov, overenskomst, individuel aftale eller andet retsgrundlag. Dette gælder blandt andet, men ikke begrænset til, krav vedrørende løn, bonus, pension, ferie, godtgørelse, erstatning, fratrædelsesvilkår, G-dage, eller ethvert an-det forhold, der udspringer af ansættelsesforholdet eller dets ophør.

14.3	Aftalen er indgået under den udtrykkelige forudsætning, at Medarbejderen ikke rejser krav om godtgørelse i forbindelse med opsigelsen, herunder krav efter funktionærlo-vens § 2 b, ligebehandlingsloven, forskelsbehandlingsloven eller andet tilsvarende grundlag, og at Medarbejderen heller ikke fremsætter krav på yderligere løn, ferie-penge eller andre ydelser over for Selskabet eller Koncernselskaber.

{% if noAssistance %}
14.4	Medarbejderen er opfordret til og har haft lejlighed til at indhente juridisk bistand in-den underskrivelsen af denne Aftale. Medarbejderen erklærer at have haft tilstræk-kelig tid og mulighed for at gennemgå Aftalen og forstå dens indhold, inden under-skrift.
{% else %}
14.4	Medarbejderen har været bistået af {{ EmployeeLawyer }} i forbindelse med gennemgangen og indgåelsen af Aftalen og erklærer at have forstået Aftalens indhold forud for underskrift.
{% endif %}

##	Fortrolighed 
15.1	Indholdet af Aftalen er fortroligt mellem Parterne. 


##	Lovvalg og værneting

16.1	Denne Aftale er reguleret af dansk ret.

{% if Court %}
16.2	Tvister, der måtte opstå i anledning af denne Aftale, herunder dens fortolkning og opfyl-delse, skal indbringes for [indsæt byret/by navn] som aftalt værneting, med sædvanlig henvisnings- og appeladgang i henhold til retsplejelovens regler.
{% else %}
16.2	Tvister, der måtte opstå i anledning af denne Aftale, herunder dens fortolkning og opfyl-delse, afgøres ved voldgift i henhold til den i Ansættelsesaftalen aftalte voldgiftsbe-stemmelse. Voldgiftsretten nedsættes og behandler sagen i overensstemmelse med de procedureregler, der fremgår af ansættelsesaftalen og de heri omhandlede voldgiftsvil-kår.
{% endif %}

##	Acceptfrist 
17.1	Aftalen er Selskabets tilbud til Medarbejderen om fratrædelse på de vilkår, der er beskre-vet ovenfor. Hvis Aftalen ikke er underskrevet af Medarbejderen senest den {{AcceptanceDeadline }} kl. 12.00, bortfalder Aftalen i sin helhed.

##	Underskrift
18.1	Denne Aftalen underskrives elektronisk.


&nbsp;

&nbsp;

&nbsp;

**For {{ C_Name }}**

&nbsp;

&nbsp;

&nbsp;

________________________________

**{{ C_Representative }}**


&nbsp;

&nbsp;

**Medarbejder**

&nbsp;

&nbsp;

&nbsp;

________________________________

**{{ P_Name }}**
