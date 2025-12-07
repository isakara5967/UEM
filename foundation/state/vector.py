"""
UEM v2 - StateVector

Ajanın iç durumunu temsil eden genişletilebilir vektör.
Core + Extensions pattern: Core sabit, extensions dinamik.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Iterator
from copy import deepcopy

from .fields import SVField


@dataclass
class StateVector:
    """
    Genişletilebilir StateVector.
    
    Core alanlar (3): resource, threat, wellbeing - asla değişmez
    Extensions: Dinamik, SVField enum korumalı
    
    Usage:
        state = StateVector(resource=0.8, threat=0.2)
        state.set(SVField.AROUSAL, 0.5)
        arousal = state.get(SVField.AROUSAL)
    """
    
    # ══════════════════════════════════════════════════════════════════
    # CORE FIELDS - Asla değişmez
    # ══════════════════════════════════════════════════════════════════
    resource: float = 0.5
    threat: float = 0.0
    wellbeing: float = 0.5
    
    # ══════════════════════════════════════════════════════════════════
    # EXTENSIONS - Dinamik alanlar
    # ══════════════════════════════════════════════════════════════════
    _extensions: Dict[SVField, float] = field(default_factory=dict)
    
    # ══════════════════════════════════════════════════════════════════
    # METADATA
    # ══════════════════════════════════════════════════════════════════
    _timestamp: Optional[float] = None  # Oluşturma zamanı
    _cycle_id: Optional[int] = None     # Hangi cycle'da oluştu
    
    def __post_init__(self):
        """Değerleri normalize et."""
        self.resource = self._clamp(self.resource)
        self.threat = self._clamp(self.threat)
        self.wellbeing = self._clamp(self.wellbeing)
    
    @staticmethod
    def _clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """Değeri [min_val, max_val] aralığına sınırla."""
        return max(min_val, min(max_val, value))
    
    # ══════════════════════════════════════════════════════════════════
    # GETTER / SETTER
    # ══════════════════════════════════════════════════════════════════
    
    def get(self, key: SVField, default: float = 0.0) -> float:
        """
        Core veya extension alanına eriş.
        
        Args:
            key: SVField enum değeri
            default: Alan yoksa dönecek değer
            
        Returns:
            Alanın değeri veya default
        """
        # Core alanları kontrol et
        if key == SVField.RESOURCE:
            return self.resource
        elif key == SVField.THREAT:
            return self.threat
        elif key == SVField.WELLBEING:
            return self.wellbeing
        
        # Extension'larda ara
        return self._extensions.get(key, default)
    
    def set(self, key: SVField, value: float) -> None:
        """
        Extension alanı ekle veya güncelle.
        
        Core alanları (resource, threat, wellbeing) doğrudan attribute ile set et.
        
        Args:
            key: SVField enum değeri
            value: Yeni değer (0-1 aralığına normalize edilir)
        """
        normalized = self._clamp(value)
        
        # Core alanları için uyarı ver ama yine de set et
        if key == SVField.RESOURCE:
            self.resource = normalized
        elif key == SVField.THREAT:
            self.threat = normalized
        elif key == SVField.WELLBEING:
            self.wellbeing = normalized
        else:
            self._extensions[key] = normalized
    
    def has(self, key: SVField) -> bool:
        """Alan var mı kontrol et."""
        if key in SVField.core_fields():
            return True
        return key in self._extensions
    
    # ══════════════════════════════════════════════════════════════════
    # BULK OPERATIONS
    # ══════════════════════════════════════════════════════════════════
    
    def update(self, **kwargs: float) -> "StateVector":
        """
        Birden fazla alanı güncelle, yeni StateVector döndür.
        
        Args:
            **kwargs: field_name=value pairs (string keys)
            
        Returns:
            Yeni StateVector instance
        """
        new_state = self.copy()
        
        for key_str, value in kwargs.items():
            try:
                key = SVField(key_str)
                new_state.set(key, value)
            except ValueError:
                # Bilinmeyen alan, atla veya logla
                pass
        
        return new_state
    
    def to_dict(self) -> Dict[str, float]:
        """Tüm alanları dict olarak döndür."""
        result = {
            SVField.RESOURCE.value: self.resource,
            SVField.THREAT.value: self.threat,
            SVField.WELLBEING.value: self.wellbeing,
        }
        
        for key, value in self._extensions.items():
            result[key.value] = value
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "StateVector":
        """Dict'ten StateVector oluştur."""
        state = cls(
            resource=data.get(SVField.RESOURCE.value, 0.5),
            threat=data.get(SVField.THREAT.value, 0.0),
            wellbeing=data.get(SVField.WELLBEING.value, 0.5),
        )
        
        for key_str, value in data.items():
            try:
                key = SVField(key_str)
                if key not in SVField.core_fields():
                    state.set(key, value)
            except ValueError:
                pass
        
        return state
    
    def copy(self) -> "StateVector":
        """Derin kopya oluştur."""
        new_state = StateVector(
            resource=self.resource,
            threat=self.threat,
            wellbeing=self.wellbeing,
            _timestamp=self._timestamp,
            _cycle_id=self._cycle_id,
        )
        new_state._extensions = deepcopy(self._extensions)
        return new_state
    
    # ══════════════════════════════════════════════════════════════════
    # ARITHMETIC OPERATIONS
    # ══════════════════════════════════════════════════════════════════
    
    def delta(self, other: "StateVector") -> Dict[SVField, float]:
        """
        İki StateVector arasındaki farkı hesapla.
        
        Returns:
            {SVField: delta_value} dict
        """
        deltas = {}
        
        # Core fields
        deltas[SVField.RESOURCE] = self.resource - other.resource
        deltas[SVField.THREAT] = self.threat - other.threat
        deltas[SVField.WELLBEING] = self.wellbeing - other.wellbeing
        
        # Extensions - her iki tarafta olan alanlar
        all_keys = set(self._extensions.keys()) | set(other._extensions.keys())
        for key in all_keys:
            self_val = self.get(key, 0.0)
            other_val = other.get(key, 0.0)
            deltas[key] = self_val - other_val
        
        return deltas
    
    def magnitude(self) -> float:
        """StateVector'ün büyüklüğünü hesapla (Euclidean norm)."""
        values = list(self.to_dict().values())
        return sum(v ** 2 for v in values) ** 0.5
    
    # ══════════════════════════════════════════════════════════════════
    # REPRESENTATION
    # ══════════════════════════════════════════════════════════════════
    
    def __repr__(self) -> str:
        ext_str = ", ".join(f"{k.value}={v:.2f}" for k, v in self._extensions.items())
        base = f"StateVector(r={self.resource:.2f}, t={self.threat:.2f}, w={self.wellbeing:.2f}"
        if ext_str:
            return f"{base}, {ext_str})"
        return f"{base})"
    
    def __len__(self) -> int:
        """Toplam alan sayısı."""
        return 3 + len(self._extensions)
    
    def __iter__(self) -> Iterator[tuple[SVField, float]]:
        """Tüm alanları iterate et."""
        yield SVField.RESOURCE, self.resource
        yield SVField.THREAT, self.threat
        yield SVField.WELLBEING, self.wellbeing
        yield from self._extensions.items()
