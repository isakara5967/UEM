# UEM v2 - VİZYON VE YOL HARİTASI

**Son Güncelleme:** 8 Aralık 2025  
**Versiyon:** 1.1  
**Durum:** Aktif

---

## 1. MEVCUT DURUM (Dürüst Değerlendirme)

### 1.1 Ne Var?

| Modül | Test | Gerçek Durum |
|-------|------|--------------|
| Perception | 49 | ⚠️ Hardcoded input, gerçek sensör yok |
| Cognition | 75 | ⚠️ Basit reasoning, sınırlı planning |
| Memory | 25 | ⚠️ CRUD var, semantic search yok |
| Affect | ~50 | ✅ PAD, empathy, sympathy, trust çalışıyor |
| Self | 88 | ⚠️ Yapı var, gerçek kullanım yok |
| Consciousness | 69 | ⚠️ GWT konsepti var, entegrasyon zayıf |
| Metamind | 65 | ⚠️ Pattern var, veri olmadan anlamsız |
| Monitoring | 29 | ✅ Dashboard çalışıyor |
| Integration | 41 | ⚠️ İzole testler |

**Toplam:** 530 test, 11 modül

### 1.2 Ne Yok? (Kritik Eksiklikler)

| # | Eksik | Önem | Durum |
|---|-------|------|-------|
| 1 | **Dil/Konuşma** | 🔴 Kritik | Hiç yok |
| 2 | **Conversation Memory** | 🔴 Kritik | Hiç yok |
| 3 | **Embedding/Semantic Search** | 🔴 Kritik | Hiç yok |
| 4 | **Context Management** | 🔴 Kritik | Hiç yok |
| 5 | **Aktif Decay/Forgetting** | 🟡 Önemli | Kod var, aktif değil |
| 6 | **Learning** | 🟡 Önemli | Hiç yok |
| 7 | **Multi-Agent** | 🟠 Sonra | Hiç yok |
| 8 | **Gerçek Sensör** | 🟠 Sonra | Hiç yok |
| 9 | **Oyun Entegrasyonu** | ⚪ Çok sonra | Hiç yok |

### 1.3 Dürüst Özet

```
UEM şu an:
  ✅ İskelet tamamlandı
  ✅ Temel modüller çalışıyor (izole)
  ✅ Unit testler geçiyor
  
  ❌ Konuşamıyor
  ❌ Gerçek senaryoda test edilmedi
  ❌ Production'a hazır değil
  
Durum: ALPHA - Sadece geliştirici için çalışır
```

---

## 2. KRİTİK EKSİKLİKLER (Detaylı)

### 2.1 Conversation Memory (YOK)

**Sorun:**
```python
# Şu an
memory.store_episode("Bob yardım etti")  # Tek cümle

# Olması gereken
memory.store_dialogue([
    {"role": "user", "content": "Merhaba"},
    {"role": "agent", "content": "Merhaba!"},
    {"role": "user", "content": "Nasılsın?"},
    {"role": "agent", "content": "İyiyim, teşekkürler"},
])
```

**Neden Kritik:** Sohbet geçmişi olmadan dil entegrasyonu imkansız.

**Çözüm:**
```python
@dataclass
class DialogueTurn:
    role: str                    # "user" | "agent"
    content: str                 # Mesaj
    timestamp: datetime          # Ne zaman
    emotion: Optional[PADState]  # Duygu durumu
    intent: Optional[str]        # Niyet (soru, rica, bilgi)
    topic: Optional[str]         # Konu

class ConversationMemory:
    def add_turn(self, turn: DialogueTurn) -> None
    def get_recent(self, n: int = 10) -> List[DialogueTurn]
    def get_by_topic(self, topic: str) -> List[DialogueTurn]
    def get_by_date(self, start: datetime, end: datetime) -> List[DialogueTurn]
    def count_turns(self) -> int
```

**Dosyalar:**
- [ ] `core/memory/conversation.py`
- [ ] `core/memory/persistence/conversation_repo.py`
- [ ] `sql/conversation_schema.sql`
- [ ] `tests/unit/test_conversation_memory.py`

