"""Rules that read the SCAR narratives: who named a feature (the namer clause), what it is named after (the honoree clause),
and the kind of honour. Imported by 01_clean.py. Conservative: anything the rules cannot read is 'unknown'."""
import re

WS = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).replace("&#40;", "(").replace("&#41;", ")").replace("&amp;", "&").strip()

# ---- the namer: agencies and expeditions -> nation (the order matters: first match in the namer clause wins) ----
NAMERS = [
    (r"US-?ACAN|US-SCAN|\bACAN\b|Advisory Committee on Antarctic Names|US Board on Geographic Names|U\.?S\.? ?BGN|\bUSAS\b|ByrdAE|Byrd Antarctic Expedition|\bByrd\b|\bRARE\b|Ronne|\bUSEE\b|Wilkes|United States Exploring|Ellsworth|\bUSN\b|U\.S\. Navy|United States Navy|Operation Highjump|Operation Windmill|USARP|\bUSGS\b|American|\bU\.S\.|United States|Palmer|Pendleton|\bLASE\b|Antarctic Search for Meteorites", "United States"),
    (r"NZ-?APC|NZGB|New Zealand|NZGSAE|NZARP|NZTAE|\bVUWAE\b|Victoria University of Wellington|\bNZ\b|NZGSAE|NZ Antarctic", "New Zealand"),
    (r"ANCA|ANARE|Australian|\bAAE\b|Australasian Antarctic Expedition|BANZARE|Mawson|\bAAD\b|Antarctic Names Committee of Australia", "Australia"),
    (r"UK-?APC|Br-?APC|\bAPC\b|Antarctic Place-?names Committee|\bFIDS\b|FIDASE|\bBAS\b|British Antarctic Survey|\bBrAE\b|\bBGLE\b|British|Discovery Investigations|\bDI\b|ScotNAE|Scottish|\bSNAE\b|\bTAE\b|Trans-Antarctic Expedition|\bRN\b|Royal Navy|Admiralty|\bScott\b|Shackleton|Bruce|Biscoe|Foster|Weddell|Bransfield|James Clark Ross|\bRoss\b|Rymill|Discovery Committee|\bCook\b|Enderby|Balleny|Kemp|Powell|Smith", "United Kingdom"),
    (r"Norw|NBSAE|Lars Christensen|Christensen|Amundsen|Riiser-Larsen|Norsk Polar|Norway|Larsen|Mikkelsen|\bNARE\b|Holtedahl", "Norway"),
    (r"Belg|de Gerlache|Gerlache", "Belgium"),
    (r"\bFrAE\b|French|France|Charcot|Dumont d'Urville|d'Urville|Expéditions Polaires|Kerguelen", "France"),
    (r"German|GerAE|Drygalski|Filchner|Ritscher|Schwabenland|GANOVEX|Alfred Wegener|\bAWI\b|Dallmann", "Germany"),
    (r"Swed|SwedAE|Nordenskj", "Sweden"),
    (r"Japan|JARE", "Japan"),
    (r"Soviet|Russia|USSR|SovAE|Bellingshausen|Lazarev", "Russia"),
    (r"Argentin", "Argentina"),
    (r"Chile|\bCAE\b|Pardo", "Chile"),
    (r"Bulgar", "Bulgaria"),
    (r"Polish|Poland", "Poland"), (r"Chinese|China|CHINARE", "China"), (r"\bIndian\b|India", "India"), (r"Italian|Italy|PNRA", "Italy"),
    (r"Korea", "South Korea"), (r"Spanish|Spain", "Spain"), (r"South Africa|SANAE", "South Africa"), (r"Czech", "Czech Republic"),
    (r"Ukrain", "Ukraine"), (r"Ecuador", "Ecuador"), (r"Urugua", "Uruguay"), (r"Brazil", "Brazil"), (r"Peru", "Peru"),
    (r"Finn|Finland", "Finland"), (r"Dutch|Netherlands", "Netherlands"), (r"Canad", "Canada"),
]
NAMERS_C = [(re.compile(p), n) for p, n in NAMERS]


def namer_nation(clause):
    """The nation of the first agency, expedition or leader named in the namer clause (text between 'named' and 'for/after')."""
    best = None
    for rx, nat in NAMERS_C:
        m = rx.search(clause)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), nat, m.group(0))
    return (best[1], best[2]) if best else (None, None)


HON = re.compile(r"\b(?:re)?named\b(?P<namer>[^;]{0,220}?)\b(?P<prep>for|after|in honou?r of|in memory of|to commemorate|from|because|in association with|descriptively|by association)\b(?P<rest>.*)", re.I | re.S)
HON2 = re.compile(r"\b(?P<prep>in honou?r of|honou?rs|commemorates|to commemorate|in memory of|after whom|for whom)\b(?P<rest>.*)", re.I | re.S)


