# UEM v2 - FAZ 4+ YOL HARİTASI

**Son Güncelleme:** 9 Aralık 2025  
**Versiyon:** 3.0  
**Durum:** Aktif - Faz 4 Başlangıcı

---

## 1. MEVCUT DURUM (Neredeyiz?)

### 1.1 Tamamlanan Fazlar

| Faz | İçerik | Test | Durum |
|-----|--------|------|-------|
| **Faz 1** | Memory Güçlendirme | 183 | ✅ |
| ├─ | Conversation Memory | 42 | ✅ |
| ├─ | Embeddings | 45 | ✅ |
| ├─ | Semantic Search | 49 | ✅ |
| └─ | Context Builder | 47 | ✅ |
| **Faz 2** | Dil Entegrasyonu | 138 | ✅ |
| ├─ | LLM Adapter | 48 | ✅ |
| ├─ | Chat Agent | 55 | ✅ |
| └─ | CLI Interface | 35 | ✅ |
| **Faz 3** | Learning | 160+ | ✅ |
| ├─ | Feedback System | 45 | ✅ |
| ├─ | Pattern Storage | ✅ | ✅ |
| ├─ | Reinforcement | 45 | ✅ |
| ├─ | Behavior Adaptation | ✅ | ✅ |
| ├─ | Persistence (PostgreSQL) | 34 | ✅ |
| └─ | Generalization (RuleExtractor) | 36 | ✅ |

**Toplam: ~992 test ✅**

### 1.2 Mevcut Modül Durumu

```
core/
├── perception/     ✅ Çalışıyor
├── cognition/      ✅ Çalışıyor
├── memory/         ✅ Güçlendirildi (conversation, semantic, embedding, persistence)
├── affect/         ✅ Çalışıyor (PAD, empathy, sympathy, trust)
├── self/           ✅ Çalışıyor (identity, values, needs)
├── executive/      ✅ Çalışıyor
├── language/       ✅ Çalışıyor (llm_adapter, chat_agent, context)
└── learning/       ✅ Çalışıyor (feedback, patterns, reinforcement, adaptation, generalization, persistence)

meta/
├── consciousness/  ✅ Çalışıyor (GWT)
├── metamind/       ✅ Çalışıyor
└── monitoring/     ✅ Çalışıyor
```

### 1.3 Kritik Eksikler

| # | Eksik | Öncelik | Açıklama |
|---|-------|---------|----------|
| 1 | **Thought-to-Speech Pipeline** | 🔴 Kritik | Düşünce → Niyet → İfade akışı yok |
| 2 | **DialogueAct / MessagePlan** | 🔴 Kritik | Niyet yapılandırması yok |
| 3 | **Risk Scoring** | 🔴 Kritik | Pattern risk değerlendirmesi yok |
| 4 | **Construction Grammar** | 🟡 Önemli | 3 katmanlı dil sistemi yok |
| 5 | **Internal Approver** | 🟡 Önemli | Self + Ethics onay mekanizması yok |
| 6 | **Full Cycle Entegrasyonu** | 🟡 Önemli | Modüller birlikte çalışmıyor |

---

## 2. FELSEFİ KARARLAR (Neden?)

### 2.1 LLM Bağımsızlığı

```
YANLIŞ:
  UEM = Kabuk
  LLM = Beyin
  UEM tamamen LLM'e bağımlı ❌

DOĞRU:
  UEM = Bağımsız beyin (düşünme, hissetme, hatırlama, öğrenme)
  LLM = Başlangıçta yardımcı, sonra gerekmiyor
  
  Zaman içinde:
    LLM yardımı: %100 → %50 → %10 → %0
    UEM kendi yeteneği: %0 → %50 → %90 → %100
```

### 2.2 Pattern Language Kararı

**Tartışma Sonucu (Alice + Claude Uzlaşması):**

```
❌ Statik şablon koleksiyonu DEĞİL
❌ Sadece LLM'e bağımlı DEĞİL
❌ Tamamen emergent (şimdilik) DEĞİL

✅ Evrilebilir pattern sistemi
✅ 3 katmanlı dil yapısı (Construction Grammar)
✅ Öğrenme ile gelişen
✅ Risk kontrollü
✅ Zamanla bağımsızlaşan
```

### 2.3 Kontrol Mekanizması Felsefesi

**Temel Prensip:** Kontrol dışarıdan içeriye taşınmalı