---

### 2.2 Embedding/Semantic Search (YOK)

**Sorun:**
```python
# Şu an
memory.recall_episodes(agent_id="bob")  # ID ile ara

# Olması gereken
memory.search("geçen hafta ne konuştuk?")  # Anlam ile ara
```

**Neden Kritik:** Kullanıcı "dün ne konuştuk?" derse cevap veremiyoruz.

**Çözüm:**
```python
class SemanticMemory:
    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        self.encoder = SentenceTransformer(model)
        self.dimension = 384
    
    def encode(self, text: str) -> np.ndarray
    def store(self, text: str, metadata: dict) -> str
    def search(self, query: str, k: int = 5) -> List[SearchResult]
    def search_by_date(self, query: str, after: datetime) -> List[SearchResult]
```

**Gerekli Kütüphaneler:**
- `sentence-transformers` - Embedding modeli
- `pgvector` - PostgreSQL vector extension

**Dosyalar:**
- [ ] `core/memory/semantic.py`
- [ ] `core/memory/embeddings.py`
- [ ] `sql/vector_schema.sql`
- [ ] `tests/unit/test_semantic_memory.py`

---

### 2.3 Context Management (YOK)

**Sorun:**
```
Memory'de: 10,000 mesaj
LLM context: ~4,000 token limit

Soru: Hangilerini LLM'e vereceğiz?
```

**Neden Kritik:** Yanlış context = yanlış cevap.

**Çözüm:**
```python
class ContextBuilder:
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def build(self,
              query: str,
              recent_turns: List[DialogueTurn],
              relevant_memories: List[MemoryItem],
              self_state: SelfState,
              relationship: RelationshipRecord) -> str:
        """
        Context öncelik sırası:
        1. System prompt (personality, rules)
        2. Self state özeti (mood, needs)
        3. Relationship özeti (trust, history)
        4. Son N turn (recency)
        5. İlgili memory'ler (relevance)
        6. Kullanıcı mesajı
        """
    
    def count_tokens(self, text: str) -> int
    def truncate_to_fit(self, sections: List[str]) -> str
```

**Dosyalar:**
- [ ] `core/language/context.py`
- [ ] `tests/unit/test_context_builder.py`

---

### 2.4 LLM Adapter (YOK)

**Sorun:** UEM karar veriyor ama konuşamıyor.

**Çözüm:**
```python
class LLMAdapter:
    """LLM API wrapper - değiştirilebilir backend"""
    
    def __init__(self, provider: str = "anthropic"):
        self.provider = provider
        self.client = self._init_client()
    
    async def generate(self,
                       context: str,
                       temperature: float = 0.7,
                       max_tokens: int = 500) -> str:
        """Cevap üret"""
    
    async def generate_stream(self,
                              context: str) -> AsyncIterator[str]:
        """Streaming cevap"""

class UEMChatAgent:
    """UEM + LLM entegre agent"""
    
    def __init__(self,
                 personality: str,
                 llm: LLMAdapter,
                 memory: MemoryStore,
                 self_processor: SelfProcessor):
        self.personality = personality
        self.llm = llm
        self.memory = memory
        self.self_processor = self_processor
    
    async def chat(self, user_message: str) -> str:
        # 1. Memory'den context al
        recent = self.memory.conversation.get_recent(10)
        relevant = self.memory.semantic.search(user_message, k=5)
        
        # 2. Self state al
        self_state = self.self_processor.get_state()
        
        # 3. Context oluştur
        context = self.context_builder.build(
            query=user_message,
            recent_turns=recent,
            relevant_memories=relevant,
            self_state=self_state
        )
        
        # 4. LLM'den cevap al
        response = await self.llm.generate(context)
        
        # 5. Memory'ye kaydet
        self.memory.conversation.add_turn(
            DialogueTurn(role="user", content=user_message)
        )
        self.memory.conversation.add_turn(
            DialogueTurn(role="agent", content=response)
        )
        
        # 6. UEM state güncelle
        self._update_state(user_message, response)
        
        return response
```