MEANING = re.compile(r"(?:^|\.\s)[A-ZÆØÅ][\w-]{0,20}\.?\s?=\s?(?:the |a )?[a-z]|\bnamed [A-ZÆØÅÔ][\w'-]+(?:[ -][\w'-]+){0,3} \((?:the |a |an )?[a-z][^)]{0,60}\)|\bnamed according to its\b|\b(?:is|means|meaning) (?:the )?(?:Korean|Chinese|Japanese|Norwegian|German|Russian|Bulgarian|Polish|Spanish|French|Italian|Maori) word\b", re.S)
FR_ES = [(re.compile(r"\b(?:en l'honneur d[eu']|en hommage [àa]|baptis[ée]e? en l'honneur d[eu']|en recuerdo de(?:l)?|en honor a(?:l)?|en homenaje a(?:l)?|in onore di|in memoria di|zu Ehren von|nach)\s?(?P<rest>.*)", re.I | re.S), "for"),
         (re.compile(r"\b(?:d'après le nom d[eu']|nom du navire|del buque|nombre del buque|por el buque|du navire)\s?(?P<rest>.*)", re.I | re.S), "for-ship"),
         (re.compile(r"\b(?:corresponde al apellido d(?:el|e)|en el apellido d(?:el|e))\s?(?P<rest>.*)", re.I | re.S), "for-person"),
         (re.compile(r"(?:\bcorresponde al nombre d(?:el|e)|^Pour |^Par )\s?(?P<rest>.*)", re.I | re.S), "for"),
         (re.compile(r"\b(?:nom descriptif|nombre descriptivo|descriptivo|descriptif|por su forma|por su aspecto|en raison de)\b(?P<rest>.*)", re.I | re.S), "because")]


def clauses(text):
    """(namer clause, preposition, honoree clause) from the first statement that names something; None if none."""
    t = WS(text)
    for m in HON.finditer(t):
        namer = m.group("namer")
        if re.search(r"\bnamed\s*$", namer):
            continue
        return namer, m.group("prep").lower(), m.group("rest").strip()
    m = re.search(r"\bThe name [^,.;]{1,60}, (?P<prep>after|for) (?P<rest>.*)", t, re.S)
    if m:
        return "", m.group("prep"), m.group("rest").strip()
    if re.search(r"\b(?:so )?called descriptively\b|\bdescriptive name\b|\bname is descriptive\b|\bnamed descriptively\b", t, re.I):
        return "", "because", "descriptive"
    m = HON2.search(t)
    if m:
        return "", m.group("prep").lower(), m.group("rest").strip()
    m = re.search(r"(?:^|[.;]\s)(?:After|Efter)\s(?P<rest>[A-ZÀ-Ýa-z].*)", t, re.S)
    if m:
        return "", "after", m.group("rest").strip()
    if MEANING.search(t):
        return "", "because", "its meaning"
    for rx, prep in FR_ES:
        m = rx.search(t)
        if m:
            rest = m.group("rest").strip()
            if prep == "for-person":
                return "", "for-person", rest
            if prep == "for-ship":
                return "", "for", "the ship " + rest
            return "", prep, rest
    return None
TITLE = (r"(?:Lt\.?|Lieut\.?|Lieutenant|Capt\.?|Captain|Cdr\.?|Comdr\.?|Commander|Cmdr\.?|Dr\.?|Doctor|Prof\.?|Professor|Sir|Lord|Lady|Mr\.?|Mrs\.?|Miss|Ms\.?|Admiral|Adm\.?|"
         r"Rear Admiral|Vice Admiral|R\. ?Adm\.?|V\. ?Adm\.?|General|Gen\.?|Colonel|Col\.?|Lt\. ?Col\.?|Lt\. ?Cdr\.?|Lt\. ?Comdr\.?|Major|Maj\.?|Sgt\.?|Sergeant|Cpl\.?|Corporal|Ensign|Ens\.?|"
         r"Chief|CPO|PO\.?|Petty Officer|Flt\.? ?Lt\.?|Flight Lieutenant|Flt\.? ?Sgt\.?|Sqn\.? ?Ldr\.?|Squadron Leader|Wing Commander|Wg\.? ?Cdr\.?|Air Commodore|Group Captain|"
         r"King|Queen|Prince|Princess|Crown Prince|Emperor|Empress|Duke|Duchess|Earl|Count|Countess|Baron|Baroness|Viscount|Marquis|Marquess|President|Senator|Sen\.?|Congressman|Hon\.?|Rev\.?|Reverend|Father|Fr\.?|Bishop|Archbishop|Pope|Saint|St\.?|Dame|Mme\.?|Madame|Monsieur|M\.|Herr|Frau|Kapitän|Kapitan|Konsul|Consul|Governor|Gov\.?|Judge|Justice|Senhor|Señor|Don|Doña|Lt\. \(j\.g\.\)|Lt\.?\s?\(jg\)|Midshipman|Surgeon|Engineer|Boatswain|AD[1-3]|AT[1-3]|AM[1-3]|AE[1-3]|PH[1-3]|RM[1-3]|CE[1-3]|ET[1-3]|EM[1-3]|UT[1-3]|SW[1-3]|BU[1-3]|CD[1-3]|AG[1-3]|HM[1-3]|Cmdr|Cdre\.?|Commodore|Warrant Officer|W\.?O\.?)")
