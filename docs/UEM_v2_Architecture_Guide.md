# UEM v2 - Mimari KÄ±lavuz ve KÃ¶prÃ¼ DokÃ¼manÄ±

**Proje:** Unknown Evola Mind (UEM)  
**Versiyon:** 2.0 BaÅŸlangÄ±Ã§ Rehberi  
**Tarih:** 2025-12-07  
**AmaÃ§:** Yeni projeye sÄ±fÄ±rdan baÅŸlarken referans + sohbetler arasÄ± hafÄ±za kÃ¶prÃ¼sÃ¼

---

## 1. NEDEN SIFIRDAN BAÅžLIYORUZ?

### 1.1 Eski Projenin Durumu (v1)

| Metrik | DeÄŸer | Problem |
|--------|-------|---------|
| Dizin sayÄ±sÄ± | 100 | YÃ¶netilemez |
| Dosya sayÄ±sÄ± | 353 | Ã‡ok fazla |
| Test sayÄ±sÄ± | 641+ | Ä°yi ama neyi test ettiÄŸi belirsiz |
| .bak dosyalarÄ± | 10+ | Teknik borÃ§ |
| .zip dosyalarÄ± | 6 | Patch'ler birikmiÅŸ |

### 1.2 Tespit Edilen Sorunlar

**Duplikasyonlar:**
```
empathy/                    â†’ 1 dosya (empathy_orchestrator.py)
metamind/social/            â†’ 7 alt modÃ¼l (aynÄ± iÅŸ!)
  â”œâ”€â”€ cognitive_empathy/
  â”œâ”€â”€ emotional_empathy/
  â”œâ”€â”€ social_simulation/
  â””â”€â”€ ...

cognition/meta_cognition/   â†’ var
metamind/                   â†’ var  
consciousness/              â†’ var
(Ã¼Ã§Ã¼ de "Ã¼st-biliÅŸ" yapÄ±yor?)
```

**Belirsizlikler:**
- Hangi dosyalar aktif kullanÄ±lÄ±yor?
- Hangi modÃ¼ller birbiriyle Ã§akÄ±ÅŸÄ±yor?
- 353 dosyadan kaÃ§Ä± gerÃ§ekten Ã§alÄ±ÅŸÄ±yor?

**SonuÃ§:** Refactor yerine temiz baÅŸlangÄ±Ã§ daha mantÄ±klÄ±.

---

## 2. Ã–ÄžRENÄ°LEN DERSLER

### 2.1 Mimari Hatalar

| # | Hata | Sonucu | Ã‡Ã¶zÃ¼m |
|---|------|--------|-------|
| 1 | DÃ¼z modÃ¼l yapÄ±sÄ± | 11+ modÃ¼l aynÄ± seviyede | HiyerarÅŸik yapÄ± kullan |
| 2 | Erken optimizasyon | Her ÅŸey iÃ§in alt modÃ¼l | Ã–nce Ã§alÄ±ÅŸsÄ±n, sonra bÃ¶l |
| 3 | Belirsiz sorumluluk | empathy vs metamind/social | Tek sorumluluk prensibi |
| 4 | StateVector sabit boyut | 3Dâ†’16Dâ†’27D her seferinde kÄ±rÄ±ldÄ± | Core + Extensions pattern |
| 5 | DokÃ¼mantasyon-kod uyumsuzluÄŸu | Brief'ler gerÃ§eÄŸi yansÄ±tmÄ±yor | Kod Ã¶nce, dokÃ¼man sonra |
| 6 | Monitoring sonradan | Ä°zleme yok, debug zor | Monitoring ilk gÃ¼nden |

### 2.2 Kavramsal TanÄ±mlar

**Cognition vs Metacognition:**
```
Cognition     = DÃ¼ÅŸÃ¼nme           â†’ "2+2 kaÃ§ eder?"
Metacognition = DÃ¼ÅŸÃ¼nme hakkÄ±nda  â†’ "DoÄŸru dÃ¼ÅŸÃ¼nÃ¼yor muyum?"
```