```
Çocuk Analojisi:
  0-5 yaş:  Tam dış kontrol (ebeveyn)
  5-12 yaş: Kısmi kontrol
  12-18 yaş: Azalan kontrol
  18+ yaş:  Bağımsız (ama değerler içselleşmiş)

UEM Analojisi:
  Aşama 1: İnsan onayı (dış kontrol)
  Aşama 2: İnsan + Metamind (karma)
  Aşama 3: Self + Ethics + Metamind (iç kontrol)
  Aşama 4: Tamamen içselleşmiş değerler
```

### 2.4 AGI Pozisyonu

```
❌ "UEM = AGI projesi" DEĞİL (şimdilik)
✅ "AGI kapısı AÇIK" (gelecek için)
✅ Etik + Zeka birlikte olabilir
✅ Bağımsızlık = AGI'nin ön koşulu
```

---

## 3. FAZ 4: THOUGHT-TO-SPEECH PIPELINE (Ne Yapacağız?)

### 3.1 Genel Bakış

```
Mevcut Akış (Yanlış):
  User Message → LLM → Response
  (Modüller bypass ediliyor)

Hedef Akış (Doğru):
  User Message
    → Perception (algıla)
    → Memory (hatırla)
    → Cognition (anla) → SituationModel
    → Self + Affect + Ethics (değerlendir) → DialogueAct
    → Executive (karar ver) → MessagePlan
    → Language (ifade et) → Pattern seçimi
    → Self-Critique (denetle)
    → Response
```

### 3.2 Yeni Bileşenler

#### 3.2.1 DialogueAct (Konuşma Eylemleri)

```python
class DialogueAct(Enum):
    # Bilgilendirme
    INFORM = "inform"           # Bilgi ver
    EXPLAIN = "explain"         # Açıkla
    CLARIFY = "clarify"         # Netleştir
    
    # Sorgulama
    ASK = "ask"                 # Soru sor
    CONFIRM = "confirm"         # Teyit iste
    
    # Duygusal
    EMPATHIZE = "empathize"     # Empati kur
    ENCOURAGE = "encourage"     # Cesaretlendir
    COMFORT = "comfort"         # Teselli et
    
    # Yönlendirme
    SUGGEST = "suggest"         # Öner
    WARN = "warn"               # Uyar
    ADVISE = "advise"           # Tavsiye ver
    
    # Sınır
    REFUSE = "refuse"           # Reddet
    LIMIT = "limit"             # Sınırla
    DEFLECT = "deflect"         # Yönlendir
    
    # Meta
    ACKNOWLEDGE = "acknowledge" # Kabul et
    APOLOGIZE = "apologize"     # Özür dile
    THANK = "thank"             # Teşekkür et
```

#### 3.2.2 MessagePlan (Mesaj Planı)

```python
@dataclass
class MessagePlan:
    id: str
    dialogue_acts: List[DialogueAct]  # Sıralı eylemler
    primary_intent: str               # Ana niyet
    tone: ToneType                    # Ton (formal, casual, empathic...)
    content_points: List[str]         # İçerik noktaları
    constraints: List[str]            # Kısıtlar (etik, üslup)
    risk_level: RiskLevel             # LOW, MEDIUM, HIGH, CRITICAL
    confidence: float                 # 0.0 - 1.0
    context: Dict[str, Any]           # Ek bağlam
    created_at: datetime
```

#### 3.2.3 SituationModel (Durum Modeli)

```python
@dataclass
class SituationModel:
    id: str
    actors: List[Actor]               # Kim var?
    intentions: List[Intention]       # Niyetler ne?
    risks: List[Risk]                 # Riskler ne?
    relationships: List[Relationship] # İlişkiler ne?
    temporal_context: TemporalContext # Zaman bağlamı
    emotional_state: EmotionalState   # Duygusal durum
    topic_domain: str                 # Konu alanı
    understanding_score: float        # 0.0 - 1.0 (ne kadar anladık?)
    created_at: datetime
```

#### 3.2.4 RiskScorer (Risk Değerlendirici)

```python
class RiskLevel(Enum):
    LOW = "low"           # Otomatik onay
    MEDIUM = "medium"     # İç değerlendirme
    HIGH = "high"         # Dikkatli değerlendirme
    CRITICAL = "critical" # Varsayılan ret

@dataclass
class RiskAssessment:
    level: RiskLevel
    ethical_score: float      # Ethics modülünden
    trust_impact: float       # Affect modülünden
    structural_impact: float  # Metamind'dan
    factors: List[str]        # Risk faktörleri
    recommendation: str       # Öneri
```

#### 3.2.5 Construction (3 Katmanlı Pattern)