ASSOC = re.compile(r"\b(?:in association with|by association|association with|associated with|from (?:the )?(?:nearby|adjacent|neighbouring|neighboring)|after (?:the )?(?:nearby|adjacent|neighbouring|neighboring)|takes? (?:its|the) name from|named from|derived from|from its proximity|same name|following the theme|theme|grouped in this area|in this area|group of names|in the group|series of names)\b", re.I)
WOMAN = re.compile(r"\b(?:Mrs\.?|Miss|Ms\.?|Lady|Dame|Queen|Princess|Empress|Duchess|Countess|Baroness|Mme\.?|Madame|Mademoiselle|Mlle\.?|Frau|Fräulein|Señora|Senhora|Doña|wife|widow|daughter|daughters|sister|sisters|mother|grandmother|granddaughter|niece|aunt|fiancée|fiancee|girlfriend|bride|woman|women|female|she|her|heroine|née|nee)\b", re.I)
FIRSTNAME_WOMEN = set("""Mary Margaret Elizabeth Anne Ann Anna Jane Joan Joanna Jean Janet Judith Judy Ruth Helen Helene Hélène Sarah Sara Susan Susanne Suzanne
Barbara Patricia Linda Carol Caroline Catherine Katherine Kathleen Kate Karen Nancy Betty Dorothy Doris Edith Ellen Eleanor Elinor Emily Emma Florence Frances
Grace Hazel Irene Jacqueline Josephine Julia Julie June Laura Lucy Louise Lois Marie Maria Marion Martha Mildred Olga Phyllis Rose Rosemary Shirley Sylvia Valerie
Victoria Virginia Wendy Gillian Diana Deborah Debra Pamela Sandra Sharon Sheila Alice Agnes Amelia Christine Christina Claire Clara Cynthia Denise Diane Elaine
Eva Evelyn Gladys Gwen Hannah Heather Ingrid Ingeborg Isabel Isabella Jennifer Jessica Joyce Kirsten Lisa Lorna Lynn Maud Maude Mabel Marjorie Michelle Monica
Muriel Nora Norma Patricia Paula Pauline Penelope Rachel Rebecca Rita Sally Sonja Sonia Stella Teresa Theresa Tove Ulla Vera Violet Wilhelmina Yvonne Zoe Astrid
Ragnhild Märtha Martha Sigrid Solveig Gunhild Birgit Brigitte Charlotte Dagmar Hedwig Gertrud Gertrude Liv Ida Inger Kari Marit Randi Aud Bodil Signe Thora""".split())
ROLE = (r"(?:[\w-]+ specialist|specialist|geologist|geophysicist|glaciologist|biologist|zoologist|botanist|ornithologist|oceanographer|meteorologist|physicist|chemist|scientist|surveyor|cartographer|"
        r"geodesist|seismologist|ionospheric physicist|aurora(?:l)? (?:physicist|observer)|photographer|photographer's mate|cook|radioman|radio operator|operator|mechanic|electrician|"
        r"carpenter|engineer|technician|pilot|co-?pilot|navigator|aviation \w+|aircrewman|crewman|seaman|sailor|whaler|sealer|explorer|leader|commander|officer|doctor|physician|surgeon|"
        r"medical officer|dog handler|handyman|builder|tractor driver|driver|diesel mechanic|weather observer|observer|assistant|historian|journalist|writer|author|artist|painter|"
        r"poet|composer|climber|mountaineer|skier|chairman|director|president|secretary|minister|ambassador|governor|senator|congressman|representative|admiral|general|captain|"
        r"lieutenant|ensign|sergeant|corporal|patron|benefactor|sponsor|donor|member|manager|administrator|nurse|teacher|professor|student|helicopter pilot|shipowner|ship owner|"
        r"industrialist|businessman|banker|merchant|statesman|politician|scholar|philosopher|mathematician|astronomer|geographer|engineman|machinist|boatswain|steward|stoker|"
        r"fireman|mate|petty officer|chief petty officer|storekeeper|yeoman|hospital corpsman|corpsman|radar operator|aerographer|aerologist|electronics technician|construction \w+|"
        r"equipment operator|utilitiesman|steelworker|builder|cartographic technician|station leader|base leader|officer-in-charge|scientific leader|field assistant|general assistant)")
NAT = r"(?:fellow|colleague|American|British|English|Scottish|Welsh|Irish|Australian|New Zealand|Norwegian|Swedish|Danish|Finnish|German|French|Belgian|Dutch|Swiss|Austrian|Italian|Spanish|Portuguese|Russian|Soviet|Polish|Czech|Bulgarian|Chilean|Argentine|Argentinian|Japanese|Chinese|Canadian|South African|Indian|Brazilian|Uruguayan|Ecuadorian|Peruvian|Korean|Ukrainian|Hungarian|Romanian|Greek|Estonian|Latvian|Lithuanian|Icelandic|USARP|USAP|USGS|USN|ANARE|FIDS|BAS|NZARP|Antarctic|U\.S\.|US|UK|NZ|ex-|former|noted|eminent|famous|distinguished|Dutch|polar|well-known|pioneer|chief|senior|principal|deputy|assistant)"