**Empathy vs Sympathy vs Trust:**
```
EMPATHY  = BaÅŸkasÄ±nÄ± ANLAMAK (biliÅŸsel)     â†’ "O ne hissediyor?"
SYMPATHY = AnladÄ±ktan sonra HÄ°SSETMEK       â†’ "Bu bende ne uyandÄ±rÄ±yor?"
TRUST    = GeÃ§miÅŸe gÃ¶re GÃœVENMEK            â†’ "Ona gÃ¼venebilir miyim?"
```

**Consciousness (Global Workspace):**
```
TÃ¼m modÃ¼ller paralel Ã§alÄ±ÅŸÄ±r:
- Perception: "Tehlike gÃ¶rÃ¼yorum"
- Memory: "Daha Ã¶nce de olmuÅŸtu"
- Emotion: "Korku hissediyorum"

CONSCIOUSNESS = Bilgilerin buluÅŸtuÄŸu "sahne"
â†’ Entegre karar: "Tehlike var, kaÃ§malÄ±yÄ±m"
```

**Ontology:**
```
KavramlarÄ±n tanÄ±mÄ± ve iliÅŸkileri:
- "DÃ¼ÅŸman" nedir? â†’ hostile=true, threat=high
- "DÃ¼ÅŸman" neyin tersi? â†’ Ally
- "DÃ¼ÅŸman" neye dÃ¶nÃ¼ÅŸebilir? â†’ Neutral
```

**Event Bus:**
```
ModÃ¼ller arasÄ± iletiÅŸim (Pub/Sub):
- Perception: "THREAT_DETECTED" yayÄ±nla
- Emotion: "THREAT_DETECTED" dinle, tepki ver
- Spagetti import yerine temiz iletiÅŸim
```

### 2.3 Ne Ä°ÅŸe YaradÄ± (v1'den)

- 10-phase cognitive cycle konsepti âœ“
- PostgreSQL logging altyapÄ±sÄ± âœ“
- Scenario-based testing yaklaÅŸÄ±mÄ± âœ“
- PAD emotion modeli (valence, arousal, dominance) âœ“

---

## 3. YENÄ° MÄ°MARÄ° PRENSÄ°PLER

### 3.1 AltÄ±n Kurallar

```
1. YAGNI (You Aren't Gonna Need It)
   â†’ Kullanmayacaksan yazma
   
2. Tek Sorumluluk
   â†’ Bir modÃ¼l bir iÅŸ yapar
   
3. Ã–nce Ã‡alÄ±ÅŸsÄ±n
   â†’ MVP Ã¶nce, optimizasyon sonra
   
4. DÃ¼z > Derin
   â†’ 3 seviye maksimum iÃ§ iÃ§e dizin
   
5. Kod = DokÃ¼man
   â†’ Kod gerÃ§eÄŸi yansÄ±tÄ±r, dokÃ¼man deÄŸil
   
6. Ä°skelet Sabit
   â†’ KlasÃ¶r ekleme YASAK, sadece dosya ekle
   
7. Monitoring Ä°lk GÃ¼nden
   â†’ main.py Ã§alÄ±ÅŸÄ±nca izleyebilmeliyiz
```

### 3.2 ModÃ¼l SayÄ±sÄ± KuralÄ±

```
BaÅŸlangÄ±Ã§:  BoÅŸ __init__.py dosyalarÄ±
BÃ¼yÃ¼me:     Dosya ekle, klasÃ¶r EKLEME
Maksimum:   Ä°skelet sabit (~55 klasÃ¶r)

Her yeni Ã¶zellik iÃ§in sor:
"Hangi mevcut klasÃ¶re eklenir?"
```

### 3.3 Dosya SayÄ±sÄ± KuralÄ±

```
Alt modÃ¼l baÅŸÄ±na:  3-7 dosya ideal
UyarÄ±:             10+ dosya â†’ GÃ¶zden geÃ§ir
Tehlike:           15+ dosya â†’ TasarÄ±m hatasÄ±
```

---

## 4. UEM v2 FÄ°NAL MÄ°MARÄ°

### 4.1 Ãœst Seviye YapÄ± (6 Kategori)

