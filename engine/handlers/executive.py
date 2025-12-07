"""
UEM v2 - Executive Phase Handlers

Cognitive Cycle'ın DECIDE ve ACT fazları için handler'lar.
StateVector'dan okuyarak karar verir ve action seçer.

Kullanım:
    from engine.handlers.executive import create_decide_handler, create_act_handler
    
    cycle = CognitiveCycle()
    cycle.register_handler(Phase.DECIDE, create_decide_handler())
    cycle.register_handler(Phase.ACT, create_act_handler())
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import logging

import sys
sys.path.insert(0, '.')

from foundation.state import StateVector, SVField
from foundation.types import Context, Action, ActionCategory, ActionOutcome
from engine.phases import Phase, PhaseResult

logger = logging.getLogger(__name__)


@dataclass
class ExecutiveConfig:
    """Executive fazları yapılandırması."""
    
    # Karar eşikleri
    threat_flee_threshold: float = 0.7      # Bu üstünde kaç
    threat_observe_threshold: float = 0.3   # Bu üstünde gözle
    
    trust_help_threshold: float = 0.4       # Bu üstünde yardım et
    empathy_engage_threshold: float = 0.5   # Bu üstünde etkileşim
    
    # Action seçimi
    use_orchestrator_suggestion: bool = True  # Orchestrator önerisini kullan
    
    # Risk değerlendirme
    consider_trust_for_action: bool = True
    low_trust_caution: float = 0.3  # Trust bu altındaysa dikkatli ol


# Action tanımları
AVAILABLE_ACTIONS = {
    "flee": Action(
        action_id="flee",
        category=ActionCategory.MOTOR,
        name="flee",
        priority=1.0,
        expected_duration_ms=500,
    ),
    "observe": Action(
        action_id="observe",
        category=ActionCategory.COGNITIVE,
        name="observe",
        priority=0.5,
        expected_duration_ms=200,
    ),
    "approach": Action(
        action_id="approach",
        category=ActionCategory.MOTOR,
        name="approach",
        priority=0.6,
        expected_duration_ms=300,
    ),
    "help": Action(
        action_id="help",
        category=ActionCategory.SOCIAL,
        name="help",
        priority=0.7,
        expected_duration_ms=1000,
    ),
    "greet": Action(
        action_id="greet",
        category=ActionCategory.VERBAL,
        name="greet",
        priority=0.4,
        expected_duration_ms=100,
    ),
    "avoid": Action(
        action_id="avoid",
        category=ActionCategory.MOTOR,
        name="avoid",
        priority=0.8,
        expected_duration_ms=300,
    ),
    "defend": Action(
        action_id="defend",
        category=ActionCategory.MOTOR,
        name="defend",
        priority=0.9,
        expected_duration_ms=500,
    ),
    "celebrate": Action(
        action_id="celebrate",
        category=ActionCategory.SOCIAL,
        name="celebrate",
        priority=0.5,
        expected_duration_ms=200,
    ),
    "wait": Action(
        action_id="wait",
        category=ActionCategory.WAIT,
        name="wait",
        priority=0.2,
        expected_duration_ms=1000,
    ),
    "comfort": Action(
        action_id="comfort",
        category=ActionCategory.SOCIAL,
        name="comfort",
        priority=0.6,
        expected_duration_ms=500,
    ),
    "celebrate": Action(
        action_id="celebrate",
        category=ActionCategory.SOCIAL,
        name="celebrate",
        priority=0.6,
        expected_duration_ms=300,
    ),
    "congratulate": Action(
        action_id="congratulate",
        category=ActionCategory.VERBAL,
        name="congratulate",
        priority=0.5,
        expected_duration_ms=100,
    ),
}


class DecidePhaseHandler:
    """
    DECIDE fazı handler'ı.
    
    StateVector'dan değerleri okuyarak karar verir:
    - Threat → flee/avoid/defend
    - Empathy + Trust → help/comfort
    - Low threat → observe/approach/greet
    """
    
    def __init__(self, config: Optional[ExecutiveConfig] = None):
        self.config = config or ExecutiveConfig()
    
    def __call__(
        self,
        phase: Phase,
        state: StateVector,
        context: Context,
    ) -> PhaseResult:
        """DECIDE fazını çalıştır."""
        
        # StateVector'dan değerleri oku
        threat = state.threat
        trust = state.get(SVField.TRUST_VALUE, 0.5)
        empathy = state.get(SVField.EMPATHY_TOTAL, 0.0)
        sympathy_level = state.get(SVField.SYMPATHY_LEVEL, 0.0)
        sympathy_valence = state.get(SVField.SYMPATHY_VALENCE, 0.5)
        valence = state.get(SVField.VALENCE, 0.5)
        
        # Orchestrator önerisi (varsa)
        orchestrator_suggestion = None
        if self.config.use_orchestrator_suggestion:
            # FEEL fazından gelen öneri
            feel_result = context.metadata.get("phase_results", {}).get(Phase.FEEL)
            if feel_result and feel_result.output:
                orchestrator_suggestion = feel_result.output.get("suggested_action")
        
        # Karar ver
        action_name, confidence, reasoning = self._decide_action(
            threat=threat,
            trust=trust,
            empathy=empathy,
            sympathy_level=sympathy_level,
            sympathy_valence=sympathy_valence,
            valence=valence,
            orchestrator_suggestion=orchestrator_suggestion,
        )
        
        # Action oluştur
        action = AVAILABLE_ACTIONS.get(action_name, AVAILABLE_ACTIONS["observe"]).to_dict()
        action["confidence"] = confidence
        
        # Context'e kaydet (ACT için)
        context.metadata["selected_action"] = action_name
        context.metadata["action_confidence"] = confidence
        context.metadata["action_reasoning"] = reasoning
        
        output = {
            "action": action_name,
            "confidence": confidence,
            "reasoning": reasoning,
            "inputs": {
                "threat": threat,
                "trust": trust,
                "empathy": empathy,
                "sympathy": sympathy_level,
                "valence": valence,
            },
        }
        
        logger.debug(f"Decision: {action_name} (conf={confidence:.2f})")
        
        return PhaseResult(
            phase=phase,
            success=True,
            output=output,
        )
    
    def _decide_action(
        self,
        threat: float,
        trust: float,
        empathy: float,
        sympathy_level: float,
        sympathy_valence: float,
        valence: float,
        orchestrator_suggestion: Optional[str],
    ) -> Tuple[str, float, str]:
        """
        Action seç.
        
        Returns:
            (action_name, confidence, reasoning)
        """
        
        # 1. Yüksek threat → flee/defend
        if threat > self.config.threat_flee_threshold:
            if trust < 0.3:  # Güvensiz → kaç
                return "flee", 0.9, f"High threat ({threat:.2f}), low trust → flee"
            else:  # Güvenilir → savun
                return "defend", 0.8, f"High threat ({threat:.2f}), has trust → defend"
        
        # 2. Orta threat → avoid/observe
        if threat > self.config.threat_observe_threshold:
            if trust < 0.4:
                return "avoid", 0.7, f"Moderate threat ({threat:.2f}), low trust → avoid"
            else:
                return "observe", 0.6, f"Moderate threat ({threat:.2f}) → observe"
        
        # 3. Düşük threat - sosyal kararlar
        
        # Orchestrator önerisini değerlendir
        if orchestrator_suggestion and orchestrator_suggestion != "observe":
            # Trust ile modüle et
            if self.config.consider_trust_for_action:
                if trust < self.config.low_trust_caution:
                    # Düşük trust → dikkatli ol
                    if orchestrator_suggestion in ["help", "comfort", "approach"]:
                        return "observe", 0.5, f"Orchestrator suggests {orchestrator_suggestion}, but low trust → observe first"
            
            # Öneriyi kabul et
            confidence = 0.7 + (trust * 0.2)  # Trust artarsa confidence artar
            return orchestrator_suggestion, confidence, f"Following orchestrator: {orchestrator_suggestion}"
        
        # 4. Empathy + Trust - sympathy valence'a göre farklı tepkiler
        if empathy > self.config.empathy_engage_threshold and trust > self.config.trust_help_threshold:
            if sympathy_valence > 0.6:  # Prosocial
                # Valence'a göre help vs celebrate
                if valence > 0.6:
                    # Pozitif durum → celebrate
                    return "celebrate", 0.7, f"High empathy ({empathy:.2f}), positive valence ({valence:.2f}) → celebrate"
                elif sympathy_level > 0.5:
                    # Negatif durum ama yüksek sempati → help
                    return "help", 0.7, f"High empathy ({empathy:.2f}), prosocial sympathy → help"
                else:
                    return "comfort", 0.6, f"High empathy ({empathy:.2f}), moderate sympathy → comfort"
            else:  # Antisocial veya nötr
                return "observe", 0.5, f"High empathy but low sympathy valence → observe"
        
        # 5. Pozitif valence → approach/greet
        if valence > 0.6:
            if trust > 0.5:
                return "approach", 0.6, f"Positive valence ({valence:.2f}), good trust → approach"
            else:
                return "greet", 0.5, f"Positive valence ({valence:.2f}) → greet"
        
        # 6. Default → observe
        return "observe", 0.4, "Default action"


class ActPhaseHandler:
    """
    ACT fazı handler'ı.
    
    DECIDE'da seçilen action'ı "execute" eder.
    Gerçek execution şimdilik simüle edilir.
    """
    
    def __call__(
        self,
        phase: Phase,
        state: StateVector,
        context: Context,
    ) -> PhaseResult:
        """ACT fazını çalıştır."""
        
        # Seçilen action
        action_name = context.metadata.get("selected_action", "wait")
        confidence = context.metadata.get("action_confidence", 0.5)
        
        # Simüle et (gerçek execution yok)
        success = True
        
        # Action'ın StateVector'a etkisi
        self._apply_action_effects(action_name, state)
        
        output = {
            "executed_action": action_name,
            "confidence": confidence,
            "success": success,
        }
        
        logger.debug(f"Executed: {action_name}")
        
        return PhaseResult(
            phase=phase,
            success=True,
            output=output,
        )
    
    def _apply_action_effects(
        self,
        action_name: str,
        state: StateVector,
    ) -> None:
        """Action'ın StateVector'a etkisini uygula."""
        
        # Flee/avoid → threat düşer (uzaklaştık)
        if action_name in ["flee", "avoid"]:
            state.threat = max(0.0, state.threat - 0.3)
        
        # Help/comfort → wellbeing artar
        elif action_name in ["help", "comfort"]:
            state.wellbeing = min(1.0, state.wellbeing + 0.1)
            # Sosyal engagement artar
            engagement = state.get(SVField.SOCIAL_ENGAGEMENT, 0.5)
            state.set(SVField.SOCIAL_ENGAGEMENT, min(1.0, engagement + 0.1))
        
        # Observe → attention artar
        elif action_name == "observe":
            attention = state.get(SVField.ATTENTION_FOCUS, 0.5)
            state.set(SVField.ATTENTION_FOCUS, min(1.0, attention + 0.1))
        
        # Approach/greet → sosyal engagement
        elif action_name in ["approach", "greet"]:
            engagement = state.get(SVField.SOCIAL_ENGAGEMENT, 0.5)
            state.set(SVField.SOCIAL_ENGAGEMENT, min(1.0, engagement + 0.15))
        
        # Celebrate/congratulate → valence ve engagement artar
        elif action_name in ["celebrate", "congratulate"]:
            valence = state.get(SVField.VALENCE, 0.5)
            state.set(SVField.VALENCE, min(1.0, valence + 0.15))
            engagement = state.get(SVField.SOCIAL_ENGAGEMENT, 0.5)
            state.set(SVField.SOCIAL_ENGAGEMENT, min(1.0, engagement + 0.2))
            state.wellbeing = min(1.0, state.wellbeing + 0.1)
        
        # Defend → dominance artar
        elif action_name == "defend":
            dominance = state.get(SVField.DOMINANCE, 0.5)
            state.set(SVField.DOMINANCE, min(1.0, dominance + 0.2))


def create_decide_handler(
    config: Optional[ExecutiveConfig] = None,
) -> DecidePhaseHandler:
    """DECIDE fazı handler'ı oluştur."""
    return DecidePhaseHandler(config)


def create_act_handler() -> ActPhaseHandler:
    """ACT fazı handler'ı oluştur."""
    return ActPhaseHandler()
