"""
tests/unit/test_embeddings.py

Embedding modulu unit testleri.
EmbeddingEncoder, similarity utilities ve cache testleri.
"""

import pytest
import sys
sys.path.insert(0, '.')

import numpy as np
from core.memory import (
    EmbeddingConfig,
    EmbeddingModel,
    EmbeddingEncoder,
    create_embedding_encoder,
    cosine_similarity,
    batch_cosine_similarity,
    top_k_indices,
    euclidean_distance,
    normalize_vector,
)


# ========================================================================
# FIXTURES
# ========================================================================

@pytest.fixture
def encoder():
    """Create embedding encoder with lazy loading."""
    config = EmbeddingConfig(
        lazy_load=True,
        cache_enabled=True,
        cache_max_size=100,
    )
    return create_embedding_encoder(config)


@pytest.fixture
def loaded_encoder():
    """Create and load embedding encoder."""
    config = EmbeddingConfig(
        lazy_load=False,
        cache_enabled=True,
        cache_max_size=100,
    )
    return create_embedding_encoder(config)


@pytest.fixture
def no_cache_encoder():
    """Create encoder without cache."""
    config = EmbeddingConfig(
        lazy_load=True,
        cache_enabled=False,
    )
    return create_embedding_encoder(config)


# ========================================================================
# EMBEDDING CONFIG TESTS
# ========================================================================

class TestEmbeddingConfig:
    """EmbeddingConfig testleri."""

    def test_default_config(self):
        """Varsayilan config degerler."""
        config = EmbeddingConfig()
        assert config.model_name == EmbeddingModel.MULTILINGUAL_MINILM.value
        assert config.dimension == 384
        assert config.batch_size == 32
        assert config.cache_enabled is True
        assert config.lazy_load is True
        assert config.normalize_embeddings is True

    def test_custom_config(self):
        """Ozel config degerler."""
        config = EmbeddingConfig(
            model_name=EmbeddingModel.MINILM_L6.value,
            dimension=384,
            batch_size=64,
            cache_max_size=5000,
        )
        assert config.model_name == "all-MiniLM-L6-v2"
        assert config.batch_size == 64
        assert config.cache_max_size == 5000


class TestEmbeddingModel:
    """EmbeddingModel enum testleri."""

    def test_multilingual_model(self):
        """Multilingual model degeri."""
        assert EmbeddingModel.MULTILINGUAL_MINILM.value == "paraphrase-multilingual-MiniLM-L12-v2"

    def test_minilm_model(self):
        """MiniLM model degeri."""
        assert EmbeddingModel.MINILM_L6.value == "all-MiniLM-L6-v2"

    def test_mpnet_model(self):
        """MPNet model degeri."""
        assert EmbeddingModel.MPNET_BASE.value == "all-mpnet-base-v2"


# ========================================================================
# ENCODER LAZY LOADING TESTS
# ========================================================================

class TestEncoderLazyLoading:
    """Encoder lazy loading testleri."""

    def test_lazy_load_not_loaded_initially(self, encoder):
        """Lazy load: model ilk basta yuklenmez."""
        assert encoder.is_model_loaded() is False

    def test_lazy_load_on_first_encode(self, encoder):
        """Lazy load: ilk encode'da yuklenir."""
        assert encoder.is_model_loaded() is False
        _ = encoder.encode("test")
        assert encoder.is_model_loaded() is True

    def test_eager_load(self, loaded_encoder):
        """Eager load: model hemen yuklenir."""
        assert loaded_encoder.is_model_loaded() is True

    def test_model_property_triggers_load(self, encoder):
        """Model property'si yuklemeyi tetikler."""
        assert encoder.is_model_loaded() is False
        _ = encoder.model
        assert encoder.is_model_loaded() is True


# ========================================================================
# ENCODING TESTS
# ========================================================================

