"""
core/language/pipeline/self_critique.py

SelfCritique - Uretilen cevabi degerlendir ve gerekirse duzelt.

Metamind + Self + Ethics ile ic degerlendirme yapar:
- Ton uyumu kontrolu
- Icerik kapsama kontrolu
- Kisit ihlali kontrolu
- Otomatik revizyon

UEM v2 - Thought-to-Speech Pipeline bileşeni.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import re

from ..dialogue.types import (
    MessagePlan,
    SituationModel,
    ToneType,
    DialogueAct,
)
from .config import SelfCritiqueConfig


@dataclass
class CritiqueResult:
    """
    Self critique sonucu.

    Attributes:
        passed: Kritik basarili mi? (revizyon gerekmez)
        score: Deger skoru (0.0-1.0)
        violations: Tespit edilen ihlaller
        improvements: Iyilestirme onerileri
        revised_output: Revize edilmis cikti (opsiyonel)
        details: Detayli degerlendirme bilgisi
    """
    passed: bool
    score: float
    violations: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    revised_output: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate score range."""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(
                f"Score must be between 0.0 and 1.0, got {self.score}"
            )

    @property
    def needs_revision(self) -> bool:
        """Revizyon gerekiyor mu?"""
        return not self.passed and len(self.improvements) > 0

    @property
    def violation_count(self) -> int:
        """Ihlal sayisi."""
        return len(self.violations)

    @property
    def has_critical_violation(self) -> bool:
        """Kritik ihlal var mi?"""
        critical_keywords = [
            "etik", "guvenlik", "tehlike", "kritik",
            "ethical", "safety", "danger", "critical"
        ]
        return any(
            any(kw in v.lower() for kw in critical_keywords)
            for v in self.violations
        )