PRE = (r"(?:the late |late |the Honou?rable |Honou?rable |The Rt\.? Hon\.? |Rt\.? Hon\.? |Tech\.? Sgt\.? |Asst\.? |Enseigne de Vaisseau |"
       r"Senior Lieutenant |Lieutenant-Colonel |Squadron-Leader |Flight-Lieutenant |Wing-Commander |Airman \d\w* Class |Lt\.? \(jg\) ||Instr\.? Cmdr\.? |Surg\.? Capt\.? |Surg\.? Lt\.? |Specialist \d\w*(?: Class)? |Utilities ?Man \d\w* Class |"
       r"(?:Equipment|Construction|Aviation|Electronics|Engineman|Utilities)\w* (?:Operator|Technician|Mechanic|Electrician|Man|Mate)? ?\d\w* Class |"
       r"(?:capitán|capitan|teniente|sargento|cabo|general|almirante|comandante|contraalmirante|vicealmirante|suboficial|marinero|piloto|ingeniero|"
       r"doctor|profesor|coronel|mayor|subteniente|alférez|guardiamarina|cirujano|médico|herrero|carpintero|mecánico|fogonero|cocinero)"
       r"(?: de (?:corbeta|fragata|navío|navio|brigada(?: aérea)?|aviación|ejército|mar))?(?: \d[ºo°]?)?(?: (?:ingeniero|mecánico de aviación|de aviación|\(\w+\.?\)))? |"
       r"Kapt\.? |Kaptein |Tte\.? \d?°? |Teniente |Capitán |Almte\.? |Herzog |Graf |Freiherr |Messrs\.? |Sra\.? |Sr\.? |Ing\.? |Dipl\.? |Mag\.? )")
# a personal name: optional prefix and title, one to three given names or initials, particles, a surname
NAME = (r"(?:" + PRE + r")*(?:" + TITLE + r"\s)*"
        r"[A-ZÀ-Ý][a-zà-ÿ'’]+(?:-[A-ZÀ-Ý][a-zà-ÿ'’]+)*"
        r"(?:\s(?:(?:[A-Z]\.){1,3}|[A-Z]\.?|\"[^\"]{1,20}\"|\([A-Za-z\" ]{1,20}\)|de|von|van|der|den|du|la|le|da|di|del|dos|d'|Mac|Mc|[A-ZÀ-Ý][a-zà-ÿ'’]+(?:-[A-ZÀ-Ý][a-zà-ÿ'’]+)*|[A-Z][a-z]*[A-Z][a-z]+)){1,5}"
        r"(?:,?\s(?:Jr|Sr|II|III|IV)\.?)?")
INITS = r"(?:" + PRE + r")*(?:" + TITLE + r"\s)*(?:[A-ZÀ-Ý]\.\s?){1,3}\s?(?:de |von |van |du |le |la |Mac|Mc|O')?[A-ZÀ-Ý][\w'’-]+"
INITS2 = r"(?:[A-Z]{1,3}\s){1,2}[A-Z][a-z][\w'’-]+(?=[,\s.(])"
NOTPERSON = (r"\b(?:River|Pass|Fjord|Fiord|Firth|Province|State|County|City|Town|Village|Republic|Kingdom|Empire|University|College|Institute|Institution|Society|Academy|"
             r"Museum|Foundation|Fund|Company|Corporation|Survey|Service|Office|Agency|Committee|Commission|Council|Club|School|Observatory|Laboratory|Association|"
             r"Department|Ministry|Bureau|Program|Programme|Project|Operation|Expedition|Navy|Army|Force|Guard|Squadron|Trust|League|Union|Inc|Ltd|GmbH|Co|Brothers|"
             r"Mountains|Alps|Andes|Himalaya|Sea|Ocean|Gulf|Lake|Strait|Channel|Desert|Forest|Park|Street|Road|Square|Castle|Cathedral|Church|Abbey|Palace|"
             r"Theatre|Hall|House|Bridge|Tower|Gate|Harbour|Port)\b")
GEOW = (r"\b(?:Mountain|Planina|Island|Islands|Glacier|Mount|Mountains|Cape|Bay|Station|Land|Sea|Coast|Peninsula|Point|Peak|Range|Inlet|Sound|Strait|"
        r"Ice Shelf|Nunatak|Nunataks|Valley|Ridge|Plateau|Harbour|Harbor|Lake|Rock|Rocks|Hill|Hills|Base|Trough|Bank|Basin|Névé|Neve|Heights)\b")
VESSEL = (r"(?:ship|ships|vessel|vessels|barque|barques|steamship|steamer|schooner|brig|brigantine|sloop|icebreaker|ice-breaker|whale-?catcher|"
          r"whale catcher|whalecatcher|catcher|floating factory|factory ship|factory|sealer|sealing vessel|tugboat|tug|survey boat|boat|launch|yacht|tanker|trawler|"
          r"frigate|corvette|cruiser|destroyer|submarine|seaplane tender|tender|flagship|transport|patrol ship|buque|navire|whaler)")
VEHICLE = (r"(?:aircraft|airplane|aeroplane|monoplane|biplane|seaplane|flying boat|plane|helicopter|airship|balloon|satellite|satellites|spacecraft|"
           r"space ?ship|rocket|tractor|tractors|Sno-?[Cc]ats?|motor toboggan|motor sledges?|vehicle|vehicles|Weasel|Otter|Beaver)")
