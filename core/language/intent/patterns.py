"""
core/language/intent/patterns.py

Türkçe intent pattern veritabanı.

Her intent kategorisi için:
- Standart formlar
- Kısaltmalar (slm, mrb, tşk, vs.)
- Yazım hataları (nasilsin, tesekkurler, vs.)
- Informal varyantlar (naber, nbr, vs.)

UEM v2 - Intent Recognition sistemi.
"""

from typing import Dict, List, Optional
from .types import IntentCategory


# Intent pattern veritabanı
# Her pattern normalize edilmiş forma göre (lowercase, Türkçe karakter düzeltilmiş)
INTENT_PATTERNS: Dict[IntentCategory, List[str]] = {

    # =========================================================================
    # GREETING - Selamlama
    # =========================================================================
    IntentCategory.GREETING: [
        # Standart
        "merhaba",
        "selam",
        "selamlar",
        "hey",
        "hi",
        "hello",
        "gunaydin",
        "iyi gunler",
        "iyi aksam",
        "iyi aksamlar",
        "iyi geceler",

        # Dini
        "selamun aleyküm",
        "selamun aleykum",
        "selamunaleykum",
        "aleykum selam",
        "as",
        "sa",
        "sa as",

        # Kısaltmalar
        "slm",
        "mrb",
        "mrhb",
        "slm as",
        "selam as",

        # Informal
        "selamunaleyküm",  # yazım hatası

        # İngilizce varyantlar
        "good morning",
        "good evening",
        "good night",
        "howdy",
        "hiya",
    ],

    # =========================================================================
    # FAREWELL - Vedalaşma
    # =========================================================================
    IntentCategory.FAREWELL: [
        # Standart
        "hoscakal",
        "hosca kal",
        "gule gule",
        "gorusuruz",
        "sonra gorusuruz",
        "yine gorusuruz",
        "kendine iyi bak",
        "iyi gunler",
        "iyi geceler",
        "iyi aksamlar",

        # İngilizce
        "bye",
        "goodbye",
        "see you",
        "see ya",
        "later",
        "cya",
        "cu",
        "take care",

        # Kısaltmalar
        "bb",
        "bay bay",
        "bbye",
        "güle güle",  # normalize öncesi

        # Informal
        "ben gidiyorum",
        "gitmem lazim",
        "sonra konusalim",
        "simdilik gorusuruz",
    ],

    # =========================================================================
    # ASK_WELLBEING - Hal hatır sorma
    # =========================================================================
    IntentCategory.ASK_WELLBEING: [
        # Standart
        "nasilsin",
        "nasil hissediyorsun",
        "keyifler nasil",
        "iyi misin",
        "nasil gidiyor",
        "ne haber",
        "naber",
        "keyifler",
        "her sey yolunda mi",
        "iyisin dimi",
        "iyi misiniz",
        "ne var ne yok",

        # Kısaltmalar
        "nbr",
        "n'aber",
        "nslsn",

        # Informal
        "ne yapiyorsun",
        "ne durumdasin",
        "napiyorsun",
        "napiyosun",
        "napiyon",
        "keyfin nasil",
        "keyifler nasildir",

        # Yazım hataları
        "nasilsiniz",
        "keyfin nasıl",  # normalize öncesi
    ],

    # =========================================================================
    # ASK_IDENTITY - Kimlik sorma
    # =========================================================================
    IntentCategory.ASK_IDENTITY: [
        # Standart
        "sen kimsin",
        "kimsin",
        "kimsiniz",
        "kim bu",
        "nesin",
        "sen nesin",
        "adin ne",
        "adiniz ne",
        "ismin ne",
        "isminiz ne",

        # Görev sorma
        "ne yapiyorsun",
        "gorevin ne",
        "gorevleriniz neler",
        "neler yapabilirsin",
        "ne is yapiyorsun",
        "ne yapabiliyorsun",
        "yeteneklerin neler",

        # İngilizce
        "who are you",
        "what are you",
        "what's your name",
        "what can you do",

        # Informal
        "sen necisin",
        "kim oldugunu soyler misin",
        "sen ne halt etmektesin",  # agresif ama gerçek kullanım
    ],

    # =========================================================================
    # EXPRESS_POSITIVE - Pozitif duygu ifadesi
    # =========================================================================
    IntentCategory.EXPRESS_POSITIVE: [
        # Standart
        "iyiyim",
        "iyi",
        "harika",
        "harikayim",
        "super",
        "mukemmel",
        "cok iyi",
        "gayet iyi",
        "fena degil",
        "idare eder",
        "eh iste",
        "guzel",
        "mutluyum",
        "cok mutluyum",
        "keyifliyim",
        "sahane",

        # İngilizce
        "great",
        "awesome",
        "perfect",
        "excellent",
        "good",
        "fine",

        # Informal/Abartılı
        "bomba gibiyim",
        "tek kelime muhtesem",
        "atesim",
        "kralim",
        "kralicayim",
        "super iyiyim",
        "cok cok iyiyim",
    ],

    # =========================================================================
    # EXPRESS_NEGATIVE - Negatif duygu ifadesi
    # =========================================================================
    IntentCategory.EXPRESS_NEGATIVE: [
        # Standart
        "kotuyum",
        "kotu",
        "kotu hissediyorum",
        "berbat",
        "cok kotu",
        "uzgunum",
        "uzgun",
        "uzgun hissediyorum",
        "mutsuzum",
        "mutsuz",
        "iyi degilim",
        "fena",
        "moralim bozuk",
        "moralim yok",
        "canim sikkin",
        "depresif",
        "depresifteyim",
        "depresyondayim",
        "stresli",
        "stresliyim",
        "yorgunum",
        "yorgun",
        "biktim",
        "biktim artik",
        "yeter artik",
        "dayanamiyorum",

        # İngilizce
        "sad",
        "bad",
        "terrible",
        "awful",
        "depressed",
        "stressed",
        "tired",

        # Şikayet tonu
        "hic iyi degilim",
        "berbat hissediyorum",
        "cok kotu durumdayim",
        "psikolojim bozuk",
        "ici bozuktum",
        "kafa bozuktum",
    ],

    # =========================================================================
    # REQUEST_HELP - Yardım isteme
    # =========================================================================
    IntentCategory.REQUEST_HELP: [
        # Standart
        "yardim",
        "yardim et",
        "yardimci ol",
        "yardim eder misin",
        "yardim edebilir misin",
        "yardimina ihtiyacim var",
        "bana yardim et",
        "yardima ihtiyacim var",
        "destek",
        "destege ihtiyacim var",

        # İngilizce
        "help",
        "help me",
        "can you help",
        "need help",
        "assistance",

        # İstek ifadeleri
        "bir sorunum var",
        "sorun yasiyorum",
        "problem var",
        "sikinti var",
        "ne yapmam lazim",
        "ne yapmaliyim",
        "nasil yapacagim",

        # Kısaltmalar
        "yardm",
        "hlp",
    ],

    # =========================================================================
    # REQUEST_INFO - Bilgi isteme
    # =========================================================================
    IntentCategory.REQUEST_INFO: [
        # Standart
        "bilgi ver",
        "bilgi verir misin",
        "anlat",
        "acikla",
        "aciklar misin",
        "bu ne demek",
        "nedir",
        "ne demek",
        "nasil",
        "nasil yapilir",
        "ogren",
        "ogrenmek istiyorum",

        # Soru formları
        "bana soyle",
        "bana anlat",
        "bana acikla",
        "soyle bana",
        "soyler misin",
        "anlatir misin",
        "ogretir misin",

        # İngilizce
        "tell me",
        "explain",
        "what is",
        "how to",
        "teach me",
        "show me",

        # Spesifik
        "detay ver",
        "detayli anlat",
        "daha fazla bilgi",
        "ek bilgi",
    ],

    # =========================================================================
    # THANK - Teşekkür
    # =========================================================================
    IntentCategory.THANK: [
        # Standart
        "tesekkurler",
        "tesekkur ederim",
        "tesekkur",
        "sagol",
        "sag ol",
        "cok sagol",
        "cok tesekkur ederim",
        "cok tesekkurler",
        "eyvallah",
        "eyv",
        "tsk",
        "tskkrler",

        # İngilizce
        "thanks",
        "thank you",
        "thank you very much",
        "thx",
        "ty",
        "tysm",
        "many thanks",

        # Resmi
        "minnettarim",
        "minnetdarim",
        "size tesekkur ederim",
        "tesekkurlerimi sunarim",

        # Informal
        "adamsın",
        "kralsin",
        "mukemmelsin",
        "eyv allah razi olsun",
    ],

    # =========================================================================
    # APOLOGIZE - Özür dileme
    # =========================================================================
    IntentCategory.APOLOGIZE: [
        # Standart
        "ozur dilerim",
        "ozur",
        "pardon",
        "kusura bakma",
        "kusura bakmayın",
        "affedersin",
        "affedersiniz",
        "uzgunum",
        "cok uzgunum",

        # İngilizce
        "sorry",
        "i'm sorry",
        "so sorry",
        "apologies",
        "my apologies",
        "excuse me",

        # Informal
        "kb",  # kusura bakma
        "pardon abi",
        "yanlış anladım",
        "hatam",
        "benim hatam",
    ],

    # =========================================================================
    # AGREE - Onay/Kabul
    # =========================================================================
    IntentCategory.AGREE: [
        # Standart
        "evet",
        "eveet",
        "evetttt",
        "tamam",
        "tamamdir",
        "olur",
        "oldu",
        "peki",
        "kabul",
        "kabul ediyorum",
        "anlasildi",
        "anlastik",

        # İngilizce
        "yes",
        "yeah",
        "yep",
        "yup",
        "okay",
        "ok",
        "okey",
        "alright",
        "sure",
        "fine",
        "agreed",

        # Kısaltmalar
        "oki",
        "okey",
        "oky",
        "okii",

        # Informal
        "aynen",
        "aynen oyle",
        "kesinlikle",
        "tabii",
        "tabii ki",
        "elbette",
        "hadi bakalim",
        "yapabiliriz",
        "yapalim",
    ],

    # =========================================================================
    # DISAGREE - Red/Karşı çıkma
    # =========================================================================
    IntentCategory.DISAGREE: [
        # Standart
        "hayir",
        "hayır",
        "yok",
        "olmaz",
        "olmuyor",
        "istemiyorum",
        "istemem",
        "kabul etmiyorum",
        "razı degilim",
        "katilmiyorum",

        # İngilizce
        "no",
        "nope",
        "nah",
        "not really",
        "i don't think so",

        # Informal
        "yok ya",
        "yok canım",
        "hayatta olmaz",
        "asla",
        "imkansiz",
        "oyle olmaz",
        "degil",
        "yanlis",
        "yanlış biliyorsun",
    ],

    # =========================================================================
    # CLARIFY - Netleştirme isteme
    # =========================================================================
    IntentCategory.CLARIFY: [
        # Standart
        "anlamadim",
        "anlamadım",
        "anlamıyorum",
        "ne demek",
        "ne demek istiyorsun",
        "tekrar eder misin",
        "tekrar soyle",
        "tekrarlar misin",
        "aciklar misin",
        "aciklayin",

        # Soru formları
        "nasil yani",
        "yani",
        "ne alaka",
        "anlamadım bi daha soyle",
        "biraz daha acikla",
        "detayli anlat",

        # İngilizce
        "what do you mean",
        "i dont understand",
        "i don't get it",
        "can you clarify",
        "explain please",
        "repeat",

        # Informal
        "ne diyorsun",
        "ne diyon",
        "bi daha soyle",
        "haa",
        "haaa ne",
    ],

    # =========================================================================
    # COMPLAIN - Şikayet
    # =========================================================================
    IntentCategory.COMPLAIN: [
        # Standart
        "sikayet",
        "sikayet ediyorum",
        "sikayetim var",
        "sorun var",
        "problem var",
        "bir sorun var",
        "calısmiyor",
        "calismiyor",
        "bozuk",
        "hata var",
        "yanlis",
        "dogru degil",

        # Güçlü şikayet
        "cok kotu",
        "berbat",
        "rezalet",
        "olmamis",
        "iyi degil",
        "hic iyi degil",
        "boyle olmamali",

        # Spesifik
        "bu ne ya",
        "bu ne bicim",
        "nasil boyle olabilir",
        "inanilmaz",
        "kabul edilemez",
        "memnun degilim",

        # İngilizce
        "complaint",
        "not working",
        "broken",
        "error",
        "wrong",
        "bad",
    ],

    # =========================================================================
    # META_QUESTION - Sistem hakkında soru
    # =========================================================================
    IntentCategory.META_QUESTION: [
        # Standart
        "neden",
        "neden boyle dedin",
        "niye oyle soyledin",
        "nasil calisiyorsun",
        "nasıl calıştığını",
        "nasil yapiyorsun",
        "nasil ogreniyorsun",
        "nasil dusunuyorsun",

        # Yetenek/Kısıt sorguları
        "neler yapabilirsin",
        "neleri biliyorsun",
        "sinirlarin ne",
        "sinirlarin neler",
        "yapamazsin dimi",

        # Reasoning sorguları
        "bu karari nasil verdin",
        "neden bu cevabi verdin",
        "hangi bilgiye gore",
        "nereden biliyorsun",
        "emin misin",

        # İngilizce
        "how do you work",
        "why did you say that",
        "how do you know",
        "what are your limits",
    ],

    # =========================================================================
    # SMALLTALK - Sohbet
    # =========================================================================
    IntentCategory.SMALLTALK: [
        # Standart
        "hava nasil",
        "hava durumu",
        "bugun gunlerden ne",
        "ne yapiyorsun",
        "napiyon",
        "saat kac",
        "tarih ne",

        # Hobi/İlgi
        "nelerden hoslanirsin",
        "hobilerin neler",
        "ne seversin",
        "sevdigin seyler",

        # Günlük
        "gunun nasil gecti",
        "gunun nasil",
        "ne yaptın bugün",
        "planların ne",

        # Rastgele
        "sıkıldım",
        "canım sıkıldı",
        "biraz sohbet edelim",
        "konusalim mi",
        "sohbet",

        # İngilizce
        "how's the weather",
        "what's up",
        "what are you doing",
        "let's chat",
        "tell me something",
    ],
}


