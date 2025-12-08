"""
UEM v2 - MetaMind Patterns

Kalip tespiti: "Tekrarlayan kalipler var mi?"
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import statistics

from .types import (
    Pattern,
    PatternType,
    CycleAnalysisResult,
    SeverityLevel,
)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class PatternDetectorConfig:
    """PatternDetector yapilandirmasi."""
    # Tespit esikleri
    min_occurrences: int = 3                   # Min tekrar sayisi
    recurrence_threshold: float = 0.3          # %30 tekrarlama = kalip
    spike_threshold: float = 2.0               # 2x = spike
    degradation_threshold: float = 0.1         # %10 bozulma

    # Zaman pencereleri
    short_window: int = 10                     # Kisa pencere
    medium_window: int = 50                    # Orta pencere
    long_window: int = 200                     # Uzun pencere

    # Kararlilik
    stability_threshold: float = 0.7           # Kararlilik esigi
    min_stability_samples: int = 20            # Min sample

    # Pattern yaslama
    pattern_max_age_hours: int = 48            # Max yas
    max_patterns: int = 50                     # Max kalip sayisi


# ============================================================================
# PATTERN DETECTOR
# ============================================================================

class PatternDetector:
    """
    Kalip dedektoru.

    Cycle analizlerinde tekrarlayan kaliplari tespit eder.
    """

    def __init__(self, config: Optional[PatternDetectorConfig] = None):
        """
        PatternDetector baslat.

        Args:
            config: Yapilandirma
        """
        self.config = config or PatternDetectorConfig()

        # Tespit edilen kalipler
        self._patterns: Dict[str, Pattern] = {}

        # Veri gecmisleri
        self._duration_history: List[Tuple[int, float]] = []  # (cycle_id, duration)
        self._phase_histories: Dict[str, List[Tuple[int, float]]] = {}
        self._anomaly_history: List[Tuple[int, str]] = []  # (cycle_id, reason)

        # Sayaclar
        self._patterns_detected = 0
        self._cycles_processed = 0

    # ========================================================================
    # MAIN DETECTION
    # ========================================================================

    def process_analysis(
        self,
        analysis: CycleAnalysisResult,
    ) -> List[Pattern]:
        """
        Analiz sonucunu isle ve kaliplari tespit et.

        Args:
            analysis: Cycle analiz sonucu

        Returns:
            Yeni tespit edilen kalipler
        """
        self._cycles_processed += 1

        # Veriyi gecmise ekle
        self._update_histories(analysis)

        detected_patterns = []

        # 1. Spike detection
        spike = self._detect_spike(analysis)
        if spike:
            detected_patterns.append(spike)

        # 2. Recurring anomaly detection
        if analysis.is_anomaly and analysis.anomaly_reason:
            recurring = self._detect_recurring_anomaly(analysis)
            if recurring:
                detected_patterns.append(recurring)

        # 3. Phase bottleneck pattern
        bottleneck = self._detect_phase_bottleneck(analysis)
        if bottleneck:
            detected_patterns.append(bottleneck)

        # 4. Trend patterns (yeterli veri varsa)
        if len(self._duration_history) >= self.config.medium_window:
            trend = self._detect_trend_pattern()
            if trend:
                detected_patterns.append(trend)

        # 5. Oscillation detection
        if len(self._duration_history) >= self.config.short_window:
            osc = self._detect_oscillation()
            if osc:
                detected_patterns.append(osc)

        # 6. Stability pattern
        stability = self._detect_stability()
        if stability:
            detected_patterns.append(stability)

        # Cleanup old patterns
        self._cleanup_old_patterns()

        return detected_patterns

    # ========================================================================
    # HISTORY MANAGEMENT
    # ========================================================================

    def _update_histories(self, analysis: CycleAnalysisResult) -> None:
        """Gecmisleri guncelle."""
        # Duration history
        self._duration_history.append((analysis.cycle_id, analysis.total_duration_ms))
        if len(self._duration_history) > self.config.long_window * 2:
            self._duration_history = self._duration_history[-self.config.long_window:]

        # Phase histories
        for phase, duration in analysis.phase_durations.items():
            if phase not in self._phase_histories:
                self._phase_histories[phase] = []
            self._phase_histories[phase].append((analysis.cycle_id, duration))
            if len(self._phase_histories[phase]) > self.config.long_window:
                self._phase_histories[phase] = self._phase_histories[phase][-self.config.long_window:]

        # Anomaly history
        if analysis.is_anomaly:
            self._anomaly_history.append((analysis.cycle_id, analysis.anomaly_reason or "unknown"))
            if len(self._anomaly_history) > self.config.long_window:
                self._anomaly_history = self._anomaly_history[-self.config.long_window:]

    # ========================================================================
    # SPIKE DETECTION
    # ========================================================================

    def _detect_spike(self, analysis: CycleAnalysisResult) -> Optional[Pattern]:
        """Ani artis (spike) tespit et."""
        if len(self._duration_history) < self.config.min_occurrences:
            return None

        recent = [d for _, d in self._duration_history[-self.config.short_window:]]
        if not recent:
            return None

        avg = statistics.mean(recent)
        if avg == 0:
            return None

        # Spike kontrolu
        if analysis.total_duration_ms > avg * self.config.spike_threshold:
            pattern_key = "spike_duration"

            if pattern_key in self._patterns:
                # Mevcut pattern'i guncelle
                self._patterns[pattern_key].update_occurrence(
                    analysis.cycle_id,
                    analysis.total_duration_ms,
                )
                return None  # Yeni pattern degil
            else:
                # Yeni spike pattern
                pattern = Pattern(
                    pattern_type=PatternType.SPIKE,
                    name="Duration Spike",
                    description=f"Cycle duration spiked to {analysis.total_duration_ms:.1f}ms (avg: {avg:.1f}ms)",
                    affected_metric="duration_ms",
                    average_impact=analysis.total_duration_ms - avg,
                    confidence=0.85,
                )
                pattern.update_occurrence(analysis.cycle_id, analysis.total_duration_ms)

                self._register_pattern(pattern, pattern_key)
                return pattern

        return None

    # ========================================================================
    # RECURRING ANOMALY DETECTION
    # ========================================================================

    def _detect_recurring_anomaly(self, analysis: CycleAnalysisResult) -> Optional[Pattern]:
        """Tekrarlayan anomali tespit et."""
        if not analysis.anomaly_reason:
            return None

        # Ayni nedenden kac anomali var?
        reason = analysis.anomaly_reason
        similar_count = sum(1 for _, r in self._anomaly_history if r == reason)

        if similar_count >= self.config.min_occurrences:
            pattern_key = f"recurring_anomaly_{hash(reason) % 10000}"

            if pattern_key in self._patterns:
                self._patterns[pattern_key].update_occurrence(analysis.cycle_id)
                self._patterns[pattern_key].stability = min(
                    1.0,
                    similar_count / len(self._anomaly_history),
                )
                return None
            else:
                pattern = Pattern(
                    pattern_type=PatternType.RECURRING,
                    name=f"Recurring Anomaly: {reason[:50]}",
                    description=f"Same anomaly occurred {similar_count} times",
                    confidence=0.7 + (similar_count * 0.05),
                    stability=similar_count / max(1, len(self._anomaly_history)),
                )
                pattern.update_occurrence(analysis.cycle_id)

                self._register_pattern(pattern, pattern_key)
                return pattern

        return None

    # ========================================================================
    # PHASE BOTTLENECK PATTERN
    # ========================================================================

    def _detect_phase_bottleneck(self, analysis: CycleAnalysisResult) -> Optional[Pattern]:
        """Phase darbogazpattern'i tespit et."""
        if not analysis.slowest_phase:
            return None

        phase = analysis.slowest_phase
        if phase not in self._phase_histories:
            return None

        phase_data = self._phase_histories[phase]
        if len(phase_data) < self.config.min_occurrences:
            return None

        # Bu phase kac kez en yavas oldu?
        # Son N cycle'da kontrol et
        recent_analyses = self._duration_history[-self.config.short_window:]
        bottleneck_count = 0

        for cycle_id, _ in recent_analyses:
            # Bu cycle icin phase verisi var mi?
            phase_dur = next((d for cid, d in phase_data if cid == cycle_id), None)
            if phase_dur is None:
                continue

            # Toplam sure icin diger phase'leri de kontrol et
            total_dur = next((d for cid, d in self._duration_history if cid == cycle_id), 0)
            if total_dur > 0 and phase_dur / total_dur > 0.4:  # %40+
                bottleneck_count += 1

        frequency = bottleneck_count / len(recent_analyses) if recent_analyses else 0

        if frequency >= self.config.recurrence_threshold:
            pattern_key = f"bottleneck_{phase}"

            if pattern_key in self._patterns:
                self._patterns[pattern_key].frequency = frequency
                self._patterns[pattern_key].update_occurrence(analysis.cycle_id)
                return None
            else:
                avg_phase_dur = statistics.mean([d for _, d in phase_data[-self.config.short_window:]])

                pattern = Pattern(
                    pattern_type=PatternType.RECURRING,
                    name=f"Phase Bottleneck: {phase}",
                    description=f"{phase} is consistently the slowest phase ({frequency*100:.0f}% of cycles)",
                    affected_metric=f"phase_{phase}_ms",
                    average_impact=avg_phase_dur,
                    frequency=frequency,
                    confidence=0.8,
                )
                pattern.update_occurrence(analysis.cycle_id, avg_phase_dur)

                self._register_pattern(pattern, pattern_key)
                return pattern

        return None

    # ========================================================================
    # TREND PATTERN DETECTION
    # ========================================================================

    def _detect_trend_pattern(self) -> Optional[Pattern]:
        """Trend pattern'i tespit et (iyilesme/bozulma)."""
        if len(self._duration_history) < self.config.medium_window:
            return None

        recent = self._duration_history[-self.config.medium_window:]
        first_half = [d for _, d in recent[:len(recent)//2]]
        second_half = [d for _, d in recent[len(recent)//2:]]

        if not first_half or not second_half:
            return None

        avg_first = statistics.mean(first_half)
        avg_second = statistics.mean(second_half)

        if avg_first == 0:
            return None

        change_percent = ((avg_second - avg_first) / avg_first) * 100

        # Degisim yeterli mi?
        if abs(change_percent) < self.config.degradation_threshold * 100:
            return None

        if change_percent > 0:
            pattern_type = PatternType.DEGRADATION
            pattern_name = "Performance Degradation"
            description = f"Performance degraded by {change_percent:.1f}% over {len(recent)} cycles"
        else:
            pattern_type = PatternType.IMPROVEMENT
            pattern_name = "Performance Improvement"
            description = f"Performance improved by {abs(change_percent):.1f}% over {len(recent)} cycles"

        pattern_key = f"trend_{pattern_type.value}"

        # Ayni trend zaten var mi?
        if pattern_key in self._patterns:
            self._patterns[pattern_key].average_impact = change_percent
            cycle_id = recent[-1][0]
            self._patterns[pattern_key].update_occurrence(cycle_id, change_percent)
            return None
        else:
            pattern = Pattern(
                pattern_type=pattern_type,
                name=pattern_name,
                description=description,
                affected_metric="duration_ms",
                average_impact=change_percent,
                confidence=0.75,
                stability=0.6,
            )
            cycle_id = recent[-1][0]
            pattern.update_occurrence(cycle_id, change_percent)

            self._register_pattern(pattern, pattern_key)
            return pattern

    # ========================================================================
    # OSCILLATION DETECTION
    # ========================================================================

    def _detect_oscillation(self) -> Optional[Pattern]:
        """Salinti pattern'i tespit et."""
        if len(self._duration_history) < self.config.short_window:
            return None

        recent = [d for _, d in self._duration_history[-self.config.short_window:]]

        # Yon degisimi say
        direction_changes = 0
        for i in range(1, len(recent) - 1):
            if (recent[i] > recent[i-1] and recent[i] > recent[i+1]) or \
               (recent[i] < recent[i-1] and recent[i] < recent[i+1]):
                direction_changes += 1

        # Cok fazla yon degisimi = oscillation
        oscillation_rate = direction_changes / (len(recent) - 2) if len(recent) > 2 else 0

        if oscillation_rate > 0.5:  # %50+ yon degisimi
            pattern_key = "oscillation"

            if pattern_key in self._patterns:
                self._patterns[pattern_key].frequency = oscillation_rate
                cycle_id = self._duration_history[-1][0]
                self._patterns[pattern_key].update_occurrence(cycle_id)
                return None
            else:
                avg = statistics.mean(recent)
                stdev = statistics.stdev(recent) if len(recent) > 1 else 0

                pattern = Pattern(
                    pattern_type=PatternType.OSCILLATION,
                    name="Performance Oscillation",
                    description=f"Duration oscillating around {avg:.1f}ms (stdev: {stdev:.1f}ms)",
                    affected_metric="duration_ms",
                    average_impact=stdev,
                    frequency=oscillation_rate,
                    confidence=0.7,
                )
                cycle_id = self._duration_history[-1][0]
                pattern.update_occurrence(cycle_id, stdev)

                self._register_pattern(pattern, pattern_key)
                return pattern

        return None

    # ========================================================================
    # STABILITY DETECTION
    # ========================================================================

    def _detect_stability(self) -> Optional[Pattern]:
        """Kararlilik pattern'i tespit et."""
        if len(self._duration_history) < self.config.min_stability_samples:
            return None

        recent = [d for _, d in self._duration_history[-self.config.min_stability_samples:]]

        avg = statistics.mean(recent)
        if avg == 0:
            return None

        stdev = statistics.stdev(recent) if len(recent) > 1 else 0
        cv = stdev / avg  # Coefficient of variation

        # Dusuk CV = yuksek kararlilik
        stability = 1.0 - min(1.0, cv)

        if stability >= self.config.stability_threshold:
            pattern_key = "stability"

            if pattern_key in self._patterns:
                self._patterns[pattern_key].stability = stability
                cycle_id = self._duration_history[-1][0]
                self._patterns[pattern_key].update_occurrence(cycle_id)
                return None
            else:
                pattern = Pattern(
                    pattern_type=PatternType.STABILITY,
                    name="Stable Performance",
                    description=f"Performance is stable around {avg:.1f}ms (CV: {cv:.2f})",
                    affected_metric="duration_ms",
                    average_impact=avg,
                    stability=stability,
                    confidence=0.85,
                )
                cycle_id = self._duration_history[-1][0]
                pattern.update_occurrence(cycle_id, stability)

                self._register_pattern(pattern, pattern_key)
                return pattern

        return None

    # ========================================================================
    # PATTERN MANAGEMENT
    # ========================================================================

    def _register_pattern(self, pattern: Pattern, key: str) -> None:
        """Pattern'i kaydet."""
        self._patterns[key] = pattern
        self._patterns_detected += 1

        # Limit kontrolu
        if len(self._patterns) > self.config.max_patterns:
            self._cleanup_old_patterns()

    def _cleanup_old_patterns(self) -> None:
        """Eski pattern'leri temizle."""
        now = datetime.now()
        max_age = timedelta(hours=self.config.pattern_max_age_hours)

        # Eski veya az gorulenleri sil
        to_remove = []
        for key, pattern in self._patterns.items():
            # Cok eski
            if pattern.last_seen and (now - pattern.last_seen) > max_age:
                to_remove.append(key)
            # Az gorulen ve stabil olmayan
            elif pattern.occurrence_count < self.config.min_occurrences and pattern.stability < 0.5:
                to_remove.append(key)

        for key in to_remove:
            del self._patterns[key]

    def get_pattern(self, pattern_id: str) -> Optional[Pattern]:
        """Pattern getir."""
        for pattern in self._patterns.values():
            if pattern.id == pattern_id:
                return pattern
        return None

    def get_patterns_by_type(self, pattern_type: PatternType) -> List[Pattern]:
        """Ture gore pattern'leri getir."""
        return [p for p in self._patterns.values() if p.pattern_type == pattern_type]

    def get_all_patterns(self) -> List[Pattern]:
        """Tum pattern'leri getir."""
        return sorted(
            self._patterns.values(),
            key=lambda p: (p.occurrence_count, p.confidence),
            reverse=True,
        )

    def get_significant_patterns(
        self,
        min_occurrences: int = 5,
        min_confidence: float = 0.7,
    ) -> List[Pattern]:
        """Onemli pattern'leri getir."""
        return [
            p for p in self._patterns.values()
            if p.occurrence_count >= min_occurrences and p.confidence >= min_confidence
        ]

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Istatistikleri getir."""
        patterns = list(self._patterns.values())

        by_type = {}
        for p in patterns:
            t = p.pattern_type.value
            by_type[t] = by_type.get(t, 0) + 1

        return {
            "patterns_detected": self._patterns_detected,
            "active_patterns": len(patterns),
            "cycles_processed": self._cycles_processed,
            "by_type": by_type,
        }

    def summary(self) -> Dict[str, Any]:
        """Genel ozet."""
        patterns = self.get_all_patterns()

        return {
            "active_patterns": len(patterns),
            "total_detected": self._patterns_detected,
            "significant_patterns": len(self.get_significant_patterns()),
            "top_patterns": [p.to_dict() for p in patterns[:5]],
        }


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_pattern_detector(
    config: Optional[PatternDetectorConfig] = None,
) -> PatternDetector:
    """PatternDetector factory."""
    return PatternDetector(config)


_default_detector: Optional[PatternDetector] = None


def get_pattern_detector() -> PatternDetector:
    """Default PatternDetector getir."""
    global _default_detector
    if _default_detector is None:
        _default_detector = PatternDetector()
    return _default_detector


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "PatternDetectorConfig",
    "PatternDetector",
    "create_pattern_detector",
    "get_pattern_detector",
]