ANIMAL = (r"(?:penguin|penguins|seal|seals|skua|skuas|petrel|petrels|tern|terns|whale|whales|cetacean|bird|birds|krill|fish|lichen|lichens|moss|mosses|algae|"
          r"fossil|fossils|plant|plants|grass|tree|trees|flower|flowers|animal|animals|dog|dogs|dog-teams?|dog teams?|husky|huskies|pony|ponies|cormorant|"
          r"cormorants|shag|shags|albatross|sheathbill|prion|sea lion|beetle|midge|mite|insect|insects|shells|wildlife|vegetation|rookery|rookeries|colony)")
PLACEK = (r"(?:town|towns|city|village|villages|settlement|hamlet|municipality|region|historical region|province|county|district|parish|river|mountain|"
          r"mountains|peak|lake|island|islands|peninsula|valley|cape|bay|fortress|castle|monastery|locality|seaport|port|plain|pass|gorge|cave|state|"
          r"country|capital|homeland|neighbourhood|neighborhood|suburb|quarter|street|park|nation|republic|kingdom|harbour|harbor|sound|fjord|"
          r"firth|strait|sea|gulf|massif|range|hill|hills|volcano|desert|forest|estate|farm|home ?town|birthplace|resort|spa|monument|cathedral|church|"
          r"ancient city|ancient town|Thracian|Roman|medieval|old capital|historic|historical)")
INSTK = (r"(?:university|college|institute|institution|society|academy|museum|foundation|fund|company|corporation|firm|survey|service|office|agency|"
         r"administration|committee|commission|council|club|school|observatory|laboratory|association|federation|department|ministry|bureau|"
         r"program|programme|project|operation|expedition|station|base|navy|army|air force|coast guard|squadron|trust|league|union|party|unit|"
         r"corps|battalion|regiment|group|team|newspaper|magazine|publisher|organi[sz]ation|brewery|railway|bank|hospital|parliament|government|"
         r"Inc\.?|Ltd\.?|GmbH|A/S|& Co\.?)")
WORDK = (r"(?:word|words|term|expression|code ?word|call ?sign|nickname|letter|initials|phrase|motto|slogan|abbreviation|acronym|composition|symphony|"
         r"song|opera|poem|novel|book|play|painting|film|ballet|constellation|star|stars|planet|comet|asteroid|satellites? of|moon of|projection|"
         r"map projection|theory|equation|method|technique|process|element|mineral|chemical|discipline|science|branch of|unit of|"
         r"dance|instrument|musical|language|alphabet|Greek alphabet|letter of)")
MYTHK = (r"(?:god|goddess|gods|deity|deities|nymph|nymphs|titan|giant|muse|muses|hero|heroine|character|characters|figure|figures|creature|demon|"
         r"spirit|dragon|monster|mythological|mythical|legendary|fictional|apostle|saint|biblical|angel)")
EVENTK = (r"(?:International Geophysical Year|IGY|International Polar Year|Christmas|Easter|New Year|Midwinter|Thanksgiving|day|anniversary|centenary|"
          r"centennial|bicentenary|bicentennial|tercentenary|jubilee|year|coronation|battle|war|victory|landing|discovery|first ascent|first landing|"
          r"first flight|first crossing|first sighting|conference|congress|treaty|olympics|olympic games|games|expedition's|occasion|event)")
DESCK = (r"(?:its|their|the shape|the form|the colou?r|the appearance|the position|the location|the shape of|the presence|the abundance|"
         r"the large number|the many|the numerous|the steep|the smooth|the sharp|the resemblance|a resemblance|resemblance|similarity|the similarity|"
         r"the outline|the profile|the view|the sound|the noise|the smell|the difficult|the difficulty|the danger|the hazard|the fact|the conspicuous|"
         r"the descriptive|descriptive|the pattern|the way|the dark|the white|the black|the red|the brown|the yellow|the green|the blue|the grey|"
         r"the gray|the colours?|the colors?|the bands|the profusion|the striking|the prominent|the isolated|the lonely|the high|the low|the "
         r"surrounding|the nearby ice|the ice|the snow|the wind|the winds|the weather|the storm|the fog|the cold|the warm|the many|the feature's|"
         r"the [\w-]+-like|the triangular|the conical|the rounded|the flat|the pointed|the jagged|the twin|the pair|the three|the four|the sharp|"
         r"being|lying|it is|it lies|it was the|which|where|when|while|having|as it|as they|so|how)")
APPOS = [("ship", r"(?:[\w'.-]+ ){0,5}" + VESSEL + r"\b(?!'s)"),
         ("vehicle", r"(?:[\w'.-]+ ){0,4}" + VEHICLE + r"\b"),
         ("myth", r"(?:[\w'.-]+ ){0,4}" + MYTHK + r"\b"),
         ("word", r"(?:[\w'.-]+ ){0,4}" + WORDK + r"\b"),
         ("place", r"(?:[\w'.-]+ ){0,3}" + PLACEK + r"\b"),
         ("institution", r"(?:[\w'.-]+ ){0,3}" + INSTK + r"\b"),
         ("person", r"(?:(?:then|later|now|formerly|the|a|an|one of the|his|her|who|was|is|chief|senior|first|former|leading|noted|well-known|famous|eminent|distinguished|pioneer|\w+ish|\w+ian|\w+an|\w+ese|\w+ic)\s)*(?:[\w'.()-]+ ){0,4}" + ROLE + r"\b"),
         ("person", r"(?:who|whose|he|she|husband|wife|son|daughter|father|mother|brother|sister|widow|born|b\.|d\.|died|deceased|\(?\d{4})")]