| Kategori | AmaÃ§ | Ä°Ã§erik |
|----------|------|--------|
| `core/` | ðŸ§  Beyin | 6 lob - iÅŸlem katmanÄ± |
| `meta/` | ðŸ”® Ãœst-biliÅŸ | Consciousness, MetaMind, Monitoring |
| `foundation/` | ðŸ—ï¸ Temel | State, Types, Ontology |
| `infra/` | âš™ï¸ AltyapÄ± | Logging, Storage, Config |
| `interface/` | ðŸ–¥ï¸ ArayÃ¼z | Dashboard, API, CLI |
| `engine/` | ðŸ”„ Motor | Cycle, Events, Phases |

### 4.2 Tam AÄŸaÃ§ YapÄ±sÄ±

```
uem_v2/
â”‚
â”œâ”€â”€ core/                               # ðŸ§  BEYIN (6 LOB)
â”‚   â”‚
â”‚   â”œâ”€â”€ perception/                     # ðŸ‘ï¸ LOB 1: ALGI
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ sensory/
â”‚   â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ attention/
â”‚   â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ fusion/
â”‚   â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚   â””â”€â”€ world_model/
â”‚   â”‚       â””â”€â”€ __init__.py
â”‚   â”‚
â”‚   â”œâ”€â”€ cognition/                      # ðŸ¤” LOB 2: BÄ°LÄ°Åž
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ reasoning/
â”‚   â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ evaluation/
â”‚   â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ creativity/
â”‚   â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚   â””â”€â”€ simulation/
â”‚   â”‚       â””â”€â”€ __init__.py
â”‚   â”‚
â”‚   â”œâ”€â”€ memory/                         # ðŸ—„ï¸ LOB 3: BELLEK
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ working/
â”‚   â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ episodic/
â”‚   â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ semantic/
â”‚   â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ emotional/
â”‚   â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚   â””â”€â”€ consolidation/
â”‚   â”‚       â””â”€â”€ __init__.py
â”‚   â”‚
â”‚   â”œâ”€â”€ affect/                         # ðŸ’š LOB 4: DUYGULANIM
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ emotion/
â”‚   â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”‚   â”œâ”€â”€ core/
â”‚   â”‚   â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚   â”‚   â”œâ”€â”€ primitive/
â”‚   â”‚   â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚   â”‚   â”œâ”€â”€ somatic/
â”‚   â”‚   â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚   â”‚   â””â”€â”€ regulation/
â”‚   â”‚   â”‚       â””â”€â”€ __init__.py
â”‚   â”‚   â””â”€â”€ social/
â”‚   â”‚       â”œâ”€â”€ __init__.py
â”‚   â”‚       â”œâ”€â”€ empathy/
â”‚   â”‚       â”‚   â””â”€â”€ __init__.py
â”‚   â”‚       â”œâ”€â”€ sympathy/
â”‚   â”‚       â”‚   â””â”€â”€ __init__.py
â”‚   â”‚       â”œâ”€â”€ trust/
â”‚   â”‚       â”‚   â””â”€â”€ __init__.py
â”‚   â”‚       â””â”€â”€ theory_of_mind/
â”‚   â”‚           â””â”€â”€ __init__.py
â”‚   â”‚
â”‚   â”œâ”€â”€ self/                           # ðŸªž LOB 5: BENLÄ°K
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ identity/
â”‚   â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ values/
â”‚   â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ ethics/
â”‚   â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ narrative/
â”‚   â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚   â””â”€â”€ integrity/
â”‚   â”‚       â””â”€â”€ __init__.py
â”‚   â”‚
â”‚   â””â”€â”€ executive/                      # ðŸŽ¯ LOB 6: YÃ–NETÄ°CÄ°
â”‚       â”œâ”€â”€ __init__.py
â”‚       â”œâ”€â”€ planning/
â”‚       â”‚   â””â”€â”€ __init__.py
â”‚       â”œâ”€â”€ decision/
â”‚       â”‚   â””â”€â”€ __init__.py
â”‚       â”œâ”€â”€ action/
â”‚       â”‚   â””â”€â”€ __init__.py
â”‚       â”œâ”€â”€ goal/
â”‚       â”‚   â””â”€â”€ __init__.py
â”‚       â””â”€â”€ strategy/
â”‚           â””â”€â”€ __init__.py
â”‚
â”œâ”€â”€ meta/                               # ðŸ”® ÃœST-BÄ°LÄ°Åž KATMANI
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚
â”‚   â”œâ”€â”€ consciousness/                  # ðŸŒŸ Global Workspace
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â””â”€â”€ workspace/
â”‚   â”‚       â””â”€â”€ __init__.py
â”‚   â”‚
â”‚   â”œâ”€â”€ metamind/                       # ðŸ“Š Sistem Analizi
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ analyzers/
â”‚   â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ insights/
â”‚   â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ patterns/
â”‚   â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚   â””â”€â”€ learning/
â”‚   â”‚       â””â”€â”€ __init__.py
â”‚   â”‚
â”‚   â””â”€â”€ monitoring/                     # ðŸ“¡ Sistem Ä°zleme
â”‚       â”œâ”€â”€ __init__.py
â”‚       â”œâ”€â”€ metrics/
â”‚       â”‚   â””â”€â”€ __init__.py
â”‚       â”œâ”€â”€ alerts/
â”‚       â”‚   â””â”€â”€ __init__.py
â”‚       â””â”€â”€ predata/
â”‚           â””â”€â”€ __init__.py
â”‚
â”œâ”€â”€ foundation/                         # ðŸ—ï¸ TEMEL YAPILAR
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚
â”‚   â”œâ”€â”€ state/                          # StateVector
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ vector.py
â”‚   â”‚   â””â”€â”€ fields.py
â”‚   â”‚
â”‚   â”œâ”€â”€ types/                          # Ortak tipler
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ base.py
â”‚   â”‚   â”œâ”€â”€ actions.py
â”‚   â”‚   â””â”€â”€ results.py
â”‚   â”‚
â”‚   â”œâ”€â”€ ontology/                       # ðŸ“š Kavram TanÄ±mlarÄ±
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ concepts.py
â”‚   â”‚   â”œâ”€â”€ relations.py
â”‚   â”‚   â””â”€â”€ grounding.py
â”‚   â”‚
â”‚   â””â”€â”€ schemas/                        # DB ÅžemalarÄ±
â”‚       â””â”€â”€ __init__.py
â”‚
â”œâ”€â”€ infra/                              # âš™ï¸ ALTYAPI
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚
â”‚   â”œâ”€â”€ logging/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ logger.py
â”‚   â”‚   â””â”€â”€ handlers/
â”‚   â”‚       â””â”€â”€ __init__.py
â”‚   â”‚
â”‚   â”œâ”€â”€ storage/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ postgres/
â”‚   â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ file/
â”‚   â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚   â””â”€â”€ memory/
â”‚   â”‚       â””â”€â”€ __init__.py
â”‚   â”‚
â”‚   â””â”€â”€ config/
â”‚       â”œâ”€â”€ __init__.py
â”‚       â””â”€â”€ loader.py
â”‚
â”œâ”€â”€ interface/                          # ðŸ–¥ï¸ DIÅž ARAYÃœZ
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚
â”‚   â”œâ”€â”€ dashboard/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â””â”€â”€ app.py
â”‚   â”‚
â”‚   â”œâ”€â”€ api/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â””â”€â”€ routes.py
â”‚   â”‚
â”‚   â””â”€â”€ cli/
â”‚       â”œâ”€â”€ __init__.py
â”‚       â””â”€â”€ commands.py
â”‚
â”œâ”€â”€ engine/                             # ðŸ”„ MOTOR
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ cycle.py
â”‚   â”œâ”€â”€ events/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â””â”€â”€ bus.py
â”‚   â””â”€â”€ phases/
â”‚       â”œâ”€â”€ __init__.py
â”‚       â””â”€â”€ definitions.py
â”‚
â”œâ”€â”€ tests/                              # ðŸ§ª TESTLER
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ unit/
â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”œâ”€â”€ integration/
â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â””â”€â”€ e2e/
â”‚       â””â”€â”€ __init__.py
â”‚
â”œâ”€â”€ config/                             # ðŸ“‹ YAPILANDIRMA
â”‚   â”œâ”€â”€ default.yaml
â”‚   â”œâ”€â”€ logging.yaml
â”‚   â””â”€â”€ metamind.yaml
â”‚
â”œâ”€â”€ sql/                                # ðŸ—ƒï¸ DB
â”‚   â””â”€â”€ schema.sql
â”‚
â”œâ”€â”€ scenarios/                          # ðŸŽ¬ SENARYOLAR
â”‚   â””â”€â”€ test_scenarios.yaml
â”‚
â”œâ”€â”€ main.py                             # ðŸš€ GÄ°RÄ°Åž
â””â”€â”€ requirements.txt
```