**Dosyalar:**
- [ ] `core/language/__init__.py`
- [ ] `core/language/llm_adapter.py`
- [ ] `core/language/chat_agent.py`
- [ ] `core/language/prompts.py`
- [ ] `tests/unit/test_chat_agent.py`

---

### 2.5 Decay/Forgetting (Pasif)

**Sorun:** Kod var ama aktif kullanılmıyor.

```python
# memory/store.py'de var
def apply_decay(self, hours: float = 1.0):
    """Memory decay uygula"""

# Ama hiçbir yerde çağrılmıyor!
```

**Çözüm:**
- [ ] Decay'i scheduled job olarak çalıştır
- [ ] Importance'a göre decay rate
- [ ] Consolidation (STM → LTM)

---

### 2.6 Learning (YOK)

**Sorun:** Agent hiçbir şey öğrenmiyor.

**Temel Learning:**
- Başarılı etkileşimleri hatırla
- Başarısızlardan kaçın
- Pattern'leri fark et

**İleri Learning (Sonra):**
- Skill acquisition
- Behavior adaptation
- Personality evolution

---

## 3. ÖNCELIK MATRİSİ

```
                    ACIL
                      ↑
    ┌─────────────────┼─────────────────┐
    │                 │                 │
    │  Conversation   │                 │
    │  Memory         │                 │
    │                 │                 │
    │  Embedding      │                 │
    │  Search         │                 │
    │                 │                 │
ÖNEMLİ ──────────────┼──────────────── ÖNEMSİZ
    │                 │                 │
    │  Context Mgmt   │  Multi-Agent    │
    │                 │                 │
    │  LLM Adapter    │  Oyun/NPC       │
    │                 │                 │
    │  Decay Active   │  Robotik        │
    │                 │                 │
    └─────────────────┼─────────────────┘
                      ↓
                  ACİL DEĞİL
```

---

## 4. ROADMAP (Gerçekçi)

### Faz 1: Memory Güçlendirme (4-6 Hafta)

| Hafta | İş | Çıktı |
|-------|-----|-------|
| 1-2 | Conversation Memory | `conversation.py`, testler |
| 3-4 | Embedding + pgvector | `semantic.py`, vector search |
| 5 | Context Management | `context.py` |
| 6 | Entegrasyon + Test | Memory v2 çalışır |

**Başarı Kriteri:**
```python
memory.conversation.add_turn(...)
results = memory.semantic.search("dün ne konuştuk?")
context = context_builder.build(...)
```

### Faz 2: Dil Entegrasyonu (4-6 Hafta)

| Hafta | İş | Çıktı |
|-------|-----|-------|
| 1 | LLM Adapter | Claude/Ollama wrapper |
| 2-3 | Chat Agent | UEMChatAgent sınıfı |
| 4 | CLI Interface | `python -m uem.chat` |
| 5 | Test & Debug | 100 turlu sohbet testi |
| 6 | Refinement | Prompt tuning |

**Başarı Kriteri:**
```bash
$ python -m uem.chat
UEM: Merhaba! Ben UEM. Nasıl yardımcı olabilirim?
Sen: Dün ne konuşmuştuk?
UEM: Dün Python projenden bahsetmiştin. Deadline yaklaşıyordu, nasıl gitti?
```

### Faz 3: Stabilizasyon (2-4 Hafta)

| İş | Açıklama |
|----|----------|
| Decay aktif | Scheduled memory cleanup |
| Logging | Conversation logs |
| Error handling | Graceful failures |
| Performance | Response time < 2s |

### Faz 4: Interface (2-4 Hafta)

| İş | Açıklama |
|----|----------|
| Web UI | Basit chat interface |
| API | REST endpoint |
| Docs | Kullanım kılavuzu |

### Gelecek (6+ Ay Sonra)

| İş | Ne Zaman |
|----|----------|
| Learning basics | Faz 4 sonrası |
| Multi-agent | Learning sonrası |
| Discord/Telegram bot | İsteğe bağlı |
| Oyun entegrasyonu | Yıllar sonra |