def kind(prep, rest, namer="", lang="en"):
    """Kind of honour, read from the start of the honoree clause (the text after 'named for/after')."""
    head = rest[:140]
    m = re.search(r"\b(?:grouped|names) in (?:this|the) (?:area|region|vicinity)[^.;]{0,40}?,?\s(?:named |were named |was named )?(?:after|for)\s(?P<r>.*)", rest[:300])
    if m:
        return kind("for", m.group("r"))
    if prep in ("because", "descriptively"):
        return "descriptive"
    if prep == "for-person":
        return "person"
    if prep in ("in association with", "by association"):
        return "association"
    if ASSOC.search(head[:60]) and not re.search(r",\s*named (?:after|for)\b", rest[:260]):
        return "association"
    if re.match(r"(?:the |a |an |his |their |its |her )?(?:[\w'.-]+ ){0,5}ship'?s'? (?:surgeon|doctor|carpenter|cook|captain|master|mate|engineer|boatswain|officer|steward|crew|company|surgeon)", head, re.I):
        return "person"
    if re.match(r"(?:the |a |an |his |their |its |her )?(?:[\w'.-]+ ){0,5}" + VESSEL + r"\b(?!'s)", head, re.I) and not re.match(r"(?:" + PRE + r")*" + TITLE + r"\s", head) and not re.match(NAME + r"\s(?:on|of|in|aboard|with)\s", head) and not re.match(r"(?:[\w'.-]+ ){0,4}(?:captain|master|commander|owner|owners|mate|crew|surgeon)\b", head, re.I):
        return "ship"
    if re.match(r"(?:the )?(?:US |U\.S\. |British |Norwegian |German |French |Soviet |Russian |Argentine |Chilean |Australian |Japanese )?(?:USS|USNS|USCGC|USCG|HMS|HMAS|HMNZS|HMCS|RRS|MV|M/V|M\.V\.|R/V|RV|R\.V\.|SS|S\.S\.|FS|F\.S\.|ARA|AP|RSV|NB|M/S|MS|D/S|DS|S/S|T/S|ORP|BIC|BAP|BIO|SA|Polarstern)\s", head):
        return "ship"
    if re.match(r"(?:the |a |an |his |their )?(?:[\w'.-]+ ){0,4}" + VEHICLE + r"\b", head, re.I) and not re.match(r"(?:[\w'.-]+ ){0,4}(?:pilot|pilots|driver|drivers|mechanic|mechanics|crew|crewman|commander|navigator|designer|designers|maker|makers|manufacturer)\b", head, re.I):
        return "vehicle"
    if re.match(r"(?:the |a |an )?(?:[\w'-]+ ){0,4}(?:King|Queen|Khan|Tsar|Tsaritsa|Emperor|Empress|ruler|king|queen|khan|tsar|tsaritsa|boyar|voivode|prince|princess|chieftain|patriarch|metropolitan|bishop|archbishop|saint|St\.|scholar|linguist|enlightener|revolutionary|educator|writer|poet|composer|artist|painter|singer|sculptor|actor|actress|scientist|historian|philosopher|physician|politician|statesman|hero|leader|merchant|benefactor|founder|missionary|monk|abbot)\b,?\s(?:of [\w ]+\s)?(?:" + NAME + "|" + INITS + "|[A-ZÀ-Ý][a-zà-ÿ]+)", head):
        return "person"
    if re.match(r"(?:the |a )?(?:" + PRE + r")*" + TITLE + r"\s", head) and not re.match(r"(?:the )?(?:King|Queen|Prince|Princess|Crown Prince) (?:of\b|Maud|George V|George VI|Olav Coast|Harald Coast|Elizabeth Land|Astrid Coast|Ragnhild Coast|Martha Coast)", head):
        return "person"
    if re.match(r"(?:the |a |an )?(?:" + NAT + r"\s)*(?:[\w'-]+\s)?" + ROLE + r",?\s(?:and\s\w+\s)?(?:the late\s)?(?:" + NAME + "|" + INITS + ")", head, re.I):
        return "person"
    if re.match(r"(?:the |a |an )?(?:[A-Z][\w-]+ )(?:brothers|family|sisters)\b", head):
        return "person"
    if re.match(r"(?:the |a |an )?(?:then |late |former |present |reigning |then reigning )*(?:sovereign|monarch|king|queen|prince|princess|emperor|empress|pope|wife|daughter|son|widow|mother|father|brother|sister|niece|nephew|grandson|granddaughter|husband|fianc[ée]e|family|brothers|sisters|daughters|sons|children)\b", head, re.I):
        return "person"
    if re.match(r"(?:his|her|their|[A-Z][\w-]+'s) (?:wife|daughter|son|sister|brother|mother|father|widow|niece|nephew|fianc[ée]e|grandson|granddaughter|family|daughters|sons|children|mother's|father's|wife's)", head):
        return "person"
    if re.match(r"(?:the |an |a )?(?:earlier |early |old |local |former |long |continued )?(?:usage|use|names? used|name given) (?:of|by)\b", head, re.I):
        return "other"
    seg = re.split(r"[,(;]|\s(?:of|who|whose|at|from|with|in)\s", head, 1)[0]
    if (re.match(NAME + r"\s?(?:[.,(;:]|\sof\b|\sand\s[A-Z]|\swho\b|\swhose\b|\s[a-z]|$)", head) or re.match(INITS, head) or re.match(INITS2, head)) and not re.search(GEOW + "|" + NOTPERSON, seg):
        return "person"
    if re.match(DESCK + r"\b", head, re.I):
        return "descriptive"
    if re.match(r"(?:the |a |an )?(?:[\w-]+ ){0,3}" + MYTHK + r"\b", head, re.I):
        return "myth"
    if re.match(r"(?:the |a |an )?(?:[\w-]+ ){0,2}" + ANIMAL + r"\b", head, re.I):
        return "nature"
    if re.match(r"(?:the |a |an )?(?:[\w-]+ ){0,2}" + PLACEK + r"\b", head, re.I):
        if re.search(r"(?:\bq\.v\.|nearby|adjacent|neighbou?ring|^the (?:island|cape|glacier|peak|mountain|bay|point|ridge|nunatak|valley|lake|plateau|range)\b(?![^,.]{0,40}\b(?:in|of|near)\s[A-Z]))", head[:80], re.I):
            return "association"
        return "place"
    if re.match(r"(?:the |a |an )?(?:[A-Z][\w'&.-]+ ){0,7}" + INSTK + r"\b", head) or re.match(r"(?:the |a |an )?(?:[\w-]+ ){0,3}" + INSTK + r"\b", head, re.I):
        return "institution"
    if re.match(r"(?:the |a |an )?(?:[\w-]+ ){0,3}" + EVENTK + r"\b", head, re.I):
        return "event"
    if re.match(r"(?:the |a |an )?(?:[\w-]+ ){0,3}" + WORDK + r"\b", head, re.I):
        return "word"
    # Name, appositive: "Poseidon, god of the sea"; "the Charrua, one of the ships"; "Oamaru, Otago, New Zealand, the port"
    m = re.match(r"(?:the |The )?\"?([A-ZÀ-Ý][\w'’.-]*(?:\s(?:de |De |von |van |du |la |le |da |di |del |d')?[A-ZÀ-Ý(\"][\w'’.)\"-]*){0,5})\"?\s?(?:\([^)]{0,60}\)\s?)?,\s(.{0,90})", head)
    if m:
        ap = m.group(2)
        for kk, rx in APPOS:
            if re.match(r"(?:then |later |now |formerly |the |a |an |one of the |one of |which |his |her |its |their )*" + rx, ap, re.I):
                if kk == "place" and re.match(r"(?:the |a )?(?:island|cape|glacier|peak|mountain|bay|point)\b", ap, re.I) and re.search(r"q\.v\.|nearby|adjacent", ap):
                    return "association"
                return kk
    if (re.match(NAME + r"\s?(?:[.,(;:]|\sof\b|\sand\s[A-Z]|\swho\b|$)", head) or re.match(INITS, head) or re.match(INITS2, head)) and not re.search(GEOW, head[:45]):
        return "person"
    if re.match(r"(?:the |a )?(?:[\w-]+ ){0,3}(?:people|men|women|crew|crews|personnel|members|scientists|cartographers|surveyors|whalers|sealers|explorers|pioneers|airmen|pilots|staff|volunteers|workers|builders|wintering party|winterers|participants)\b", head, re.I):
        return "group"
    return "other"


