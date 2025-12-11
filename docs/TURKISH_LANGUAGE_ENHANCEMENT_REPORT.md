# UEM v2 - Turkce Dil Ogrenme ve Gelistirme Raporu

**Tarih:** 11 Aralik 2025
**Hazirlayan:** Claude Opus 4.5
**Proje Sahibi ve Denetleyen:** Isa/Kimb0t <isakara5967@gmail.com>
**Versiyon:** 1.0

---

## Icerik

1. [Yonetici Ozeti](#1-yonetici-ozeti)
2. [Mevcut Durum Analizi](#2-mevcut-durum-analizi)
3. [Tespit Edilen Eksiklikler ve Sorunlar](#3-tespit-edilen-eksiklikler-ve-sorunlar)
4. [Gelistirme Fazlari ve Onerileri](#4-gelistirme-fazlari-ve-onerileri)
5. [TDK ve Turkce Sozluk Entegrasyonu](#5-tdk-ve-turkce-sozluk-entegrasyonu)
6. [Turkce Metin Kaynaklari ve Veri Setleri](#6-turkce-metin-kaynaklari-ve-veri-setleri)
7. [Dikkat Mekanizmasi Degerlendirmesi](#7-dikkat-mekanizmasi-degerlendirmesi)
8. [Risk Analizi ve Onlemler](#8-risk-analizi-ve-onlemler)
9. [Uygulama Yol Haritasi](#9-uygulama-yol-haritasi)
10. [Sonuc ve Oneriler](#10-sonuc-ve-oneriler)
11. [Kaynaklar](#11-kaynaklar)

---

## 1. Yonetici Ozeti

### 1.1 Raporun Amaci

Bu rapor, UEM v2 projesinin Turkce dil isleme yeteneklerini analiz ederek, sistemin daha iyi Turkce ogrenmesi ve anlamasi icin gerekli gelistirmeleri ortaya koymaktadir.

### 1.2 Temel Bulgular

| Alan | Mevcut Durum | Hedef | Oncelik |
|------|--------------|-------|---------|
| Morfolojik Analiz | Yok | Tam destek | Kritik |
| Kelime Kokleri (Stemming) | Yok | Zemberek/Zeyrek | Yuksek |
| TDK Entegrasyonu | Yok | API servisi | Yuksek |
| Turkce Veri Seti | Sinirli | 100K+ ornek | Orta |
| Dikkat Mekanizmasi | Genel (spotlight) | Dilsel dikkat | Orta |
| Sozluk Destegi | Yok | Anlam + ornek | Yuksek |

### 1.3 Kritik Oneriler

1. **Zeyrek/Zemberek Entegrasyonu** - Turkce morfolojik analiz icin zorunlu
2. **TDK Sozluk API Wrapper** - Kelime anlami ve ornekler icin
3. **Turkce Corpus Genisletme** - Pattern ogrenme icin veri seti
4. **Dilsel Dikkat Katmani** - Token bazli attention mekanizmasi

---

## 2. Mevcut Durum Analizi

### 2.1 Proje Genel Bakisi

UEM v2, 6 LOB (Lobe) mimarisi uzerine kurulu, 193 modul, 2157 test ve ~15000+ satir koddan olusan kapsamli bir bilisssel mimaridir.

#### Dil Isleme Pipeline'i

```
User Input
    |
    v
[IntentRecognizer] --> Intent tanima (17 kategori)
    |
    v
[SituationBuilder] --> Durum modeli
    |
    v
[ActSelector] --> DialogueAct secimi (22 act)
    |
    v
[ConstructionSelector] --> Construction secimi (feedback-weighted)
    |
    v
[RiskScorer] --> Risk degerlendirmesi
    |
    v
[SelfCritique] --> Onayla/Revize et
    |
    v
Response Output
```

### 2.2 Turkce Dil Yetenekleri - Mevcut

#### 2.2.1 Normalize Turkish Fonksiyonu

**Konum:** `core/utils/text.py`

```python
TURKISH_TO_ASCII = {
    'u': 'u', 'U': 'U',
    'o': 'o', 'O': 'O',
    's': 's', 'S': 'S',
    'g': 'g', 'G': 'G',
    'i': 'i', 'I': 'I',
    'c': 'c', 'C': 'C',
}

def normalize_turkish(text: str) -> str:
    # Turkce karakterleri ASCII'ye donusturur
    # Lowercase yapar
```

**Deger:** Temel karakter normalizasyonu saglar.
**Eksik:** Morfolojik analiz, stemming, lemmatization yok.

#### 2.2.2 Intent Pattern Sistemi

**Konum:** `core/language/intent/patterns.py`

- 17 intent kategorisi
- ~500+ Turkce pattern
- Keyword-based matching
- Confidence scoring

**Ornek Pattern'ler:**
```python
IntentCategory.GREETING: [
    "merhaba", "selam", "selamlar", "gunaydin",
    "iyi gunler", "iyi aksamslar", "hey", "hi"
]

IntentCategory.EXPRESS_NEGATIVE: [
    "kotuyum", "kotu hissediyorum", "berbat",
    "uzgunum", "mutsuzum", "kafam karisik"
]
```

**Deger:** Temel intent tanima calisir.
**Eksik:**
- Morfolojik varyantlar ("merhaba" vs "merhabalar" vs "merhabalasalim")
- Ek cozumlemesi ("gidiyorum" vs "gittigimde" vs "gidebilir miydim")
- Belirsiz ifadeler (%15 unknown rate)

#### 2.2.3 Construction Grammar

**Konum:** `core/language/construction/mvcs.py`

- 3 katmanli grammar (Deep, Middle, Surface)
- MVCS (Meaning-Values-Constructions-Syntax) yapisi
- 9 aktif construction kategorisi:
  - GREET_CASUAL
  - THANKS_SIMPLE
  - EMPATHIZE_BASIC
  - RESPOND_WELLBEING
  - ACKNOWLEDGE_DISAGREEMENT
  - vb.

**Deger:** Yapilandirmali yanit uretimi.
**Eksik:**
- Dinamik construction olusturma
- Morfolojik uyum (isim-sifat-fiil uyumu)
- Sozluk tabanli kelime secimi

### 2.3 Performans Metrikleri (Son Test)

```
Episode Analysis (150 episode):
- Unknown Intent Rate: %15 (hedef: <%5)
- Express_Negative Feedback: 0.50 (hedef: >0.50)
- Construction Average Score: 0.928
- Positive Feedback Rate: %100
```

---

## 3. Tespit Edilen Eksiklikler ve Sorunlar

### 3.1 Kritik Eksiklikler

#### E1: Morfolojik Analiz Eksikligi

**Sorun:** Turkce eklemeli (agglutinative) bir dildir. Bir kelimeye eklenen ekler, anlami tamamen degistirebilir.

**Ornek:**
```
"gel" (kok)
"geliyor" (simdiki zaman)
"gelmeyecektim" (gelecek zaman + olumsuz + gecmis)
"gelememistik" (yeterlilik + olumsuz + gecmis)
```

**Etki:** Mevcut pattern matching sistemi sadece sabit stringleri eslestirebilir, ekleri cozumleyemez.

**Cozum:** Zeyrek/Zemberek entegrasyonu

#### E2: Kelime Koku (Stemming) Eksikligi

**Sorun:** Kelimelerin koklerine erisilemiyor.

**Ornek:**
```
"kitaplarimdan" --> kok: "kitap"
"okuyabileceklerini" --> kok: "oku"
"anlasilabilirlik" --> kok: "anla"
```

**Etki:** Pattern varyantlari manuel olarak eklenmek zorunda.

**Cozum:** Turkish Stemmer veya Lemmatizer kullanimi

#### E3: Sozluk/TDK Entegrasyonu Eksikligi

**Sorun:** Kelimelerin anlami, turu (isim, sifat, fiil), mecaz anlami, ornek cumleleri sistemde yok.

**Ornek TDK Verisi:**
```json
{
  "kelime": "yardim",
  "tur": "isim",
  "anlamlar": [
    {
      "anlam": "Kendi gucunu ve imkanlarini baskasinin iyiligi icin kullanma",
      "ornek": "Yardima gelen olmadi.",
      "mecaz": false
    }
  ],
  "atasozleri": ["El elden ustundur."]
}
```

**Etki:** Kelime secimi ve anlam kontrolu yapilamiyor.

**Cozum:** TDK API wrapper + local cache

#### E4: Turkce Corpus Yetersizligi

**Sorun:** Ogrenme icin yeterli Turkce veri yok.

**Mevcut Durum:**
- 150 episode (temiz veri)
- 379 episode (backup dahil)
- Sinirli senaryo cesitliligi

**Hedef:**
- 10.000+ episode
- 50+ senaryo kategorisi
- Dogal konusma ornekleri

**Cozum:** TS Corpus, TQuAD, ITU datasets entegrasyonu

### 3.2 Orta Oncelikli Eksiklikler

#### E5: Dilsel Dikkat Mekanizmasi

**Mevcut Durum:** Genel "spotlight" dikkat modeli (`meta/consciousness/attention.py`)
- Target-based focus
- Priority queue
- Decay mekanizmasi

**Eksik:** Token-level linguistic attention
- Hangi kelimeye odaklanildi?
- Baglamsal onem agirliklarí
- Cross-attention (kullanici cumle <-> yanit cumle)

#### E6: Cumle Yapisi Analizi

**Sorun:** Turkce cumle yapisi (SOV - Ozne-Nesne-Yuklem) analiz edilmiyor.

**Ornek:**
```
"Ben kitabi okudum." --> S: Ben, O: kitabi, V: okudum
"Kitabi ben okudum." --> O: Kitabi, S: ben, V: okudum (vurgu farki)
```

#### E7: Ses Uyumu Kontrolu

**Sorun:** Turkce eklerin ses uyumu kontrol edilmiyor.

**Ornek:**
```
"kitap" + "-ler" = "kitaplar" (kalin unlu uyumu)
"ev" + "-ler" = "evler" (ince unlu uyumu)
"kitap" + "-lar" = YANLIS
```

### 3.3 Dusuk Oncelikli Eksiklikler

| # | Eksik | Aciklama |
|---|-------|----------|
| E8 | Lehce Destegi | Anadolu agizlari, Istanbul Turkcesi farklari |
| E9 | Argo/Slang | Gunluk konusma dili |
| E10 | Emoji/Emoticon | Duygu ifadesi yorumlama |
| E11 | Kod-Karıştırma | Turkce-Ingilizce karisik metinler |

---

## 4. Gelistirme Fazlari ve Onerileri

### Faz 6: Turkce Morfoloji Temeli

**Sure Tahmini:** 2-3 hafta
**Oncelik:** Kritik

#### 6.1 Zeyrek Entegrasyonu

**Hedef:** Turkce morfolojik analiz ve lemmatizasyon

**Kurulum:**
```bash
pip install zeyrek
```

**Kod Ornegi:**
```python
from zeyrek import MorphAnalyzer

analyzer = MorphAnalyzer()

# Analiz
results = analyzer.analyze("gidiyorum")
# [Parse(word='gidiyorum', lemma='git', pos='Verb', ...)]

# Lemmatizasyon
lemmas = analyzer.lemmatize("kitaplarimdan")
# ['kitap']
```

**Entegrasyon Noktalari:**

1. **IntentRecognizer'a Ekleme:**
```python
# core/language/intent/recognizer.py

from zeyrek import MorphAnalyzer

class IntentRecognizer:
    def __init__(self):
        self.morph = MorphAnalyzer()

    def _normalize(self, text: str) -> str:
        # Mevcut normalizasyon
        normalized = normalize_turkish(text)

        # Lemmatizasyon ekle
        words = normalized.split()
        lemmatized = []
        for word in words:
            lemmas = self.morph.lemmatize(word)
            lemmatized.append(lemmas[0] if lemmas else word)

        return ' '.join(lemmatized)
```

2. **Yeni Modul: `core/language/morphology/`**
```
core/language/morphology/
├── __init__.py
├── analyzer.py      # Zeyrek wrapper
├── stemmer.py       # Kok cikarma
├── suffix.py        # Ek analizi
└── harmony.py       # Ses uyumu kontrolu
```

#### 6.2 Alt Gorevler

| # | Gorev | Detay | Durum |
|---|-------|-------|-------|
| 6.1.1 | Zeyrek kurulumu | pip install, test | Bekliyor |
| 6.1.2 | MorphologyAnalyzer sinifi | Wrapper olustur | Bekliyor |
| 6.1.3 | IntentRecognizer entegrasyonu | Lemmatization ekleme | Bekliyor |
| 6.1.4 | Pattern cache guncelleme | Lemmatized patterns | Bekliyor |
| 6.1.5 | Unit testler | 50+ test | Bekliyor |
| 6.1.6 | Performance benchmark | Latency olcumu | Bekliyor |

#### 6.3 Potansiyel Sorunlar ve Onlemler

| Sorun | Risk | Onlem |
|-------|------|-------|
| Zeyrek performansi | Orta | Lazy loading + cache |
| Belirsiz lemma | Dusuk | En yaygin lemma sec |
| Ozel isimler | Orta | NER ile filtrele |
| Bellek kullanimi | Dusuk | Model lazy load |

---

### Faz 7: TDK Sozluk Entegrasyonu

**Sure Tahmini:** 2-3 hafta
**Oncelik:** Yuksek

#### 7.1 TDK API Analizi

**Durum:** TDK'nin resmi public REST API'si bulunmuyor.

**Alternatif Cozumler:**

1. **tdk-service (GitHub):** sozluk.gov.tr scraping + DynamoDB cache
2. **NPM tdk paketleri:** Node.js wrapper'lar
3. **Kendi API wrapper'imiz:** sozluk.gov.tr'den veri cekme

**Onerilen Yaklasim:** Hibrit sistem

```
[UEM] --> [Local SQLite Cache] --> Varsa don
                |
                v (yoksa)
         [TDK Scraper] --> [sozluk.gov.tr]
                |
                v
         [Cache'e kaydet] --> [Response don]
```

#### 7.2 TDK Veri Yapisi

TDK sozluk.gov.tr'den alinan veri formati:

```json
{
  "madde": "yardim",
  "koken": "Turkce",
  "lisan": "Turkce",
  "telaffuz": "",
  "anlamlarListe": [
    {
      "anlam": "Kendi gucunu ve imkanlarini baskasinin iyiligi icin kullanma, muavenet",
      "ozelliklerListe": [
        {"tur": "isim", "tam_adi": "isim"}
      ],
      "orneklerListe": [
        {"ornek": "Yardima gelen olmadi."}
      ]
    },
    {
      "anlam": "Bir ise veya bir kimseye katkida bulunma",
      "fipipiil": "",
      "orneklerListe": [
        {"ornek": "Onun yardimi olmadan bu kadar kisa surede bitiremezdik."}
      ]
    }
  ],
  "birlesikler": "yardim eli, yardim etmek, yardim sandigi",
  "atasozu": [
    {"madde": "El elden ustundur"}
  ]
}
```

#### 7.3 Modul Yapisi

```
core/language/dictionary/
├── __init__.py
├── tdk_client.py      # TDK API/Scraper client
├── cache.py           # SQLite cache layer
├── models.py          # Veri modelleri
├── enricher.py        # Kelime zenginlestirme
└── examples.py        # Ornek cumle yonetimi
```

#### 7.4 Kullanim Alanlari

| Alan | Kullanim | Fayda |
|------|----------|-------|
| Intent Tanima | Kelime tur kontrolu | Daha dogru eslestirme |
| Construction | Ornek cumle sablonlari | Dogal yanitlar |
| Risk Scoring | Kaba kelime kontrolu | Guvenlik |
| Learning | Anlam tabanlí ogrenme | Generalizasyon |

#### 7.5 Ornek Cumle Entegrasyonu

TDK sozlukte her anlam icin ornek cumleler var. Bu ornek cumleler:

**Faydalar:**
- Dogal Turkce cumle yapisi ogrenme
- Construction template'i olarak kullanma
- Semantic similarity icin referans

**Ornek Kullanim:**
```python
# Construction olusturmada TDK ornegi kullan
tdk_data = tdk_client.get_word("yardim")
example = tdk_data.anlamlar[0].ornekler[0]
# "Yardima gelen olmadi."

# Template olarak kullan
template = example.replace("gelen olmadi", "{durum}")
# "Yardima {durum}."
```

---

### Faz 8: Turkce Corpus Genisletme

**Sure Tahmini:** 3-4 hafta
**Oncelik:** Orta-Yuksek

#### 8.1 Mevcut Durum

```
data/
├── episodes.jsonl        # 150 episode (aktif)
├── episodes_backup_pre_fix.jsonl  # 379 episode (backup)
└── construction_stats.json        # 9 construction istatistik
```

#### 8.2 Hedef Veri Seti

| Kaynak | Tur | Miktar | Oncelik |
|--------|-----|--------|---------|
| Manuel Episode | Senaryo | 5.000+ | Yuksek |
| TS Corpus | Genel Turkce | 10.000+ cumle | Orta |
| TQuAD | Soru-Cevap | 7.000+ | Orta |
| ITU Datasets | NER, POS | 5.000+ | Dusuk |
| TDK Ornekleri | Sozluk | 50.000+ | Yuksek |

#### 8.3 Veri Formati Standartlasma

**Onerilen Format (JSONL):**
```json
{
  "id": "ep_001",
  "source": "manual|ts_corpus|tquad|tdk",
  "input": "Bugun cok yorgunum.",
  "input_lemmatized": "bugun cok yorgun",
  "intent": "express_negative",
  "entities": [
    {"text": "bugun", "type": "TIME"},
    {"text": "yorgun", "type": "EMOTION"}
  ],
  "expected_acts": ["empathize", "ask"],
  "example_response": "Anliyorum, zor bir gun gecirmissin.",
  "metadata": {
    "domain": "wellbeing",
    "formality": 0.5,
    "emotional_valence": -0.6
  }
}
```

#### 8.4 Veri Toplama Stratejisi

**Faz 8.1: Manuel Genisletme**
- Edge case'ler (hmm, ?, belirsiz ifadeler)
- Duygu ifadeleri varyantlari
- Cok turlu yanıtlar

**Faz 8.2: TDK Ornek Cumleler**
- Sozluk orneklerini cek
- Intent/Entity etiketle
- Construction template'i olarak isle

**Faz 8.3: Acik Kaynak Corpus**
- TS Corpus'tan secim
- Kalite filtresi uygula
- Manuel etiketleme

#### 8.5 Dosya/DOCX Kullanimi Analizi

**Soru:** Turkce metinler iceren .txt, .docx dosyalari kullanilabilir mi?

**Analiz:**

| Format | Avantaj | Dezavantaj | Oneri |
|--------|---------|------------|-------|
| .txt | Basit, hizli okuma | Formatlama yok | Duz metin icin uygun |
| .docx | Zengin format | python-docx gerektir | Akademik metinler icin |
| .pdf | Yaygin | Parsing zor | Oncelikli degil |
| .json/.jsonl | Yapilandirilmis | Manuel hazirlik | En iyi secim |

**Sonuc:** .docx dosyalari FAYDALI OLABILIR ancak:
1. Yapilandirilmis veri (JSONL) oncelikli olmali
2. .docx icerik cikarma icin python-docx kullanimi gerekli
3. NLP preprocessing (tokenization, POS tagging) sonrasi kullanilmali

**Kod Ornegi:**
```python
from docx import Document

def extract_turkish_sentences(docx_path: str) -> list[str]:
    doc = Document(docx_path)
    sentences = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            # Cumle ayirma
            sents = text.split('.')
            sentences.extend([s.strip() for s in sents if s.strip()])
    return sentences
```

---

### Faz 9: Dilsel Dikkat Mekanizmasi

**Sure Tahmini:** 4-5 hafta
**Oncelik:** Orta

#### 9.1 Mevcut Dikkat Sistemi Analizi

**Konum:** `meta/consciousness/attention.py`

**Mevcut Ozellikler:**
- Spotlight metaforu (odaklanma)
- Priority-based focus
- Decay mekanizmasi
- Divided attention (bolunmus dikkat)
- Inhibition (engelleme)

**Mevcut Sinirliliklar:**
- Genel amacli (dil-agnostik)
- Token/kelime seviyesinde dikkat yok
- Cross-attention yok

#### 9.2 Dilsel Dikkat Onerileri

**Seviye 1: Token-Level Attention (Basit)**

```python
@dataclass
class TokenAttention:
    token: str
    lemma: str
    attention_weight: float  # 0.0 - 1.0
    reason: str  # Neden onemli?

class LinguisticAttention:
    def compute_attention(self, tokens: List[str]) -> List[TokenAttention]:
        """
        Her token icin dikkat agirligini hesapla.

        Faktorler:
        - Intent keywords (yuksek)
        - Named entities (yuksek)
        - Sentiment words (orta)
        - Function words (dusuk)
        """
        pass
```

**Seviye 2: Self-Attention (Orta)**

```python
def self_attention(tokens: List[str], embeddings: np.ndarray) -> np.ndarray:
    """
    Token'lar arasi iliski matrisi.

    Ornek: "Ben kitabi okudum"

    Attention Matrix:
              Ben   kitabi  okudum
    Ben       1.0    0.2     0.8
    kitabi    0.2    1.0     0.9
    okudum    0.8    0.9     1.0

    "okudum" -> "Ben" (ozne iliskisi)
    "okudum" -> "kitabi" (nesne iliskisi)
    """
    # Q, K, V hesapla
    Q = embeddings @ W_q
    K = embeddings @ W_k
    V = embeddings @ W_v

    # Attention scores
    scores = Q @ K.T / sqrt(d_k)
    attention = softmax(scores)

    return attention @ V
```

**Seviye 3: Cross-Attention (Ileri)**

```python
def cross_attention(
    user_tokens: List[str],
    response_tokens: List[str]
) -> np.ndarray:
    """
    Kullanici girisi <-> Yanit arasinda cross-attention.

    Ornek:
    User: "Bugun cok yorgunum"
    Response: "Anliyorum, zor bir gun gecirmissin"

    Cross-Attention:
                    Anliyorum  zor  bir  gun  gecirmissin
    Bugun             0.1     0.2  0.1  0.9     0.3
    cok               0.1     0.8  0.1  0.1     0.2
    yorgunum          0.7     0.6  0.1  0.2     0.8

    "yorgunum" -> "Anliyorum" (empati iliskisi)
    "Bugun" -> "gun" (zaman iliskisi)
    """
    pass
```

#### 9.3 Dikkat Mekanizmasi Degerlendirmesi

**Soru:** Dikkat mekanizmasi UEM icin isimize yarar mi?

**Analiz:**

| Ozellik | Mevcut (Spotlight) | Onerilen (Linguistic) | Fayda |
|---------|-------------------|----------------------|-------|
| Odaklanma | Genel target | Token/kelime | Daha hassas |
| Performans | Hizli | Orta (attention hesabi) | Kabul edilebilir |
| Karmasiklik | Dusuk | Orta-Yuksek | Artirilmis |
| Ogrenme | Yok | Attention weights | Onemli |

**Sonuc:** EVET, dilsel dikkat mekanizmasi FAYDALI olacaktir cunku:

1. **Intent Tanima:** Anahtar kelimelere odaklanma
2. **Empati:** Duygu kelimelerine dikkat
3. **Context Understanding:** Cumle icindeki iliskiler
4. **Response Generation:** Hangi girdi kelimesine yanit verildi?

**Ancak:**
- Ilk asamada (Faz 6-8) temel morfoloji ve TDK oncelikli
- Dikkat mekanizmasi Faz 9+ icin planlanmali
- Basit token attention ile baslanmali

#### 9.4 Entegrasyon Plani

```
Mevcut:
meta/consciousness/attention.py (spotlight)

Onerilen:
core/language/attention/
├── __init__.py
├── token_attention.py     # Token-level weights
├── self_attention.py      # Intra-sentence
├── cross_attention.py     # Input-output
└── integration.py         # Pipeline entegrasyonu
```

---

### Faz 10: Gelismis Turkce Ozellikleri

**Sure Tahmini:** 4-6 hafta
**Oncelik:** Dusuk-Orta

#### 10.1 Cumle Yapisi Analizi (SOV)

```python
from enum import Enum

class SentenceRole(Enum):
    SUBJECT = "ozne"      # Kim/Ne?
    OBJECT = "nesne"      # Kimi/Neyi?
    VERB = "yuklem"       # Ne yapiyor?
    ADVERB = "zarf"       # Nasil/Ne zaman?
    ADJECTIVE = "sifat"   # Nasil bir?

def parse_turkish_sentence(sentence: str) -> Dict[SentenceRole, str]:
    """
    Turkce cumle yapisini analiz et.

    Ornek: "Ben bugun guzel bir kitap okudum"

    {
        SUBJECT: "Ben",
        OBJECT: "kitap",
        VERB: "okudum",
        ADVERB: "bugun",
        ADJECTIVE: "guzel bir"
    }
    """
    pass
```

#### 10.2 Ses Uyumu Kontrolu

```python
def check_vowel_harmony(word: str, suffix: str) -> bool:
    """
    Turkce ses uyumu kontrolu.

    Buyuk unlu uyumu:
    - Kalin unlulər (a, i, o, u) --> kalin ek
    - Ince unlulər (e, i, o, u) --> ince ek

    Kucuk unlu uyumu:
    - Duz unlulər (a, e, i, i) --> duz ek
    - Yuvarlak unlulər (o, o, u, u) --> yuvarlak ek
    """
    back_vowels = set('aiou')
    front_vowels = set('eiou')

    # Son unluyu bul
    last_vowel = None
    for char in reversed(word):
        if char in back_vowels | front_vowels:
            last_vowel = char
            break

    if last_vowel is None:
        return True  # Unlu yok, uyum kontrolu yapilamaz

    # Ek uyumunu kontrol et
    suffix_vowel = None
    for char in suffix:
        if char in back_vowels | front_vowels:
            suffix_vowel = char
            break

    if suffix_vowel is None:
        return True

    # Uyum kontrolu
    if last_vowel in back_vowels:
        return suffix_vowel in back_vowels
    else:
        return suffix_vowel in front_vowels
```

#### 10.3 Argo/Slang Destegi

| Terim | Anlam | Kayit |
|-------|-------|-------|
| efsane | cok iyi | pozitif |
| cok fena | cok iyi (ironi) | pozitif |
| sallamak | yalan soylemek | negatif |
| tasmak | cok guzel | pozitif |

---

## 5. TDK ve Turkce Sozluk Entegrasyonu

### 5.1 TDK Kaynaklari

**Resmi Siteler:**
- [TDK Ana Sayfa](https://tdk.gov.tr/)
- [Guncel Turkce Sozluk](https://sozluk.gov.tr/)

**TDK Sozluk Icerigi:**
- Guncel Turkce Sozluk
- Atasozleri ve Deyimler Sozlugu
- Bilim ve Sanat Terimleri Sozlugu
- Turkce Kokenli Kelimeler Sozlugu
- Bati Kokenli Kelimeler Sozlugu

### 5.2 API Durumu

**Resmi API:** Mevcut DEGIL

TDK'nin resmi bir public REST API'si bulunmuyor. Ancak:
- MEB ile protokol kapsaminda web servisi var
- Ucuncu parti projeler scraping ile veri cekmektedir

### 5.3 Ucuncu Parti Cozumler

| Proje | Platform | Aciklama |
|-------|----------|----------|
| [tdk-service](https://github.com/abdurrahmanekr/tdk-service) | GitHub | Node.js, DynamoDB cache |
| NPM tdk paketleri | NPM | Cesitli wrapper'lar |
| Python TDK scraper | GitHub | Python ile veri cekme |

### 5.4 Onerilen Entegrasyon Mimarisi

```
                    +----------------+
                    |   UEM System   |
                    +-------+--------+
                            |
                    +-------v--------+
                    | TDKClient      |
                    | (core/lang/    |
                    |  dictionary/)  |
                    +-------+--------+
                            |
              +-------------+-------------+
              |                           |
      +-------v--------+         +--------v-------+
      | SQLite Cache   |         | TDK Scraper    |
      | (local DB)     |         | (sozluk.gov.tr)|
      +----------------+         +----------------+
```

**Akis:**
1. Kelime istegi al
2. SQLite cache'de ara
3. Varsa cache'den don
4. Yoksa sozluk.gov.tr'ye istek at
5. HTML parse et
6. Cache'e kaydet
7. Sonucu don

### 5.5 TDK Veri Kullanim Alanlari

| Kullanim | Veri | Ornek |
|----------|------|-------|
| Kelime turu | tur: "isim", "sifat", "fiil" | "yardim" -> isim |
| Anlam kontrolu | anlam listesi | Cok anlamli kelimeler |
| Ornek cumle | orneklerListe | Construction template |
| Kok bilgisi | koken: "Turkce", "Arapca" | Etymoloji |
| Atasozleri | atasozu listesi | Kultur referanslari |
| Birlesiksoz | birlesikler | Kelime gruplari |

### 5.6 Faydali Olup Olmayacagi Analizi

**SONUC: EVET, TDK entegrasyonu cok FAYDALI olacaktir.**

**Faydalar:**
1. **Kelime dogrulama:** Gercek Turkce kelime mi?
2. **Tur belirleme:** Intent siniflandirma icin
3. **Anlam zenginligi:** Cok anlamli kelimeler
4. **Ornek cumleler:** Dogal yapi ogrenme
5. **Kulturel bagslam:** Atasozleri, deyimler

**Riskler ve Cozumler:**
| Risk | Etki | Cozum |
|------|------|-------|
| Rate limiting | Orta | Local cache kullan |
| Site degisikligi | Yuksek | Versiyon kontrolu |
| HTML parsing hatasi | Orta | Robust parser |
| Eksik veri | Dusuk | Fallback mekanizmasi |

---

## 6. Turkce Metin Kaynaklari ve Veri Setleri

### 6.1 Acik Kaynak Turkce NLP Veri Setleri

| Kaynak | Tur | Boyut | URL |
|--------|-----|-------|-----|
| TS Corpus | Genel | 400M+ token | [tscorpus.com](https://tscorpus.com/) |
| TQuAD | Soru-Cevap | 7K+ | [GitHub](https://github.com/TQuad/turkish-nlp-qa-dataset) |
| ITU NLP | Cesitli | Degisken | [ITU](http://ddi.itu.edu.tr/en/toolsandresources) |
| UD Turkish | Treebank | 9.7K cumle | Universal Dependencies |
| NLI-TR | NLI | 550K+ | Bogazici TABI |
| MASSIVE | Intent | 1M | Amazon |

### 6.2 Turkce NLP Kutuphaneleri

| Kutuphane | Dil | Ozellik | URL |
|-----------|-----|---------|-----|
| Zeyrek | Python | Morfoloji, Lemma | [PyPI](https://pypi.org/project/zeyrek/) |
| Zemberek-NLP | Java | Kapsamli NLP | [GitHub](https://github.com/ahmetaa/zemberek-nlp) |
| turkish-stemmer | Python | Stemming | [GitHub](https://github.com/otuncelli/turkish-stemmer-python) |
| VNLP | Python | Modern NLP | [GitHub](https://github.com/vngrs-ai/vnlp) |

### 6.3 Dosya Formatlari Analizi

#### .txt Dosyalari

**Avantajlar:**
- Basit okuma
- Hizli isleme
- Evrensel uyumluluk

**Dezavantajlar:**
- Yapı bilgisi yok
- Metadata yok

**Kullanim:**
```python
with open('turkish_text.txt', 'r', encoding='utf-8') as f:
    text = f.read()
```

#### .docx Dosyalari

**Avantajlar:**
- Zengin formatlama
- Paragraf yapisi
- Akademik kaynaklar

**Dezavantajlar:**
- python-docx gerektir
- Parsing karmasikligi

**Kullanim:**
```python
from docx import Document

doc = Document('turkish_document.docx')
for para in doc.paragraphs:
    print(para.text)
```

**Kurulum:**
```bash
pip install python-docx
```

#### .json/.jsonl Dosyalari

**Avantajlar:**
- Yapilandirilmis veri
- Metadata destegi
- NLP pipeline uyumlu

**Dezavantajlar:**
- Manuel hazirlık
- Boyut artisi

**Oneri:** UEM icin .jsonl TERCIH EDILMELI

### 6.4 Veri Toplama Stratejisi

```
Faz 8 Veri Toplama:

1. Manuel Episode Genisletme
   ├── Edge cases (hmm, ?, ...)
   ├── Duygu varyantlari
   └── Cok turlu yanitlar

2. TDK Ornek Cumleler
   ├── API ile cek
   ├── Intent etiketle
   └── Construction template olarak kullan

3. TS Corpus Secimi
   ├── Kategori filtresi
   ├── Kalite kontrolu
   └── Manuel etiketleme

4. Dosya Kaynaklari
   ├── .txt metin arslivi
   ├── .docx akademik metinler
   └── Web scraping (etik sinirlar icinde)
```

---

## 7. Dikkat Mekanizmasi Degerlendirmesi

### 7.1 Mevcut Sistem

**Dosya:** `meta/consciousness/attention.py`

**Ozellikler:**
- AttentionController sinifi
- Spotlight metaforu
- Focus, divide, sustain operasyonlari
- Priority queue
- Decay mekanizmasi
- Inhibition (engelleme)

**Kod Ornegi (Mevcut):**
```python
class AttentionController:
    def focus_on(
        self,
        target_type: str,      # Genel hedef turu
        target_id: str,        # Hedef ID
        priority: AttentionPriority,
        duration_ms: float,
    ) -> AttentionFocus:
        # Spotlight focus
        pass
```

### 7.2 Transformer Dikkat Mekanizmasi

**Kaynak:** "Attention Is All You Need" (Vaswani et al., 2017)

**Temel Konseptler:**
- Query (Q): Ne ariyorum?
- Key (K): Nerede bulabilirim?
- Value (V): Ne aldim?

**Formul:**
```
Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V
```

**Turkce Dil Icin Faydalar:**

1. **Uzun mesafe baglanti:** "Ben dun aksam eve giderken yagmurda islandim"
   - "Ben" ile "islandim" arasindaki iliski

2. **Morfolojik iliskiler:** "kitaplarimdan"
   - Kok ve eklerin birlikte islenmesi

3. **Baglamsal anlam:** "Banka"
   - Oturulan yer mi? Para kurulusu mu?

### 7.3 UEM Icin Uygunluk Degerlendirmesi

| Kriter | Mevcut (Spotlight) | Transformer-style | Karar |
|--------|-------------------|-------------------|-------|
| Hiz | Hizli | Orta | Spotlight+ |
| Bellek | Dusuk | Yuksek | Spotlight+ |
| Anlama | Temel | Gelismis | Transformer |
| Uygulama | Kolay | Zor | Spotlight+ |
| Ogrenme | Yok | Var | Transformer |

**Sonuc: HIBRIT YAKLASIM**

1. **Kisa vadeli (Faz 6-8):** Mevcut spotlight + token weights
2. **Orta vadeli (Faz 9):** Self-attention katmani ekle
3. **Uzun vadeli (Faz 10+):** Full transformer attention

### 7.4 Onerilen Hibrit Mimari

```
             User Input
                  |
                  v
        +-------------------+
        | Token Attention   |  <-- Yeni (Faz 9)
        | (kelime agirlik)  |
        +-------------------+
                  |
                  v
        +-------------------+
        | Spotlight Attention| <-- Mevcut
        | (genel odak)      |
        +-------------------+
                  |
                  v
        +-------------------+
        | Self-Attention    |  <-- Yeni (Faz 10)
        | (iliskiler)       |
        +-------------------+
                  |
                  v
            Processing
```

---

## 8. Risk Analizi ve Onlemler

### 8.1 Teknik Riskler

| Risk | Olasilik | Etki | Onlem |
|------|----------|------|-------|
| Zeyrek performans sorunu | Orta | Orta | Lazy loading, cache |
| TDK site degisikligi | Yuksek | Yuksek | Versiyon kontrolu, alternatif kaynak |
| Bellek yetersizligi | Dusuk | Yuksek | Model optimizasyonu |
| Veri kalitesi sorunu | Orta | Orta | Validation pipeline |
| Entegrasyon uyumsuzlugu | Dusuk | Orta | Modular design |

### 8.2 Operasyonel Riskler

| Risk | Olasilik | Etki | Onlem |
|------|----------|------|-------|
| Proje karmasikligi | Orta | Orta | Fazli yaklasim |
| Kaynak yetersizligi | Dusuk | Orta | Onceliklendirme |
| Bagimlılik sorunları | Orta | Dusuk | Version pinning |
| Test yetersizligi | Dusuk | Orta | %80+ coverage hedefi |

### 8.3 Dilsel Riskler

| Risk | Olasilik | Etki | Onlem |
|------|----------|------|-------|
| Yanlis lemmatization | Orta | Orta | En yaygin lemma sec |
| Belirsiz anlam | Yuksek | Dusuk | Context kullan |
| Lehce farkliliklari | Dusuk | Dusuk | Standart Turkce odak |
| Argo/slang hatasi | Orta | Dusuk | Fallback mekanizmasi |

### 8.4 Onlem Matrisi

```
Risk Onlem Sureci:

1. ONLEME (Proactive)
   ├── Modular design
   ├── Kapsamli testler
   └── Dokumantasyon

2. TESPIT (Detection)
   ├── Monitoring
   ├── Logging
   └── Alerting

3. MUDAHALE (Response)
   ├── Fallback mekanizmalar
   ├── Graceful degradation
   └── Hotfix proseduru

4. IYILESTIRME (Recovery)
   ├── Rollback yeteneği
   ├── Data backup
   └── Post-mortem analiz
```

---

## 9. Uygulama Yol Haritasi

### 9.1 Zaman Cizelgesi

```
2025 Q4 (Aralik):
├── Faz 5.1: Intent pattern genisletme ✅
├── Faz 5.2: Empathy construction'lari ✅
└── Faz 5.3: Episode temizligi ✅

2026 Q1 (Ocak-Mart):
├── Faz 6: Turkce Morfoloji Temeli
│   ├── 6.1: Zeyrek kurulumu (Hafta 1)
│   ├── 6.2: MorphologyAnalyzer (Hafta 2)
│   ├── 6.3: Intent entegrasyonu (Hafta 3)
│   └── 6.4: Testler (Hafta 4)
│
├── Faz 7: TDK Entegrasyonu
│   ├── 7.1: TDK scraper (Hafta 5-6)
│   ├── 7.2: SQLite cache (Hafta 7)
│   ├── 7.3: Pipeline entegrasyonu (Hafta 8)
│   └── 7.4: Testler (Hafta 9)
│
└── Faz 8: Corpus Genisletme
    ├── 8.1: Manuel episode (Hafta 10-11)
    ├── 8.2: TDK ornekleri (Hafta 12)
    └── 8.3: Acik kaynak veri (Hafta 13-14)

2026 Q2 (Nisan-Haziran):
├── Faz 9: Dilsel Dikkat
│   ├── 9.1: Token attention (Hafta 15-17)
│   ├── 9.2: Self-attention (Hafta 18-20)
│   └── 9.3: Entegrasyon (Hafta 21-22)
│
└── Faz 10: Gelismis Ozellikler
    ├── 10.1: SOV analizi
    ├── 10.2: Ses uyumu
    └── 10.3: Argo destegi
```

### 9.2 Oncelik Matrisi

```
                    YUKSEK ETKI
                         |
    Faz 6 (Morfoloji)    |    Faz 7 (TDK)
    ★★★★★               |    ★★★★☆
                         |
DUSUK -------------------|------------------- YUKSEK
CABA                     |                    CABA
                         |
    Faz 8 (Corpus)       |    Faz 9 (Attention)
    ★★★☆☆               |    ★★☆☆☆
                         |
                    DUSUK ETKI
```

### 9.3 Bagimlilík Grafi

```
Faz 5 (Mevcut) ──────┐
                     │
                     v
              ┌─────────────┐
              │   Faz 6     │
              │ (Morfoloji) │
              └──────┬──────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
         v           v           v
    ┌────────┐  ┌────────┐  ┌────────┐
    │ Faz 7  │  │ Faz 8  │  │ Faz 9  │
    │ (TDK)  │  │(Corpus)│  │(Dikkat)│
    └────┬───┘  └────┬───┘  └────┬───┘
         │           │           │
         └───────────┼───────────┘
                     │
                     v
              ┌─────────────┐
              │   Faz 10    │
              │ (Gelismis)  │
              └─────────────┘
```

---

## 10. Sonuc ve Oneriler

### 10.1 Kritik Eylemler

1. **Hemen Yapilmali:**
   - Zeyrek kutuphanesini projede test et
   - TDK scraper prototipi olustur
   - Morfoloji modul yapısını tasarla

2. **Kisa Vadede:**
   - Faz 6'yi baslar (2026 Q1)
   - 500+ yeni episode uret
   - Morfoloji testlerini yaz

3. **Orta Vadede:**
   - TDK entegrasyonunu tamamla
   - 10.000+ episode hedefini ger lestir
   - Dilsel dikkat mekanizmasını ekle

### 10.2 Basari Kriterleri

| Metrik | Mevcut | Hedef (Q1 2026) | Hedef (Q2 2026) |
|--------|--------|-----------------|-----------------|
| Unknown Intent | %15 | <%5 | <%3 |
| Express_Negative Feedback | 0.50 | >0.60 | >0.70 |
| Morfolojik Coverage | %0 | >%80 | >%95 |
| TDK Kelime Cache | 0 | 10.000+ | 50.000+ |
| Episode Sayisi | 150 | 5.000+ | 15.000+ |

### 10.3 Sonuc

UEM v2, sagslam bir temel uzerine kurulmustur. Turkce dil ogrenme yeteneklerini gelistirmek icin:

1. **Morfolojik analiz ZORUNLUDUR** - Turkce eklemeli dil yapisi nedeniyle
2. **TDK entegrasyonu YUKSEK DEGERLIDIR** - Anlam zenginligi ve ornekler icin
3. **Dikkat mekanizmasi FAYDALIDIR** - Ancak temel (Faz 6-8) sonrası oncelikli
4. **Veri genisletme GEREKLIDIR** - Ogrenme icin yeterli ornek lazim

Bu rapor, projenin gelecek faslarí icin kapsamli bir yol haritasi sunmaktadir.

---

## 11. Kaynaklar

### 11.1 TDK ve Sozluk

- [TDK Ana Sayfa](https://tdk.gov.tr/)
- [Guncel Turkce Sozluk](https://sozluk.gov.tr/)
- [tdk-service GitHub](https://github.com/abdurrahmanekr/tdk-service)

### 11.2 Turkce NLP Kutuphaneleri

- [Zeyrek - Python Morfoloji](https://zeyrek.readthedocs.io/en/latest/)
- [Zemberek-NLP - Java](https://github.com/ahmetaa/zemberek-nlp)
- [Zemberek-Python-Examples](https://github.com/ozturkberkay/Zemberek-Python-Examples)
- [Turkish Stemmer Python](https://github.com/otuncelli/turkish-stemmer-python)

### 11.3 Veri Setleri

- [Turkish NLP Resources](https://github.com/agmmnn/turkish-nlp-resources)
- [TS Corpus](https://tscorpus.com/)
- [TQuAD Dataset](https://github.com/TQuad/turkish-nlp-qa-dataset)
- [ITU NLP Tools](http://ddi.itu.edu.tr/en/toolsandresources)

### 11.4 Dikkat Mekanizmasi

- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
- [Fine-tuning Transformer for Turkish](https://arxiv.org/html/2401.17396v1)
- [BERTurk](https://github.com/stefan-it/turkish-bert)

### 11.5 Akademik Kaynaklar

- Turkish Text Preprocessing with Zemberek (Medium)
- ITU Turkish NLP Treebanks (Universal Dependencies)
- Bogazici NLI-TR Dataset (TABI Lab)

---

**Rapor Sonu**

---

_Bu rapor UEM v2 projesinin Turkce dil ogrenme gelistirmesi icin hazirlanmistir._

_Proje Sahibi ve Denetleyen: Isa/Kimb0t <isakara5967@gmail.com>_

_Olusturulma Tarihi: 11 Aralik 2025_