---

## 5. TEKNİK KARARLAR

### 5.1 Embedding Model

| Model | Boyut | Türkçe | Karar |
|-------|-------|--------|-------|
| all-MiniLM-L6-v2 | 384 | ⚠️ Orta | Development |
| paraphrase-multilingual-MiniLM-L12-v2 | 384 | ✅ İyi | **Production** |

### 5.2 Vector Storage

| Seçenek | Karar |
|---------|-------|
| FAISS | ❌ Ayrı sistem |
| Pinecone | ❌ Paralı |
| **pgvector** | ✅ Mevcut PostgreSQL |

### 5.3 LLM Provider

| Provider | Kullanım |
|----------|----------|
| Ollama (local) | Development, test |
| Claude API | Production |

---

## 6. DOSYA YAPISI (Planlanan)

```
core/
├── memory/
│   ├── conversation.py      # YENİ - Sohbet hafızası
│   ├── semantic.py          # YENİ - Embedding search
│   ├── embeddings.py        # YENİ - Vector operations
│   └── persistence/
│       └── conversation_repo.py  # YENİ
│
├── language/                # YENİ KLASÖR
│   ├── __init__.py
│   ├── llm_adapter.py       # LLM wrapper
│   ├── chat_agent.py        # UEM + LLM entegrasyon
│   ├── context.py           # Context builder
│   └── prompts.py           # Prompt templates

interface/
├── chat/                    # YENİ KLASÖR
│   ├── __init__.py
│   ├── cli.py               # CLI chat
│   └── web.py               # Web interface (sonra)

sql/
├── conversation_schema.sql  # YENİ
└── vector_schema.sql        # YENİ
```

---

## 7. BAŞARI METRİKLERİ

### Faz 1 Sonu (Memory)

- [ ] Conversation memory 1000+ turn saklayabiliyor
- [ ] Semantic search < 100ms
- [ ] Doğru memory retrieval %80+

### Faz 2 Sonu (Dil)

- [ ] 10 turlu sohbet tutarlı
- [ ] Geçmiş hatırlanıyor
- [ ] Response time < 3s
- [ ] Kişilik tutarlı

### Faz 3 Sonu (Stabil)

- [ ] 100 turlu sohbet tutarlı
- [ ] Memory şişmiyor (decay çalışıyor)
- [ ] Error rate < %1

---

## 8. RİSKLER VE MİTİGASYON

| Risk | Olasılık | Etki | Mitigasyon |
|------|----------|------|------------|
| Embedding Türkçe zayıf | Orta | Yüksek | Multilingual model |
| LLM maliyeti | Yüksek | Orta | Ollama local dev |
| Context overflow | Orta | Orta | Smart truncation |
| Memory şişmesi | Orta | Yüksek | Decay + summarization |

---

## 9. YAPILMAYACAKLAR (Şimdilik)

| İş | Neden Değil |
|----|-------------|
| Unity/Unreal plugin | Çok erken, temel yok |
| Multi-agent simulation | Learning yok |
| Robotik | Çok uzak gelecek |
| Mobile app | Web önce |
| Voice | Text önce |

---

## 10. DEĞİŞİKLİK GEÇMİŞİ

| Tarih | Versiyon | Değişiklik |
|-------|----------|------------|
| 8 Aralık 2025 | 1.0 | İlk versiyon |
| 8 Aralık 2025 | 1.1 | Gerçekçi revizyon - Oyun/NPC kaldırıldı, kritik eksikliklere odaklanıldı |

---

## 11. SONRAKI AKSIYONLAR

**Hemen (Bu Hafta):**
1. [ ] `core/memory/conversation.py` oluştur
2. [ ] PostgreSQL conversation tablosu ekle
3. [ ] Unit testler yaz

**Yakında (2 Hafta):**
4. [ ] pgvector kurulumu
5. [ ] Embedding model seçimi ve test
6. [ ] `core/memory/semantic.py` oluştur

---

*Bu doküman yaşayan bir dokümandır. Her sprint sonunda güncellenir.*