def years_in(s):
    out = []
    s2 = re.sub(r"\((?:b\.\s?|born\s)?(?:c\.\s?)?\d{3,4}\s?(?:-|–|to)\s?\d{2,4}\)|\(b\.\s?\d{4}\)|\(born \d{4}\)|\(d\.\s?\d{4}\)|\bb\.\s?\d{4}|\bborn (?:in )?\d{4}|\bd\.\s?\d{4}|\bdied (?:in )?\d{4}|\(\d{4}-\d{4}\)", " ", s)
    for m in re.finditer(r"(?<![\d/.-])(1[789]\d\d|20[012]\d)(?![\d])", s2):
        out.append(int(m.group(1)))
    return out

PLACEWORDS = re.compile(r"\b(?:Ross|Palmer|Wilkes|Byrd|Ellsworth|Mawson|Scott|Bruce|Larsen|Weddell|Enderby|Kemp|Shackleton|Smith|Cook|Amundsen|Charcot|Filchner|Ronne|Christensen|Gerlache|Bellingshausen|Lazarev|Drygalski|Biscoe|Foster|Powell|Mac\.Robertson|MacRobertson|Victoria|Marie Byrd|Coats|Graham|Alexander|Adelaide|Oates|George V|King George|Dronning Maud|Queen Maud|Queen Mary|Princess Elizabeth|Wilhelm II|Kaiser Wilhelm II|Davis|Casey|Wilkins|McMurdo|South Pole|Halley|Rothera|Vostok|Mirny|Molodezhnaya|Showa|Syowa|Dumont d'Urville|Neumayer|Belgrano|Esperanza|Marambio|O'Higgins|Arctowski|Palmer Station|Siple|Plateau|Brunt|Riiser-Larsen|Fimbul|Amery|Lambert|Beardmore|Nimrod|Axel Heiberg|Liv|Horlick|Wright|Taylor|Ferrar|Koettlitz)\s(?:Island|Islands|Sea|Ice Shelf|Land|Station|Base|Mountains|Range|Glacier|Plateau|Strait|Coast|Peninsula|Bay|Archipelago|Sound|Dependency|Valley|Hills|Ice Stream|Ice Piedmont|Sea)\b")
SENT_SPLIT = re.compile(r"(?<=[a-z0-9\)\]])\.\s+(?=[A-Z])")