### 4.3 SayÄ±sal Ã–zet

| Metrik | DeÄŸer |
|--------|-------|
| Ãœst kategori | 6 |
| Lob sayÄ±sÄ± | 6 |
| Toplam klasÃ¶r | ~55 (SABÄ°T) |
| BaÅŸlangÄ±Ã§ dosya | ~65 |

---

## 5. 6 LOB DETAYI

### 5.1 LOB 1: PERCEPTION (AlgÄ±)

| Alt ModÃ¼l | AmaÃ§ |
|-----------|------|
| sensory/ | Ham girdi iÅŸleme |
| attention/ | Dikkat yÃ¶nlendirme |
| fusion/ | Multimodal birleÅŸtirme |
| world_model/ | DÃ¼nya durumu tahmini |

### 5.2 LOB 2: COGNITION (BiliÅŸ)

| Alt ModÃ¼l | AmaÃ§ |
|-----------|------|
| reasoning/ | MantÄ±k, Ã§Ä±karÄ±m |
| evaluation/ | DeÄŸerlendirme |
| creativity/ | YaratÄ±cÄ±lÄ±k, hipotez |
| simulation/ | Ä°Ã§ simÃ¼lasyon |

### 5.3 LOB 3: MEMORY (Bellek)

| Alt ModÃ¼l | AmaÃ§ |
|-----------|------|
| working/ | AnlÄ±k bellek (7Â±2 Ã¶ÄŸe) |
| episodic/ | Olay hafÄ±zasÄ± |
| semantic/ | Bilgi hafÄ±zasÄ± |
| emotional/ | Duygusal anÄ±lar |
| consolidation/ | Bellek pekiÅŸtirme |