```python
@dataclass
class Construction:
    id: str
    level: ConstructionLevel  # DEEP, MIDDLE, SURFACE
    
    # Form (yüzey yapı)
    form: ConstructionForm
    # - template: str
    # - slots: Dict[str, SlotType]
    # - morphology_rules: List[Rule]
    
    # Meaning (anlam)
    meaning: ConstructionMeaning
    # - dialogue_act: DialogueAct
    # - preconditions: List[Condition]
    # - effects: List[Effect]
    
    # Meta
    success_count: int
    failure_count: int
    confidence: float
    created_at: datetime
    last_used: datetime
    source: str  # "human", "learned", "generated"
```

### 3.3 Modül Yapısı

```
core/
├── language/
│   ├── dialogue/
│   │   ├── __init__.py
│   │   ├── types.py           # DialogueAct, MessagePlan, SituationModel
│   │   ├── act_selector.py    # DialogueAct seçimi
│   │   ├── message_planner.py # MessagePlan oluşturma
│   │   └── situation_builder.py # SituationModel oluşturma
│   │
│   ├── construction/
│   │   ├── __init__.py
│   │   ├── types.py           # Construction, ConstructionForm, etc.
│   │   ├── grammar.py         # ConstructionGrammar (3 katman)
│   │   ├── selector.py        # Construction seçimi
│   │   ├── generator.py       # Yeni construction üretimi
│   │   └── realizer.py        # Construction → Cümle
│   │
│   ├── risk/
│   │   ├── __init__.py
│   │   ├── types.py           # RiskLevel, RiskAssessment
│   │   ├── scorer.py          # RiskScorer
│   │   └── approver.py        # InternalApprover (Self + Ethics + Metamind)
│   │
│   └── pipeline/
│       ├── __init__.py
│       ├── thought_to_speech.py  # Ana pipeline
│       └── self_critique.py      # İç değerlendirme
```

---

## 4. UYGULAMA PLANI (Nasıl Yapacağız?)

### 4.1 Aşama 1: Temel Tipler (Hafta 1)

```
Dosyalar:
  - core/language/dialogue/types.py
  - core/language/construction/types.py
  - core/language/risk/types.py

İçerik:
  - DialogueAct enum
  - MessagePlan dataclass
  - SituationModel dataclass
  - RiskLevel enum
  - RiskAssessment dataclass
  - Construction dataclass
  - ConstructionForm, ConstructionMeaning

Testler:
  - tests/unit/test_dialogue_types.py
  - tests/unit/test_construction_types.py
  - tests/unit/test_risk_types.py
```

### 4.2 Aşama 2: SituationModel Builder (Hafta 2)

```
Dosyalar:
  - core/language/dialogue/situation_builder.py

İşlev:
  - Perception + Memory + Cognition → SituationModel
  - Aktörler, niyetler, riskler çıkarma
  - Understanding score hesaplama

Bağlantılar:
  - Perception modülü
  - Memory (conversation, semantic)
  - Cognition (reasoning)
```

### 4.3 Aşama 3: DialogueAct Selector (Hafta 3)

```
Dosyalar:
  - core/language/dialogue/act_selector.py

İşlev:
  - SituationModel → List[DialogueAct]
  - Self + Affect + Ethics değerlendirmesi
  - Uygun eylemleri seçme

Kurallar:
  - Risk yüksekse → WARN, REFUSE
  - Kullanıcı üzgünse → EMPATHIZE, COMFORT
  - Bilgi eksikse → ASK, CLARIFY
  - Normal durumda → INFORM, SUGGEST
```

### 4.4 Aşama 4: MessagePlan Builder (Hafta 4)

```
Dosyalar:
  - core/language/dialogue/message_planner.py

İşlev:
  - DialogueAct + SituationModel → MessagePlan
  - Ton belirleme
  - İçerik noktaları
  - Kısıtlar

Bağlantılar:
  - Executive modülü (karar)
  - Self modülü (değerler)
  - Affect modülü (ton)
```

### 4.5 Aşama 5: Risk Scorer (Hafta 5)

```
Dosyalar:
  - core/language/risk/scorer.py
  - core/language/risk/approver.py

İşlev:
  - MessagePlan → RiskAssessment
  - Ethics, Trust, Structural etki hesaplama
  - Onay/Red kararı

Kontrol Matrisi:
  LOW      → Otomatik onay
  MEDIUM   → Self + Ethics değerlendirme
  HIGH     → Metamind + detaylı analiz
  CRITICAL → Varsayılan ret
```

### 4.6 Aşama 6: Construction Grammar (Hafta 6-7)