def namer_of(text):
    """Nation of whoever named the feature, from the narrative. Returns (nation, matched text, namer context)."""
    t = WS(text)
    for sent in SENT_SPLIT.split(t):
        m = re.search(r"\b(?:re)?named\b", sent, re.I)
        if not m:
            continue
        after = sent[m.end():]
        stop = re.search(r"\b(?:for|after|in honou?r of|in memory of|because|in association with|descriptively|to commemorate)\b", after, re.I)
        clause = after[:stop.start()] if stop else after[:160]
        clause = PLACEWORDS.sub(" ", clause)
        if re.search(r"\bby\b", clause, re.I) or re.search(r"\b(?:US-?ACAN|UK-?APC|NZ-?APC|APC|ANCA|NZGB|JARE)\b", clause):
            nat, hit = namer_nation(clause)
            if nat:
                return nat, hit, clause.strip()
        pre = PLACEWORDS.sub(" ", sent[:m.start()])
        k = [x.end() for x in re.finditer(r"\bby\b|\bunder\b", pre)]
        if k and re.search(r"(?:who|and|which|,|they|he)\s*(?:was |were |had |subsequently |later |also )?$", pre.strip() + " ", re.I) is not None:
            seg = pre[k[0] - 3:]
            nat, hit = namer_nation(seg)
            if nat:
                return nat, hit, seg.strip()[:160]
    return None, None, None


def discoverer_of(text):
    """Nation of the first expedition, ship or leader said to have discovered, charted, sighted or named the feature:
    used only when no naming statement names anyone."""
    t = PLACEWORDS.sub(" ", WS(text))
    m = re.search(r"\b(?:named|called) (?:for|after) ([^;]{0,90}?),? who (?:first )?(?:discovered|charted|sighted|named)\b", t)
    if m:
        nat, hit = namer_nation(m.group(1))
        if nat:
            return nat, hit
    for m in re.finditer(r"\b(?:[Dd]iscovered|[Cc]harted|[Ss]ighted|[Ff]irst seen|[Ss]een|[Mm]apped|[Ss]urveyed|[Pp]hotographed|[Nn]amed|[Cc]alled|[Rr]oughly charted|[Dd]elineated|[Pp]lotted)\b[^.;]{0,90}?\bby\b((?:[^.;]|\.(?! [A-Z][a-z]+ [a-z])){0,80})", t):
        nat, hit = namer_nation(m.group(1))
        if nat:
            return nat, hit
    return None, None


import unicodedata
def fold(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]+", " ", s).strip()



# generic words in the gazetteer languages, removed to compare the specific part of names across gazetteers
GEN = set("""mount mountain mountains mt mts monte montes mont monts cerro cerros cordon cordillera sierra gora gory khrebet hrebet berg berge
bergen fjell fjella fjellet fjelli peak peaks pico picos pic pik pik pyramid pyramide island islands isla islas islote islotes ile iles ilot ilots isle
ostrov ostrova insel inseln oya oyane oyna holm holmane glacier glaciers glaciar glaciares lednik gletscher bre breen isen cape cabo cap mys kapp
point punta pointe pta tangen nes neset bay bahia baie bukta bukt buhta zaliv bucht caleta cove ensenada inlet fjord fjorden strait estrecho detroit
proliv sound canal channel paso passage pass collado col pereval sedlovina ridge cresta crete greben ryggen kamm range cadena chaine monti
massif macizo massiv nunatak nunataks nunatakk rock rocks roca rocas rocher rochers skala skaly skjer skjera skjeret hill hills colina colinas
cerrito morro kholm kholmy haug haugen hoyda point head heights valley valle vallee dolina dalen dal lake lago lac ozero vatnet vatn tjorna
coast costa cote bereg kysten land tierra terre zemlya landet plateau meseta plato platoet ice shelf shelf barrera lednik shelfovyy isen
peninsula peninsule poluostrov halvoya halbinsel spur espolon escarpment bluff bluffs cliff cliffs acantilado falaise kapp tind tinden nuten
knausen kollen toppen the de la le les el los las del des du of di da do der den das y et and saint san santa st""".split())


def specific(name):
    t = [w for w in fold(name).split() if w not in GEN and len(w) > 1]
    # Norwegian and German compounds: strip a generic suffix
    out = []
    for w in t:
        w2 = re.sub(r"(fjella|fjellet|breen|isen|nuten|toppen|kammen|ryggen|dalen|skjera|skjeret|holmane|oyane|oya|tind|tinden|knausen|haugen|"
                    r"nabben|hamaren|kletten|bukta|vika|neset|tangen|gletscher|insel|inseln|berge|berg|spitze|kopf|halbinsel|bucht)$", "", w)
        out.append(w2 if len(w2) >= 3 else w)
    return out