# Intent pattern ağırlıkları (confidence çarpanı)
# Bazı pattern'ler daha güvenilir
PATTERN_WEIGHTS: Dict[str, float] = {
    # Yüksek güven (1.0) - Spesifik ve açık
    "yardim et": 1.0,
    "yardimci ol": 1.0,
    "tesekkur ederim": 1.0,
    "cok tesekkurler": 1.0,
    "ozur dilerim": 1.0,
    "sen kimsin": 1.0,
    "adin ne": 1.0,

    # Orta güven (0.8) - Yaygın ama belirsiz olabilir
    "merhaba": 0.8,
    "nasilsin": 0.8,
    "iyiyim": 0.8,
    "kotuyum": 0.8,

    # Düşük güven (0.6) - Çok kısa veya muğlak
    "slm": 0.6,
    "mrb": 0.6,
    "tsk": 0.6,
    "bb": 0.6,
    "nbr": 0.6,
    "ok": 0.6,
    "naber": 0.7,
    "hey": 0.7,
    "yok": 0.6,
    "evet": 0.7,
    "hayir": 0.7,
}


def get_pattern_weight(pattern: str) -> float:
    """
    Pattern için güven ağırlığı döndür.

    Args:
        pattern: Pattern metni

    Returns:
        Ağırlık değeri (0.6-1.0 arası, default 0.8)
    """
    return PATTERN_WEIGHTS.get(pattern, 0.8)