### 5.4 LOB 4: AFFECT (DuygulanÄ±m)

| Alt ModÃ¼l | AmaÃ§ |
|-----------|------|
| emotion/core/ | Temel duygu iÅŸleme |
| emotion/primitive/ | Ä°lkel tepkiler (threat, attachment) |
| emotion/somatic/ | Bedensel iÅŸaretler |
| emotion/regulation/ | Duygu dÃ¼zenleme |
| social/empathy/ | BaÅŸkasÄ±nÄ± anlama |
| social/sympathy/ | Duygusal tepki |
| social/trust/ | GÃ¼ven yÃ¶netimi |
| social/theory_of_mind/ | Zihin teorisi |

### 5.5 LOB 5: SELF (Benlik)

| Alt ModÃ¼l | AmaÃ§ |
|-----------|------|
| identity/ | Kim olduÄŸum |
| values/ | DeÄŸerlerim |
| ethics/ | Etik kurallar (ETHMOR) |
| narrative/ | Hikayem, sÃ¼reklilik |
| integrity/ | TutarlÄ±lÄ±k izleme |

### 5.6 LOB 6: EXECUTIVE (YÃ¶netici)

| Alt ModÃ¼l | AmaÃ§ |
|-----------|------|
| planning/ | Plan yapma |
| decision/ | Karar verme |
| action/ | Aksiyon seÃ§me |
| goal/ | Hedef yÃ¶netimi |
| strategy/ | Strateji belirleme |

---

## 6. META KATMANI DETAYI

### 6.1 Consciousness (Global Workspace)

```
AmaÃ§: TÃ¼m modÃ¼llerden gelen bilgiyi entegre etme

Perception: "DÃ¼ÅŸman gÃ¶rÃ¼yorum"
Memory: "Bu dÃ¼ÅŸmanÄ± tanÄ±yorum"
Emotion: "Korku hissediyorum"
          â†“
    [CONSCIOUSNESS]
          â†“
Entegre: "TanÄ±dÄ±ÄŸÄ±m tehlikeli dÃ¼ÅŸman, kaÃ§malÄ±yÄ±m"
```

### 6.2 MetaMind (Sistem Analizi)