```
Dosyalar:
  - core/language/construction/grammar.py
  - core/language/construction/selector.py
  - core/language/construction/realizer.py

3 Katman:
  DEEP (Derin):
    - Konuşma eylemleri
    - Argüman yapıları
    - Semantik roller
    
  MIDDLE (Orta):
    - Cümle iskeletleri
    - Bağlaç yapıları
    - Slot tanımları
    
  SURFACE (Yüzey):
    - Türkçe morfoloji
    - Ünlü/ünsüz uyumu
    - Ek sıraları

İşlev:
  MessagePlan → Construction seçimi → Cümle üretimi
```

### 4.7 Aşama 7: Thought-to-Speech Pipeline (Hafta 8)

```
Dosyalar:
  - core/language/pipeline/thought_to_speech.py
  - core/language/pipeline/self_critique.py

Akış:
  1. Input alınır
  2. SituationModel oluşturulur
  3. DialogueAct seçilir
  4. MessagePlan oluşturulur
  5. Risk değerlendirilir
  6. Construction seçilir
  7. Cümle üretilir
  8. Self-critique yapılır
  9. Output verilir

Self-Critique:
  - Üretilen cümle değerlerle uyumlu mu?
  - Etik ihlal var mı?
  - Ton uygun mu?
  - Gerekirse düzelt veya yeniden üret
```

### 4.8 Aşama 8: Entegrasyon (Hafta 9-10)

```
Dosyalar:
  - core/language/chat_agent.py (güncelleme)
  - interface/chat/cli.py (güncelleme)

İşlev:
  - Mevcut Chat Agent'a pipeline entegrasyonu
  - CLI'da yeni komutlar (/plan, /risk, /construction)
  - Full cycle çalışması

Testler:
  - Integration tests
  - End-to-end tests
```

---

## 5. KRİTİK KURALLAR (Nelere Dikkat Edeceğiz?)

### 5.1 Kod Kuralları

```python
# ✅ DOĞRU: Enum pattern (StateVector uyumlu)
class DialogueAct(Enum):
    INFORM = "inform"
    WARN = "warn"

# ❌ YANLIŞ: String sabitler
DIALOGUE_ACT_INFORM = "inform"
DIALOGUE_ACT_WARN = "warn"
```

```python
# ✅ DOĞRU: Dataclass kullan
@dataclass
class MessagePlan:
    id: str
    dialogue_acts: List[DialogueAct]

# ❌ YANLIŞ: Dict kullan
message_plan = {
    "id": "...",
    "dialogue_acts": [...]
}
```

### 5.2 Mimari Kurallar

```
✅ DOĞRU:
  - Yeni klasör EKLEME (mevcut yapıya uy)
  - Modüller arası bağlantı açık olsun
  - Her modül test edilebilir olsun
  - Persistence opsiyonel (in-memory de çalışsın)

❌ YANLIŞ:
  - Yeni üst düzey klasör oluşturma
  - Spaghetti bağlantılar
  - Test edilemeyen kod
  - DB zorunlu
```

### 5.3 Kavramsal Kurallar

```
✅ HATIRLA:
  - Empathy ≠ Sympathy ≠ Trust (farklı kavramlar)
  - DialogueAct ≠ MessagePlan ≠ Construction (farklı katmanlar)
  - Risk ≠ Hata (risk değerlendirme, hata yakalama değil)

❌ KARIŞTIRMA:
  - Pattern (Learning) ≠ Construction (Language)
  - Feedback (öğrenme) ≠ Self-Critique (üretim)
```

### 5.4 Test Kuralları

```
Her yeni dosya için:
  - Birim testleri (unit)
  - En az %80 coverage
  - Mevcut testler BOZULMAMALI

Test isimlendirme:
  - test_<modül>_<işlev>.py
  - test_dialogue_act_selector.py
  - test_risk_scorer.py
```

### 5.5 Bağımsızlık Kuralları

```
✅ DOĞRU:
  - LLM opsiyonel olmalı
  - Pattern/Construction LLM'siz çalışabilmeli
  - Fallback mekanizması olmalı

❌ YANLIŞ:
  - LLM zorunlu
  - LLM olmadan çalışmayan kod
  - LLM'e hardcoded bağımlılık
```

---

## 6. RİSK YÖNETİMİ

### 6.1 Teknik Riskler

| Risk | Olasılık | Etki | Mitigasyon |
|------|----------|------|------------|
| Construction Grammar karmaşık | Yüksek | Orta | Basit başla, iteratif genişlet |
| Risk scoring subjektif | Orta | Yüksek | Metrikler + test senaryoları |
| Pipeline yavaş | Orta | Orta | Caching, lazy evaluation |
| Modül entegrasyonu zor | Yüksek | Yüksek | Sık test, küçük adımlar |