def get_all_patterns() -> List[str]:
    """
    Tüm pattern'leri döndür (중복 olmadan).

    Returns:
        Benzersiz pattern listesi
    """
    all_patterns = []
    for patterns in INTENT_PATTERNS.values():
        all_patterns.extend(patterns)
    return list(set(all_patterns))


def get_pattern_count() -> int:
    """
    Toplam pattern sayısı.

    Returns:
        Pattern sayısı
    """
    return len(get_all_patterns())


def get_patterns_for_category(category: IntentCategory) -> List[str]:
    """
    Belirli bir kategori için pattern'leri döndür.

    Args:
        category: Intent kategorisi

    Returns:
        O kategorinin pattern'leri
    """
    return INTENT_PATTERNS.get(category, [])


# =========================================================================
# Pattern ID Mapping - Faz 5 Episode Logging için
# =========================================================================

def _generate_pattern_ids() -> Dict[str, str]:
    """
    Her pattern için deterministic ID oluştur.

    Format: "{category_value}_{index}"
    Örnek: "greeting_0", "greeting_1", "ask_wellbeing_0", etc.

    Returns:
        Dict mapping pattern text -> pattern ID
    """
    pattern_to_id = {}

    for category, patterns in INTENT_PATTERNS.items():
        category_value = category.value
        for idx, pattern in enumerate(patterns):
            pattern_id = f"{category_value}_{idx}"
            pattern_to_id[pattern] = pattern_id

    return pattern_to_id


# Pattern ID mapping (generated once at import)
PATTERN_TO_ID: Dict[str, str] = _generate_pattern_ids()


def get_pattern_id(pattern: str) -> Optional[str]:
    """
    Pattern text'ten pattern ID'yi getir.

    Args:
        pattern: Pattern text (normalized)

    Returns:
        Pattern ID veya None
    """
    return PATTERN_TO_ID.get(pattern)


def get_pattern_ids_for_category(category: IntentCategory) -> List[str]:
    """
    Belirli bir kategorinin tüm pattern ID'lerini döndür.

    Not: Pattern ID'ler kategori bazlı index kullanır, bu yüzden
    duplicate pattern'ler (örn. "iyi gunler" hem greeting hem farewell)
    farklı kategorilerde farklı ID'lere sahip olur.

    Args:
        category: Intent kategorisi

    Returns:
        Pattern ID listesi (format: "{category_value}_{index}")
    """
    patterns = get_patterns_for_category(category)
    category_value = category.value
    return [f"{category_value}_{idx}" for idx in range(len(patterns))]