| Alt ModÃ¼l | Soru |
|-----------|------|
| analyzers/ | "Bu cycle nasÄ±l gitti?" |
| insights/ | "Ne Ã¶ÄŸrendim?" |
| patterns/ | "Tekrarlayan kalÄ±plar var mÄ±?" |
| learning/ | "NasÄ±l geliÅŸebilirim?" |

### 6.3 Monitoring (Sistem Ä°zleme)

| Alt ModÃ¼l | AmaÃ§ |
|-----------|------|
| metrics/ | Performans Ã¶lÃ§Ã¼mleri |
| alerts/ | Anomali tespiti |
| predata/ | Veri toplama (araÅŸtÄ±rma iÃ§in) |

---

## 7. STATEVECTOR TASARIMI

### 7.1 Core + Extensions Pattern

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict

class SVField(str, Enum):
    """Merkezi alan tanÄ±mÄ± - typo korumasÄ±"""
    # Core alanlar
    RESOURCE = "resource"
    THREAT = "threat"
    WELLBEING = "wellbeing"
    
    # Extension alanlar
    VALENCE = "valence"
    AROUSAL = "arousal"
    DOMINANCE = "dominance"
    COGNITIVE_EMPATHY = "cognitive_empathy"
    AFFECTIVE_EMPATHY = "affective_empathy"
    TRUST_VALUE = "trust_value"
    # Yeni alan? Buraya ekle

@dataclass
class StateVector:
    """GeniÅŸletilebilir StateVector"""
    
    # CORE - Asla deÄŸiÅŸmez (3 alan)
    resource: float = 0.5
    threat: float = 0.0
    wellbeing: float = 0.5
    
    # EXTENSIONS - Dinamik, Enum korumalÄ±
    _extensions: Dict[SVField, float] = field(default_factory=dict)
    
    def get(self, key: SVField, default: float = 0.0) -> float:
        """Core veya extension alanÄ±na eriÅŸ"""
        if hasattr(self, key.value):
            return getattr(self, key.value)
        return self._extensions.get(key, default)
    
    def set(self, key: SVField, value: float) -> None:
        """Extension alanÄ± ekle/gÃ¼ncelle"""
        self._extensions[key] = value
```

### 7.2 KullanÄ±m

```python
# OluÅŸturma
state = StateVector(resource=0.8, threat=0.2, wellbeing=0.6)

# Extension ekleme (typo korumalÄ±)
state.set(SVField.AROUSAL, 0.5)
state.set(SVField.COGNITIVE_EMPATHY, 0.7)

# EriÅŸim
arousal = state.get(SVField.AROUSAL)  # 0.5
trust = state.get(SVField.TRUST_VALUE, 0.5)  # default: 0.5

# Typo yaparsanÄ±z IDE uyarÄ±r:
# state.set(SVField.AROUSEL, 0.5)  â† AttributeError!
```

---

## 8. EMPATHY/SYMPATHY/TRUST

### 8.1 KonumlarÄ±

| Kavram | Konum | Neden |
|--------|-------|-------|
| Empathy | `core/affect/social/empathy/` | BaÅŸkasÄ±nÄ± anlama |
| Sympathy | `core/affect/social/sympathy/` | Duygusal tepki |
| Trust | `core/affect/social/trust/` | GÃ¼ven yÃ¶netimi |

### 8.2 Hesaplama AkÄ±ÅŸÄ±

```
Agent AlgÄ±landÄ±
       â”‚
       â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚     EMPATHY     â”‚  "Bu kiÅŸi ne durumda?"
â”‚  (Simulation)   â”‚  4 kanal: cognitive, affective, somatic, projective
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚ EmpathyResult
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚    SYMPATHY     â”‚  "Bu bende ne uyandÄ±rÄ±yor?"
â”‚  (Response)     â”‚  8 tÃ¼r: compassion, pity, joy, gratitude...
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚ SympathyResult
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚      TRUST      â”‚  "Bu kiÅŸiye gÃ¼venebilir miyim?"
â”‚  (Evaluation)   â”‚  7 tÃ¼r: blind, earned, cautious, neutral...
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚ TrustResult
         â–¼
    Executive'e