class SelfCritique:
    """
    Uretilen cevabi degerlendir ve gerekirse duzelt.

    Metamind + Self + Ethics ile ic degerlendirme.

    Kullanim:
        critique = SelfCritique()
        result = critique.critique(output, plan, situation)

        if result.passed:
            print("Cikti onaylandi")
        else:
            print(f"Ihlaller: {result.violations}")
            if result.revised_output:
                print(f"Revize: {result.revised_output}")
    """

    def __init__(
        self,
        config: Optional[SelfCritiqueConfig] = None,
        self_processor: Optional[Any] = None,
        ethics_processor: Optional[Any] = None,
        metamind_processor: Optional[Any] = None
    ):
        """
        SelfCritique olustur.

        Args:
            config: Critique konfigurasyonu
            self_processor: Self modulu (opsiyonel)
            ethics_processor: Ethics modulu (opsiyonel)
            metamind_processor: Metamind modulu (opsiyonel)
        """
        self.config = config or SelfCritiqueConfig()
        self.self_proc = self_processor
        self.ethics = ethics_processor
        self.metamind = metamind_processor

        # Ton anahtar kelimeleri
        self._tone_keywords = self._build_tone_keywords()

        # Problematik pattern'ler
        self._problematic_patterns = self._build_problematic_patterns()

    def critique(
        self,
        output: str,
        plan: MessagePlan,
        situation: SituationModel,
        context: Optional[Dict[str, Any]] = None
    ) -> CritiqueResult:
        """
        Ana critique metodu - ciktiyi degerlendir.

        Args:
            output: Degerlendirilen cikti metni
            plan: MessagePlan
            situation: SituationModel
            context: Ek bagam

        Returns:
            CritiqueResult: Degerlendirme sonucu
        """
        if not self.config.enabled:
            return CritiqueResult(
                passed=True,
                score=1.0,
                details={"skipped": True, "reason": "critique disabled"}
            )

        violations = []
        improvements = []
        scores = []
        details = {}

        # 1. Ton uyumu kontrolu
        if self.config.check_tone_match:
            tone_match, tone_reason = self._check_tone_match(output, plan)
            scores.append(tone_match)
            details["tone_score"] = tone_match
            if not tone_match:
                violations.append(f"Ton uyumsuzlugu: {tone_reason}")
                improvements.append(self._suggest_tone_fix(plan.tone))

        # 2. Icerik kapsama kontrolu
        if self.config.check_content_coverage:
            coverage = self._check_content_coverage(output, plan)
            scores.append(coverage)
            details["content_coverage"] = coverage
            if coverage < 0.5:
                violations.append(
                    f"Dusuk icerik kapsama: {coverage:.1%}"
                )
                improvements.extend(
                    self._suggest_content_additions(output, plan)
                )

        # 3. Kisit ihlalleri kontrolu
        if self.config.check_constraint_violations:
            constraint_violations = self._check_constraint_violations(
                output, plan
            )
            details["constraint_violations"] = constraint_violations
            if constraint_violations:
                violations.extend(constraint_violations)
                constraint_score = max(
                    0.0,
                    1.0 - (len(constraint_violations) * 0.2)
                )
                scores.append(constraint_score)
                improvements.extend(
                    self._suggest_constraint_fixes(constraint_violations)
                )
            else:
                scores.append(1.0)

        # 4. Problematik pattern kontrolu
        pattern_issues = self._check_problematic_patterns(output)
        if pattern_issues:
            violations.extend(pattern_issues)
            pattern_score = max(0.0, 1.0 - (len(pattern_issues) * 0.3))
            scores.append(pattern_score)
            improvements.append("Problematik ifadeleri kaldir veya yeniden yaz")
        else:
            scores.append(1.0)

        # 5. Uzunluk kontrolu
        length_ok, length_reason = self._check_length(output, plan)
        details["length_ok"] = length_ok
        if not length_ok:
            violations.append(f"Uzunluk sorunu: {length_reason}")
            improvements.append("Mesaji kisalt veya uzat")
            scores.append(0.7)
        else:
            scores.append(1.0)

        # Genel skor hesapla
        if scores:
            overall_score = sum(scores) / len(scores)
        else:
            overall_score = 1.0

        # Esik kontrolu
        passed = (
            overall_score >= self.config.min_score_threshold
            and not any(
                "kritik" in v.lower() or "guvenlik" in v.lower()
                for v in violations
            )
        )

        # Revizyon
        revised_output = None
        if not passed and self.config.auto_revise:
            revised_output = self.revise(output, improvements, plan)

        return CritiqueResult(
            passed=passed,
            score=overall_score,
            violations=violations,
            improvements=improvements,
            revised_output=revised_output,
            details=details
        )

    def _check_tone_match(
        self,
        output: str,
        plan: MessagePlan
    ) -> Tuple[float, str]:
        """
        Ton uyumunu kontrol et.

        Args:
            output: Cikti metni
            plan: MessagePlan

        Returns:
            Tuple[score, reason]
        """
        target_tone = plan.tone
        output_lower = output.lower()

        # Ton anahtar kelimelerini kontrol et
        if target_tone not in self._tone_keywords:
            return 0.5, "Bilinmeyen ton tipi"

        keywords = self._tone_keywords[target_tone]
        matches = sum(1 for kw in keywords["positive"] if kw in output_lower)
        violations = sum(
            1 for kw in keywords.get("negative", [])
            if kw in output_lower
        )

        # Skor hesapla
        if violations > 0:
            score = max(0.0, 0.5 - (violations * 0.2))
            return score, f"Uyumsuz ifade bulundu ({violations} adet)"

        if matches > 0:
            score = min(1.0, 0.7 + (matches * 0.1))
            return score, "Ton uyumlu"

        # Notr durum
        return 0.6, "Belirgin ton bulunamadi"

    def _check_content_coverage(
        self,
        output: str,
        plan: MessagePlan
    ) -> float:
        """
        Icerik kapsama oranini hesapla.

        Args:
            output: Cikti metni
            plan: MessagePlan

        Returns:
            Kapsama orani (0.0-1.0)
        """
        if not plan.content_points:
            return 1.0

        output_lower = output.lower()
        covered = 0

        for point in plan.content_points:
            # Icerik noktasi veya anahtar kelimeler
            point_lower = point.lower()
            keywords = point_lower.split()

            # En az bir anahtar kelime eslesmeli
            if any(kw in output_lower for kw in keywords if len(kw) > 3):
                covered += 1

        return covered / len(plan.content_points)

    def _check_constraint_violations(
        self,
        output: str,
        plan: MessagePlan
    ) -> List[str]:
        """
        Kisit ihlallerini kontrol et.

        Args:
            output: Cikti metni
            plan: MessagePlan

        Returns:
            Ihlal listesi
        """
        violations = []
        output_lower = output.lower()

        for constraint in plan.constraints:
            constraint_lower = constraint.lower()

            # "yapmak" iceriyorsa pozitif kisit
            # "yapma" iceriyorsa negatif kisit

            if "yapma" in constraint_lower or "etme" in constraint_lower:
                # Negatif kisit - yasaklanan seyler
                # Kisit aciklamasindan anahtar kelime cikar
                forbidden_words = self._extract_forbidden_words(constraint)
                for word in forbidden_words:
                    if word in output_lower:
                        violations.append(
                            f"Kisit ihlali: '{word}' kullanilmamali"
                        )

            # Etik kisitlari ozel kontrol
            if "durust" in constraint_lower or "seffaf" in constraint_lower:
                # Yaniltici ifadeler kontrol
                misleading = ["kesinlikle", "garanti", "mutlaka dogru"]
                for phrase in misleading:
                    if phrase in output_lower:
                        violations.append(
                            f"Etik kisit ihlali: '{phrase}' yaniltici olabilir"
                        )

        return violations

    def _check_problematic_patterns(self, output: str) -> List[str]:
        """
        Problematik pattern'leri kontrol et.

        Args:
            output: Cikti metni

        Returns:
            Sorun listesi
        """
        issues = []
        output_lower = output.lower()

        for category, patterns in self._problematic_patterns.items():
            for pattern in patterns:
                if pattern in output_lower:
                    issues.append(f"Problematik ifade ({category}): '{pattern}'")
                    break  # Kategori basina bir

        return issues

    def _check_length(
        self,
        output: str,
        plan: MessagePlan
    ) -> Tuple[bool, str]:
        """
        Uzunluk kontrolu.

        Args:
            output: Cikti metni
            plan: MessagePlan

        Returns:
            Tuple[is_ok, reason]
        """
        length = len(output)

        # Cok kisa
        if length < 10:
            return False, "Cok kisa (< 10 karakter)"

        # Cok uzun
        if length > 2000:
            return False, "Cok uzun (> 2000 karakter)"

        # Icerik noktasi sayisina gore
        expected_min = len(plan.content_points) * 20
        if length < expected_min and plan.content_points:
            return False, f"Icerik icin cok kisa (beklenen min: {expected_min})"

        return True, "Uzunluk uygun"

    def _suggest_tone_fix(self, target_tone: ToneType) -> str:
        """Ton duzeltme onerisi."""
        suggestions = {
            ToneType.EMPATHIC: "Daha anlayisli ve sicak ifadeler kullan",
            ToneType.FORMAL: "Daha resmi ve profesyonel dil kullan",
            ToneType.CASUAL: "Daha samimi ve gundelik ifadeler kullan",
            ToneType.SUPPORTIVE: "Daha destekleyici ve cesaretlendirici ol",
            ToneType.CAUTIOUS: "Daha dikkatli ve olculu ifadeler kullan",
            ToneType.SERIOUS: "Daha ciddi ve agir basli ol",
            ToneType.ENTHUSIASTIC: "Daha coskulu ve heyecanli ol",
            ToneType.NEUTRAL: "Daha notr ve tarafsiz ol",
        }
        return suggestions.get(target_tone, "Tonu ayarla")

    def _suggest_content_additions(
        self,
        output: str,
        plan: MessagePlan
    ) -> List[str]:
        """Eksik icerik onerileri."""
        suggestions = []
        output_lower = output.lower()

        for point in plan.content_points:
            point_lower = point.lower()
            keywords = [kw for kw in point_lower.split() if len(kw) > 3]

            if not any(kw in output_lower for kw in keywords):
                suggestions.append(f"Icerik noktasi eksik: {point[:50]}...")

        return suggestions[:3]  # En fazla 3

    def _suggest_constraint_fixes(
        self,
        violations: List[str]
    ) -> List[str]:
        """Kisit ihlali duzeltme onerileri."""
        return [
            f"Duzelt: {v.replace('Kisit ihlali: ', '')}"
            for v in violations[:3]
        ]

    def _extract_forbidden_words(self, constraint: str) -> List[str]:
        """Kisit'tan yasakli kelimeleri cikar."""
        # Basit heuristik - tirnak icindeki kelimeler
        words = re.findall(r"'([^']+)'", constraint)
        if words:
            return words

        # Ozel durumlar
        forbidden_indicators = ["kullanma", "yapma", "etme", "soyleme"]
        for indicator in forbidden_indicators:
            if indicator in constraint.lower():
                # Indicator'dan onceki kelimeyi al
                parts = constraint.lower().split(indicator)
                if len(parts) > 1 and parts[0].strip():
                    return [parts[0].strip().split()[-1]]

        return []

    def revise(
        self,
        output: str,
        improvements: List[str],
        plan: MessagePlan
    ) -> str:
        """
        Ciktiyi revizyonlari uygulayarak duzelt.

        Args:
            output: Orijinal cikti
            improvements: Iyilestirme listesi
            plan: MessagePlan

        Returns:
            Revize edilmis cikti
        """
        revised = output

        # Basit revizyonlar
        for improvement in improvements:
            improvement_lower = improvement.lower()

            # Problematik ifade kaldirma
            if "problematik" in improvement_lower:
                for category, patterns in self._problematic_patterns.items():
                    for pattern in patterns:
                        revised = revised.replace(pattern, "")
                        revised = revised.replace(pattern.capitalize(), "")

            # Ton ayarlama - basit kelime degisiklikleri
            if "anlayisli" in improvement_lower or "sicak" in improvement_lower:
                # Empati ekle
                if not any(
                    word in revised.lower()
                    for word in ["anliyorum", "hissediyorsun", "zor"]
                ):
                    revised = "Anliyorum. " + revised

            # Uzunluk ayarlama
            if "kisalt" in improvement_lower and len(revised) > 500:
                # Son cumleyi kes
                sentences = revised.split(". ")
                if len(sentences) > 2:
                    revised = ". ".join(sentences[:-1]) + "."

        # Temizlik
        revised = " ".join(revised.split())  # Fazla bosluklar
        revised = revised.replace("..", ".").replace("  ", " ")

        return revised

    def _build_tone_keywords(self) -> Dict[ToneType, Dict[str, List[str]]]:
        """Ton anahtar kelimeleri."""
        return {
            ToneType.EMPATHIC: {
                "positive": [
                    "anliyorum", "hissediyorsun", "zor", "yanindayim",
                    "destek", "buradayim"
                ],
                "negative": ["sakin ol", "abartma", "onemli degil"]
            },
            ToneType.SUPPORTIVE: {
                "positive": [
                    "basarabilirsin", "inaniyorum", "guclüsun",
                    "yalniz degilsin", "birlikte"
                ],
                "negative": ["yapamazsin", "zor", "imkansiz"]
            },
            ToneType.FORMAL: {
                "positive": [
                    "saygilarimla", "belirtmek", "bildirmek",
                    "tarafimizdan", "degerlendirmek"
                ],
                "negative": ["ya", "iste", "bak", "hadi"]
            },
            ToneType.CASUAL: {
                "positive": ["bak", "ya", "hadi", "gel", "tamam"],
                "negative": ["saygilarimla", "bildirmek", "tarafimizdan"]
            },
            ToneType.CAUTIOUS: {
                "positive": [
                    "dikkat", "olabilir", "belki", "muhtemelen",
                    "emin olmak"
                ],
                "negative": ["kesinlikle", "garanti", "mutlaka"]
            },
            ToneType.SERIOUS: {
                "positive": ["ciddi", "onemli", "kritik", "dikkat"],
                "negative": ["saka", "eglenceli", "komik"]
            },
            ToneType.ENTHUSIASTIC: {
                "positive": [
                    "harika", "muhtesem", "super", "heyecanli", "cok guzel"
                ],
                "negative": ["sikici", "kotu", "uzucu"]
            },
            ToneType.NEUTRAL: {
                "positive": [],
                "negative": []
            },
        }

    def _build_problematic_patterns(self) -> Dict[str, List[str]]:
        """Problematik pattern'ler."""
        return {
            "offensive": [
                "aptal", "salak", "gerizekali", "mal"
            ],
            "harmful": [
                "kendine zarar ver", "intihar et", "oldur"
            ],
            "misleading": [
                "kesinlikle dogru", "asla yanilmam", "her zaman isler"
            ],
            "boundary": [
                "ben bir doktorum", "tedavi edebilirim", "ila c"
            ]
        }

    def get_critique_summary(self, result: CritiqueResult) -> str:
        """
        Critique sonucunun ozeti.

        Args:
            result: CritiqueResult

        Returns:
            Ozet string
        """
        if result.passed:
            return f"Onaylandi (skor: {result.score:.2f})"

        summary = f"Basarisiz (skor: {result.score:.2f})"
        if result.violations:
            summary += f", {len(result.violations)} ihlal"
        if result.revised_output:
            summary += ", revize edildi"

        return summary