class TestEncoding:
    """Encoding testleri."""

    def test_encode_single_text(self, loaded_encoder):
        """Tek metin encode."""
        embedding = loaded_encoder.encode("Hello world")
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,)

    def test_encode_returns_float32(self, loaded_encoder):
        """Encoding float32 dondurur."""
        embedding = loaded_encoder.encode("Test")
        assert embedding.dtype == np.float32

    def test_encode_normalized(self, loaded_encoder):
        """Normalized embedding (L2 norm ~= 1)."""
        embedding = loaded_encoder.encode("Test text")
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 0.01

    def test_encode_batch_texts(self, loaded_encoder):
        """Toplu metin encode."""
        texts = ["Hello", "World", "Test"]
        embeddings = loaded_encoder.encode_batch(texts)
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (3, 384)

    def test_encode_batch_empty(self, loaded_encoder):
        """Bos liste encode."""
        embeddings = loaded_encoder.encode_batch([])
        assert embeddings.size == 0

    def test_encode_batch_single(self, loaded_encoder):
        """Tek elemanli liste encode."""
        embeddings = loaded_encoder.encode_batch(["Hello"])
        assert embeddings.shape == (1, 384)

    def test_encode_turkish(self, loaded_encoder):
        """Turkce metin encode."""
        embedding = loaded_encoder.encode("Merhaba dünya! Nasılsınız?")
        assert embedding.shape == (384,)
        assert np.linalg.norm(embedding) > 0

    def test_encode_english(self, loaded_encoder):
        """Ingilizce metin encode."""
        embedding = loaded_encoder.encode("Hello world! How are you?")
        assert embedding.shape == (384,)
        assert np.linalg.norm(embedding) > 0

    def test_similar_texts_close_embeddings(self, loaded_encoder):
        """Benzer metinler yakin embedding'ler uretir."""
        emb1 = loaded_encoder.encode("I love programming")
        emb2 = loaded_encoder.encode("I enjoy coding")
        emb3 = loaded_encoder.encode("The weather is nice today")

        sim_similar = cosine_similarity(emb1, emb2)
        sim_different = cosine_similarity(emb1, emb3)

        # Benzer metinler daha yuksek benzerlik
        assert sim_similar > sim_different

    def test_get_dimension(self, encoder):
        """Dimension degeri."""
        assert encoder.get_dimension() == 384


# ========================================================================
# CACHE TESTS
# ========================================================================

class TestCache:
    """Cache testleri."""

    def test_cache_hit(self, loaded_encoder):
        """Cache hit: ayni metin tekrar encode edilmez."""
        text = "Cache test text"

        # Ilk encode
        _ = loaded_encoder.encode(text)
        stats1 = loaded_encoder.cache_stats

        # Ikinci encode (cache'den gelmeli)
        _ = loaded_encoder.encode(text)
        stats2 = loaded_encoder.cache_stats

        assert stats2["hits"] == stats1["hits"] + 1

    def test_cache_miss(self, loaded_encoder):
        """Cache miss: farkli metinler icin."""
        _ = loaded_encoder.encode("Text 1")
        stats1 = loaded_encoder.cache_stats

        _ = loaded_encoder.encode("Text 2")
        stats2 = loaded_encoder.cache_stats

        assert stats2["misses"] == stats1["misses"] + 1

    def test_cache_clear(self, loaded_encoder):
        """Cache temizleme."""
        loaded_encoder.encode("Test 1")
        loaded_encoder.encode("Test 2")

        cleared = loaded_encoder.clear_cache()
        assert cleared >= 2

        stats = loaded_encoder.cache_stats
        assert stats["size"] == 0

    def test_cache_disabled(self, no_cache_encoder):
        """Cache devre disi."""
        no_cache_encoder._load_model()  # Load model first
        _ = no_cache_encoder.encode("Test")
        stats = no_cache_encoder.cache_stats
        assert stats["enabled"] is False

    def test_cache_stats(self, loaded_encoder):
        """Cache istatistikleri."""
        loaded_encoder.encode("Test")
        stats = loaded_encoder.cache_stats

        assert "size" in stats
        assert "max_size" in stats
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats

    def test_batch_uses_cache(self, loaded_encoder):
        """Batch encoding cache kullanir."""
        # Pre-encode some texts
        loaded_encoder.encode("Text A")
        loaded_encoder.encode("Text B")

        stats1 = loaded_encoder.cache_stats

        # Batch encode with some cached texts
        loaded_encoder.encode_batch(["Text A", "Text C", "Text B"])

        stats2 = loaded_encoder.cache_stats
        # Should have 2 cache hits
        assert stats2["hits"] >= stats1["hits"] + 2


# ========================================================================
# SIMILARITY UTILITY TESTS
# ========================================================================

class TestCosineSimilarity:
    """Cosine similarity testleri."""

    def test_identical_vectors(self):
        """Ayni vektorler 1.0 benzerlik."""
        v = np.array([1.0, 2.0, 3.0])
        sim = cosine_similarity(v, v)
        assert abs(sim - 1.0) < 0.001

    def test_orthogonal_vectors(self):
        """Ortogonal vektorler 0.0 benzerlik."""
        v1 = np.array([1.0, 0.0])
        v2 = np.array([0.0, 1.0])
        sim = cosine_similarity(v1, v2)
        assert abs(sim) < 0.001

    def test_opposite_vectors(self):
        """Zit yonlu vektorler -1.0 benzerlik."""
        v1 = np.array([1.0, 0.0])
        v2 = np.array([-1.0, 0.0])
        sim = cosine_similarity(v1, v2)
        assert abs(sim + 1.0) < 0.001

    def test_zero_vector(self):
        """Sifir vektor 0.0 benzerlik."""
        v1 = np.array([1.0, 2.0])
        v2 = np.array([0.0, 0.0])
        sim = cosine_similarity(v1, v2)
        assert sim == 0.0

    def test_2d_vectors_flattened(self):
        """2D vektorler duzlestiriliyor."""
        v1 = np.array([[1.0, 2.0, 3.0]])
        v2 = np.array([[1.0, 2.0, 3.0]])
        sim = cosine_similarity(v1, v2)
        assert abs(sim - 1.0) < 0.001