```

### 8.3 Empathy: Simulation Theory

```python
def calculate_empathy(agent, self_state):
    """
    Experience Matching DEÄžÄ°L, Simulation Theory
    
    YanlÄ±ÅŸ: "Ben de bÃ¶yle bir ÅŸey yaÅŸadÄ±m mÄ±?" â†’ Memory ara
    DoÄŸru:  "Onun yerinde olsam ne hissederdim?" â†’ SimÃ¼le et
    """
    
    # 4 kanal hesapla
    cognitive = calculate_cognitive(agent)      # Zihinsel anlama
    affective = calculate_affective(agent)      # Duygusal rezonans
    somatic = calculate_somatic(agent)          # Bedensel his
    projective = calculate_projective(agent)    # "Ben olsam" simÃ¼lasyonu
    
    return EmpathyResult(
        channels=EmpathyChannels(cognitive, affective, somatic, projective),
        total=weighted_average([cognitive, affective, somatic, projective])
    )
```

---

## 9. BÃœYÃœME STRATEJÄ°SÄ°

### 9.1 Prensip: KlasÃ¶r EKLEME, Dosya EKLE

```
YANLIÅž:
  Yeni Ã¶zellik â†’ Yeni klasÃ¶r oluÅŸtur (REFACTOR!)

DOÄžRU:
  Yeni Ã¶zellik â†’ Mevcut klasÃ¶re dosya ekle (Temiz!)
```

### 9.2 Ã–rnek: Empathy GeliÅŸtirme

**GÃ¼n 1 - BaÅŸlangÄ±Ã§:**
```
core/affect/social/empathy/
â””â”€â”€ __init__.py          # class EmpathyCore: pass
```

**GÃ¼n 30 - BÃ¼yÃ¼me:**
```
core/affect/social/empathy/
â”œâ”€â”€ __init__.py          # Facade - dÄ±ÅŸarÄ±ya tek giriÅŸ
â”œâ”€â”€ calculator.py        # Ana hesaplama (YENÄ° DOSYA)
â”œâ”€â”€ channels.py          # 4 kanal tanÄ±mlarÄ± (YENÄ° DOSYA)
â””â”€â”€ simulation.py        # Simulation engine (YENÄ° DOSYA)
```

**Refactor:** âŒ YOK! Sadece dosya eklendi.

---

## 10. CHECKPOINT FORMATI

Bu sohbete dÃ¶ndÃ¼ÄŸÃ¼nde ÅŸu formatÄ± kullan:

```markdown
## CHECKPOINT - [Tarih]

### Mevcut Durum
- Dizin sayÄ±sÄ±: X (hedef: ~55 sabit)
- Dosya sayÄ±sÄ±: Y
- Test sayÄ±sÄ±: Z (geÃ§en/toplam)

### Son YapÄ±lanlar
1. ...
2. ...

### Ã‡alÄ±ÅŸan ModÃ¼ller
- [ ] core/perception
- [ ] core/cognition
- [ ] core/memory
- [ ] core/affect/emotion
- [ ] core/affect/social (empathy, sympathy, trust)
- [ ] core/self
- [ ] core/executive
- [ ] meta/consciousness
- [ ] meta/metamind
- [ ] meta/monitoring
- [ ] engine/cycle
- [ ] interface/dashboard

### TakÄ±ldÄ±ÄŸÄ±m Yer / Soru
...

### Sonraki Hedef
...
```

---

## 11. KRÄ°TÄ°K UYARILAR

### 11.1 YAPMA Listesi

```
âŒ Yeni klasÃ¶r oluÅŸturma (iskelet sabit!)
âŒ Ä°lk gÃ¼nden karmaÅŸÄ±k kod yazma
âŒ "Ä°leride lazÄ±m olur" diye Ã¶zellik ekleme
âŒ StateVector'a string key kullanma (Enum kullan)
âŒ Monitoring'i sonraya bÄ±rakma
âŒ AynÄ± iÅŸi yapan birden fazla modÃ¼l
âŒ 3 seviyeden derin import path
```

### 11.2 YAP Listesi

```
âœ… Mevcut klasÃ¶re dosya ekle
âœ… Ã–nce Ã§alÄ±ÅŸtÄ±r, sonra gÃ¼zelleÅŸtir
âœ… Her modÃ¼l tek sorumluluk
âœ… StateVector Enum pattern kullan
âœ… Monitoring ilk gÃ¼nden aktif
âœ… Her bÃ¼yÃ¼k kararÄ± kaydet
âœ… DÃ¼zenli checkpoint yap
```

### 11.3 Dosya Ekleme KontrolÃ¼

Yeni dosya eklemeden Ã¶nce sor:

```
1. Hangi mevcut klasÃ¶re girmeli?
2. Bu gerÃ§ekten yeni dosya mÄ±, mevcut dosyaya eklenebilir mi?
3. 10 satÄ±rdan fazla mÄ± olacak?
4. Test edilebilir mi?

