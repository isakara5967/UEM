"""
core/learning/generalization.py

Rule Extractor - Pattern'lerden kural cikarma.
UEM v2 - Benzer pattern'lerden genellestirilmis kurallar olusturma.

Ozellikler:
- Benzer pattern'leri gruplama
- Ortak template cikarma
- Slot (degisken) tespiti
- Kural uygulama ve eslestirme
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
import logging

import numpy as np

from .types import (
    Pattern,
    PatternType,
    Rule,
    generate_rule_id,
)
from .patterns import PatternStorage

if TYPE_CHECKING:
    from core.memory.embeddings import EmbeddingEncoder

logger = logging.getLogger(__name__)


class RuleExtractor:
    """
    Pattern'lerden kural cikarma sinifi.

    Benzer pattern'leri gruplar ve ortak template'ler cikarir.
    Degisken kisimlar slot olarak isaretlenir.

    Ornek:
        Input patterns:
            - "Merhaba Ali, nasilsin?"
            - "Merhaba Ayse, nasilsin?"
            - "Merhaba Can, nasilsin?"

        Extracted rule:
            - template: "Merhaba {name}, nasilsin?"
            - slots: ["name"]
    """

    def __init__(
        self,
        pattern_storage: PatternStorage,
        encoder: Optional["EmbeddingEncoder"] = None
    ):
        """
        Initialize rule extractor.

        Args:
            pattern_storage: Pattern depolama
            encoder: Embedding encoder (opsiyonel)
        """
        self.patterns = pattern_storage
        self.encoder = encoder
        self._rules: Dict[str, Rule] = {}

    def extract_rules(
        self,
        min_patterns: int = 3,
        similarity_threshold: float = 0.8
    ) -> List[Rule]:
        """
        Benzer pattern'lerden kural cikar.

        1. Pattern'leri grupla (embedding benzerligi)
        2. Her grup icin ortak template bul
        3. Degisken kisimlari {slot} yap

        Args:
            min_patterns: Kural olusturmak icin minimum pattern sayisi
            similarity_threshold: Gruplama icin benzerlik esigi

        Returns:
            Cikarilan kurallar listesi
        """
        all_patterns = self.patterns.get_all()

        if len(all_patterns) < min_patterns:
            return []

        # Group by pattern type first
        by_type: Dict[PatternType, List[Pattern]] = {}
        for pattern in all_patterns:
            if pattern.pattern_type not in by_type:
                by_type[pattern.pattern_type] = []
            by_type[pattern.pattern_type].append(pattern)

        rules = []

        for pattern_type, patterns in by_type.items():
            if len(patterns) < min_patterns:
                continue

            # Group similar patterns
            groups = self._group_similar_patterns(patterns, similarity_threshold)

            for group in groups:
                if len(group) < min_patterns:
                    continue

                # Extract template from group
                template, slots = self._extract_template(group)

                if not template:
                    continue

                # Calculate confidence based on group size and success rates
                confidence = self._calculate_confidence(group)

                # Create rule
                rule = Rule(
                    id=generate_rule_id(),
                    pattern_type=pattern_type,
                    template=template,
                    slots=slots,
                    source_patterns=[p.id for p in group],
                    confidence=confidence
                )

                self._rules[rule.id] = rule
                rules.append(rule)

        logger.info(f"Extracted {len(rules)} rules from {len(all_patterns)} patterns")
        return rules

    def _group_similar_patterns(
        self,
        patterns: List[Pattern],
        threshold: float
    ) -> List[List[Pattern]]:
        """
        Benzer pattern'leri grupla.

        Args:
            patterns: Pattern listesi
            threshold: Benzerlik esigi

        Returns:
            Pattern gruplari
        """
        if not patterns:
            return []

        # If no encoder, group by string similarity
        if self.encoder is None:
            return self._group_by_string_similarity(patterns, threshold)

        # Group by embedding similarity
        groups: List[List[Pattern]] = []
        used = set()

        for i, pattern in enumerate(patterns):
            if pattern.id in used:
                continue

            group = [pattern]
            used.add(pattern.id)

            # Get embedding
            if pattern.embedding:
                p_emb = np.array(pattern.embedding)
            else:
                continue

            # Find similar patterns
            for j, other in enumerate(patterns):
                if i == j or other.id in used:
                    continue

                if other.embedding:
                    o_emb = np.array(other.embedding)
                    similarity = self._cosine_similarity(p_emb, o_emb)

                    if similarity >= threshold:
                        group.append(other)
                        used.add(other.id)

            groups.append(group)

        return groups

    def _group_by_string_similarity(
        self,
        patterns: List[Pattern],
        threshold: float
    ) -> List[List[Pattern]]:
        """
        String benzerligi ile gruplama (encoder yoksa).

        Args:
            patterns: Pattern listesi
            threshold: Benzerlik esigi

        Returns:
            Pattern gruplari
        """
        groups: List[List[Pattern]] = []
        used = set()

        for i, pattern in enumerate(patterns):
            if pattern.id in used:
                continue

            group = [pattern]
            used.add(pattern.id)

            for j, other in enumerate(patterns):
                if i == j or other.id in used:
                    continue

                # Simple string similarity using common words ratio
                similarity = self._string_similarity(pattern.content, other.content)

                if similarity >= threshold:
                    group.append(other)
                    used.add(other.id)

            groups.append(group)

        return groups

    def _string_similarity(self, s1: str, s2: str) -> float:
        """
        Basit string benzerligi hesapla.

        Args:
            s1: Birinci string
            s2: Ikinci string

        Returns:
            Benzerlik skoru (0-1)
        """
        words1 = set(s1.lower().split())
        words2 = set(s2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Cosine similarity between two vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def _extract_template(
        self,
        patterns: List[Pattern]
    ) -> Tuple[str, List[str]]:
        """
        Grup icinden ortak template cikar.

        Args:
            patterns: Pattern grubu

        Returns:
            (template, slots) tuple
        """
        if not patterns:
            return "", []

        if len(patterns) == 1:
            return patterns[0].content, []

        contents = [p.content for p in patterns]

        # Find common prefix and suffix
        prefix, suffix = self._find_common_prefix_suffix(contents)

        if not prefix and not suffix:
            # No common parts - use most frequent pattern
            return patterns[0].content, []

        # Extract varying parts
        varying_parts = []
        for content in contents:
            middle = content
            if prefix:
                middle = middle[len(prefix):]
            if suffix:
                middle = middle[:-len(suffix)] if suffix else middle
            varying_parts.append(middle.strip())

        # If all varying parts are similar, no slot needed
        if len(set(varying_parts)) == 1:
            return patterns[0].content, []

        # Create template with slot
        slot_name = self._generate_slot_name(varying_parts)
        template = f"{prefix}{{{slot_name}}}{suffix}"

        return template.strip(), [slot_name]

    def _find_common_prefix_suffix(
        self,
        strings: List[str]
    ) -> Tuple[str, str]:
        """
        Ortak onek ve sonek bul.

        Args:
            strings: String listesi

        Returns:
            (prefix, suffix) tuple
        """
        if not strings:
            return "", ""

        # Find common prefix
        prefix = strings[0]
        for s in strings[1:]:
            while not s.startswith(prefix):
                prefix = prefix[:-1]
                if not prefix:
                    break

        # Find common suffix
        suffix = strings[0]
        for s in strings[1:]:
            while not s.endswith(suffix):
                suffix = suffix[1:]
                if not suffix:
                    break

        # Handle overlap (prefix and suffix shouldn't overlap)
        if prefix and suffix and len(prefix) + len(suffix) > len(strings[0]):
            # Keep the longer one
            if len(prefix) >= len(suffix):
                suffix = ""
            else:
                prefix = ""

        return prefix, suffix

    def _generate_slot_name(self, varying_parts: List[str]) -> str:
        """
        Degisken kisimlar icin uygun slot ismi olustur.

        Args:
            varying_parts: Degisken kisimlar

        Returns:
            Slot ismi
        """
        # Check if all parts look like names (capitalized)
        if all(part and part[0].isupper() for part in varying_parts if part):
            return "name"

        # Check if all parts are numbers
        if all(part.isdigit() for part in varying_parts if part):
            return "number"

        # Default
        return "value"

    def _calculate_confidence(self, patterns: List[Pattern]) -> float:
        """
        Grup icin guven skoru hesapla.

        Args:
            patterns: Pattern grubu

        Returns:
            Guven skoru (0-1)
        """
        if not patterns:
            return 0.0

        # Factor 1: Group size (more patterns = higher confidence)
        size_factor = min(len(patterns) / 10, 1.0)

        # Factor 2: Average success rate
        success_rates = [p.success_rate for p in patterns if p.total_uses > 0]
        avg_success = sum(success_rates) / len(success_rates) if success_rates else 0.5

        # Combine factors
        confidence = (size_factor * 0.4) + (avg_success * 0.6)

        return min(max(confidence, 0.0), 1.0)

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """
        Kural ID ile getir.

        Args:
            rule_id: Kural ID'si

        Returns:
            Rule nesnesi veya None
        """
        return self._rules.get(rule_id)

    def get_all_rules(self) -> List[Rule]:
        """
        Tum kurallari getir.

        Returns:
            Kural listesi
        """
        return list(self._rules.values())

    def get_rules_by_type(self, pattern_type: PatternType) -> List[Rule]:
        """
        Ture gore kurallari getir.

        Args:
            pattern_type: Pattern turu

        Returns:
            Kural listesi
        """
        return [r for r in self._rules.values() if r.pattern_type == pattern_type]

    def apply_rule(self, rule: Rule, slot_values: Dict[str, str]) -> str:
        """
        Kural uygula: template + slot_values → cumle

        Args:
            rule: Uygulanacak kural
            slot_values: Slot degerleri

        Returns:
            Olusturulan cumle

        Raises:
            ValueError: Eksik slot degeri varsa
        """
        result = rule.template

        for slot in rule.slots:
            if slot not in slot_values:
                raise ValueError(f"Missing slot value for: {slot}")
            result = result.replace(f"{{{slot}}}", slot_values[slot])

        # Update usage count
        rule.usage_count += 1

        return result

    def find_matching_rule(
        self,
        content: str
    ) -> Optional[Tuple[Rule, Dict[str, str]]]:
        """
        Icerigi uyan kural bul ve slot degerlerini cikar.

        Args:
            content: Aranacak icerik

        Returns:
            (Rule, slot_values) tuple veya None
        """
        for rule in self._rules.values():
            slot_values = self._match_template(rule.template, rule.slots, content)
            if slot_values is not None:
                return rule, slot_values

        return None

    def _match_template(
        self,
        template: str,
        slots: List[str],
        content: str
    ) -> Optional[Dict[str, str]]:
        """
        Template'i content ile esleştir.

        Args:
            template: Kural template'i
            slots: Slot isimleri
            content: Icerik

        Returns:
            Slot degerleri sozlugu veya None
        """
        if not slots:
            # No slots - exact match
            return {} if template == content else None

        # Convert template to regex
        pattern = template
        for slot in slots:
            pattern = pattern.replace(f"{{{slot}}}", f"(?P<{slot}>.+?)")

        # Escape special regex chars except our groups
        pattern = re.escape(pattern)
        pattern = pattern.replace(r"\(\?P\<", "(?P<").replace(r"\>\.\+\?\)", ">.+?)")

        try:
            match = re.fullmatch(pattern, content)
            if match:
                return match.groupdict()
        except re.error:
            pass

        return None

    def clear(self) -> int:
        """
        Tum kurallari temizle.

        Returns:
            Silinen kural sayisi
        """
        count = len(self._rules)
        self._rules.clear()
        return count

    def stats(self) -> Dict[str, Any]:
        """
        Kural istatistiklerini getir.

        Returns:
            Istatistik sozlugu
        """
        if not self._rules:
            return {
                "total_rules": 0,
                "by_type": {},
                "average_confidence": 0.0,
                "total_usage": 0,
                "average_slots": 0.0
            }

        by_type: Dict[str, int] = {}
        for rule in self._rules.values():
            type_name = rule.pattern_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

        total_confidence = sum(r.confidence for r in self._rules.values())
        total_usage = sum(r.usage_count for r in self._rules.values())
        total_slots = sum(len(r.slots) for r in self._rules.values())

        return {
            "total_rules": len(self._rules),
            "by_type": by_type,
            "average_confidence": total_confidence / len(self._rules),
            "total_usage": total_usage,
            "average_slots": total_slots / len(self._rules)
        }