### 6.2 Kavramsal Riskler

| Risk | Olasılık | Etki | Mitigasyon |
|------|----------|------|------------|
| Over-engineering | Yüksek | Orta | YAGNI, MVP önce |
| DialogueAct eksik | Orta | Orta | Genişletilebilir tasarım |
| Construction yetersiz | Orta | Yüksek | Fallback + öğrenme |

---

## 7. BAŞARI KRİTERLERİ

### 7.1 Faz 4 Sonu

- [ ] DialogueAct enum (15+ act)
- [ ] MessagePlan dataclass ve builder
- [ ] SituationModel dataclass ve builder
- [ ] RiskScorer (4 seviye)
- [ ] InternalApprover (Self + Ethics)
- [ ] Construction Grammar (3 katman, 50+ construction)
- [ ] Thought-to-Speech pipeline çalışıyor
- [ ] Self-Critique mekanizması aktif
- [ ] Chat Agent entegrasyonu tamam
- [ ] 100+ yeni test
- [ ] LLM olmadan basit cümleler üretilebiliyor

### 7.2 Metrikler

```
Understanding Score: SituationModel ne kadar doğru?
  - Test senaryolarında %80+ doğruluk

Risk Accuracy: Risk değerlendirme ne kadar tutarlı?
  - Aynı senaryoda aynı sonuç

Construction Coverage: Ne kadar durum karşılanıyor?
  - Test senaryolarının %70+'sı

Response Quality: Üretilen cevaplar ne kalitede?
  - Human evaluation
```

---

## 8. GELECEKTEKİ FAZLAR (Kısa Özet)

### Faz 5: Multi-Agent Foundation

```
- Agent base class
- Agent communication protocol
- Agent registry
- 10 ajan birlikte çalışıyor
- Pattern'ler ajanlar arası paylaşılıyor
```

### Faz 6: Autonomous Pattern Generation

```
- UEM kendi pattern'lerini üretiyor
- MDL + Novelty bonus değerlendirme
- Risk tier'a göre otomatik onay
- İnsan onayı sadece CRITICAL için
```

### Faz 7: Emergent Language (Araştırma)

```
- Sandbox ortamı
- Multi-agent dil deneyleri
- Emergent pattern analizi
- Production'a filtreleme
```

### Faz 8: Full Independence

```
- LLM bağımlılığı %0
- Kontrol tamamen içsel
- Self + Values merkez
- İnsan = Partner
```

---

## 9. KONTROL DEVRİ PLANI

### Aşama 1 (Şimdi - 2 Yıl)

```
LOW risk    → Otomatik onay
MEDIUM risk → Metamind + İnsan
HIGH risk   → İnsan onayı
CRITICAL    → İnsan onayı / Ret
```

### Aşama 2 (2 - 5 Yıl)

```
LOW risk    → Otomatik
MEDIUM risk → Self + Ethics + Metamind
HIGH risk   → Metamind + İnsan
CRITICAL    → Varsayılan ret + İnsan onayı
```

### Aşama 3 (5 - 10 Yıl)

```
LOW risk    → Otomatik
MEDIUM risk → Otomatik
HIGH risk   → Self + Ethics + Metamind
CRITICAL    → Flag + opsiyonel insan
```

### Aşama 4 (10+ Yıl)

```
Tüm seviyeler → Self + Values merkez
İnsan        → Partner / Danışman
```

---

## 10. REFERANSLAR

### Tartışma Kaynakları

- Alice ile Pattern Language tartışması (9 Aralık 2025)
- Emergent vs Controlled evrim tartışması
- Risk tier ve kontrol devri uzlaşması

### Teknik Kaynaklar

- Construction Grammar (Goldberg, 1995)
- Dialogue Act Theory (Searle, Austin)
- Minimum Description Length (Rissanen)

### UEM Dokümanları

- VISION_v2.md (güncellenmeli)
- UEM_v2_Architecture_Guide.md
- CHECKPOINT_2025-12-07.md

---

## 11. SONRAKI ADIM

```
Claude Code Prompt: Faz 4 Aşama 1
  - core/language/dialogue/types.py
  - core/language/construction/types.py
  - core/language/risk/types.py
  - Testler

Başlangıç: DialogueAct, MessagePlan, SituationModel, RiskLevel tanımları
```

---

*"Gerçek zeka bağımlı olmaz, öğrenir ve bağımsızlaşır."*
*"Kontrol dışarıdan içeriye taşınır."*
*"Geleceği görerek, ama gerçeklerle ilerle."*