TÃ¼m cevaplar olumlu â†’ Dosya ekle
Aksi halde â†’ Mevcut dosyaya ekle veya bekle
```

---

## 12. REFERANSLAR

### 12.1 Akademik

- Goldman, A. I. (2006). *Simulating Minds* - Empathy Simulation Theory
- Baars, B. - Global Workspace Theory (Consciousness)
- Damasio, A. - Somatic Markers Hypothesis
- Oatley & Johnson-Laird - Cognitive Theory of Emotions

### 12.2 UEM v1 DÃ¶kÃ¼manlarÄ± (ArÅŸiv)

- UEM_Vision_v2_Cognitive_Pipeline.md - 14-step vizyon
- UEM_Empathy_Sympathy_Trust_FINAL_BRIEF_v1.md - Empathy detaylarÄ±
- UEM_PreData_Log_Master_Implementation_Document_v5.md - Logging sistemi
- UEM_Project_Tree.md - v1 gerÃ§ek yapÄ±sÄ± (100 dizin!)

### 12.3 Bu Sohbetten Ã‡Ä±ktÄ±lar

- UEM_Architecture_5Module_Brief_Claude.md - Ä°lk 5 modÃ¼l Ã¶nerisi
- UEM_MiniBrief_5Module_Alice_Review.md - Alice eleÅŸtirisi

---

## 13. SÃ–ZLÃœK

| Terim | TanÄ±m |
|-------|-------|
| **Cognition** | DÃ¼ÅŸÃ¼nme, akÄ±l yÃ¼rÃ¼tme |
| **Metacognition** | DÃ¼ÅŸÃ¼nme hakkÄ±nda dÃ¼ÅŸÃ¼nme, Ã¶z-izleme |
| **Consciousness** | Global Workspace - bilgi entegrasyonu |
| **StateVector** | AjanÄ±n iÃ§ durumunu temsil eden vektÃ¶r |
| **Cognitive Cycle** | AlgÄ± â†’ BiliÅŸ â†’ Duygu â†’ Karar dÃ¶ngÃ¼sÃ¼ |
| **Empathy** | BaÅŸkasÄ±nÄ±n durumunu anlama (biliÅŸsel) |
| **Sympathy** | AnladÄ±ktan sonra duygusal tepki |
| **Trust** | GeÃ§miÅŸ etkileÅŸimlere dayalÄ± gÃ¼ven |
| **ETHMOR** | Ethics + Moral - Etik deÄŸerlendirme sistemi |
| **MetaMind** | Meta-cognitive analysis - Sistem analizi |
| **Ontology** | KavramlarÄ±n tanÄ±mÄ± ve iliÅŸkileri |
| **Event Bus** | ModÃ¼ller arasÄ± iletiÅŸim (Pub/Sub) |
| **Lob** | Beyin bÃ¶lgesi analojisi - fonksiyonel modÃ¼l |

---

## 14. SON SÃ–Z

```
v1: 100 dizin, 353 dosya â†’ KarmaÅŸÄ±k, yÃ¶netilemez
v2: 55 klasÃ¶r (SABÄ°T), baÅŸlangÄ±Ã§ta ~65 dosya â†’ BÃ¼yÃ¼t gerekirse
```

**Ä°skelet baÅŸtan tam, iÃ§i boÅŸ.**  
**KlasÃ¶r EKLEME, dosya EKLE.**  
**Monitoring ilk gÃ¼nden.**

---

**DokÃ¼man Sonu**

*Bu dokÃ¼man yeni UEM v2 projesinde rehber ve iki sohbet arasÄ±nda kÃ¶prÃ¼ gÃ¶revi gÃ¶rÃ¼r.*
*Checkpoint formatÄ±nÄ± kullanarak ilerlemeyi raporla.*