class TestBatchCosineSimilarity:
    """Batch cosine similarity testleri."""

    def test_batch_similarity(self):
        """Toplu benzerlik hesaplama."""
        query = np.array([1.0, 0.0, 0.0])
        vectors = np.array([
            [1.0, 0.0, 0.0],  # same
            [0.0, 1.0, 0.0],  # orthogonal
            [-1.0, 0.0, 0.0],  # opposite
        ])

        sims = batch_cosine_similarity(query, vectors)

        assert len(sims) == 3
        assert abs(sims[0] - 1.0) < 0.001
        assert abs(sims[1]) < 0.001
        assert abs(sims[2] + 1.0) < 0.001

    def test_batch_empty_vectors(self):
        """Bos vektor listesi."""
        query = np.array([1.0, 0.0])
        vectors = np.array([]).reshape(0, 2)

        sims = batch_cosine_similarity(query, vectors)
        assert sims.size == 0

    def test_batch_zero_query(self):
        """Sifir query vektor."""
        query = np.array([0.0, 0.0])
        vectors = np.array([[1.0, 0.0], [0.0, 1.0]])

        sims = batch_cosine_similarity(query, vectors)
        assert all(s == 0.0 for s in sims)


class TestTopKIndices:
    """Top-k indices testleri."""

    def test_top_k_basic(self):
        """Temel top-k."""
        sims = np.array([0.5, 0.9, 0.3, 0.7])
        results = top_k_indices(sims, k=2)

        assert len(results) == 2
        assert results[0] == (1, 0.9)  # highest
        assert results[1] == (3, 0.7)  # second

    def test_top_k_with_threshold(self):
        """Threshold ile top-k."""
        sims = np.array([0.5, 0.9, 0.3, 0.7])
        results = top_k_indices(sims, k=10, min_threshold=0.6)

        assert len(results) == 2  # only 0.9 and 0.7
        assert all(score >= 0.6 for _, score in results)

    def test_top_k_empty(self):
        """Bos array."""
        sims = np.array([])
        results = top_k_indices(sims, k=5)
        assert results == []

    def test_top_k_fewer_than_k(self):
        """K'dan az eleman."""
        sims = np.array([0.5, 0.9])
        results = top_k_indices(sims, k=5)
        assert len(results) == 2

    def test_top_k_all_below_threshold(self):
        """Tum skorlar threshold altinda."""
        sims = np.array([0.1, 0.2, 0.3])
        results = top_k_indices(sims, k=5, min_threshold=0.5)
        assert results == []


class TestEuclideanDistance:
    """Euclidean distance testleri."""

    def test_identical_vectors(self):
        """Ayni vektorler 0 mesafe."""
        v = np.array([1.0, 2.0, 3.0])
        dist = euclidean_distance(v, v)
        assert dist == 0.0

    def test_unit_vectors(self):
        """Birim vektorler arasi mesafe."""
        v1 = np.array([1.0, 0.0])
        v2 = np.array([0.0, 1.0])
        dist = euclidean_distance(v1, v2)
        assert abs(dist - np.sqrt(2)) < 0.001


class TestNormalizeVector:
    """Normalize vector testleri."""

    def test_normalize(self):
        """Vektor normalizasyonu."""
        v = np.array([3.0, 4.0])
        normalized = normalize_vector(v)

        norm = np.linalg.norm(normalized)
        assert abs(norm - 1.0) < 0.001

    def test_normalize_zero_vector(self):
        """Sifir vektor normalizasyonu."""
        v = np.array([0.0, 0.0])
        normalized = normalize_vector(v)
        assert np.array_equal(normalized, v)


# ========================================================================
# ENCODER STATS TESTS
# ========================================================================

class TestEncoderStats:
    """Encoder istatistik testleri."""

    def test_stats_structure(self, loaded_encoder):
        """Stats yapisı."""
        stats = loaded_encoder.stats

        assert "model_name" in stats
        assert "dimension" in stats
        assert "model_loaded" in stats
        assert "encode_count" in stats
        assert "batch_count" in stats
        assert "cache" in stats

    def test_encode_count(self, loaded_encoder):
        """Encode sayaci."""
        initial = loaded_encoder.stats["encode_count"]

        loaded_encoder.encode("Test 1")
        loaded_encoder.encode("Test 2")

        assert loaded_encoder.stats["encode_count"] >= initial + 2

    def test_batch_count(self, loaded_encoder):
        """Batch sayaci."""
        initial = loaded_encoder.stats["batch_count"]

        loaded_encoder.encode_batch(["A", "B", "C"])

        assert loaded_encoder.stats["batch_count"] == initial + 1
