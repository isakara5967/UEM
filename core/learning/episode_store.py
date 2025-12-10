"""
core/learning/episode_store.py

Faz 5 Episode Storage - JSONL-based persistence for EpisodeLogs.

EpisodeStore Protocol tanımlar storage interface'ini.
JSONLEpisodeStore JSONL formatında dosyaya yazıp okur.

Query capabilities:
- By ID (specific episode)
- By session (all turns in a session)
- By intent (all episodes with specific intent)
- By act (all episodes with specific dialogue act)
- Recent N episodes (time-ordered)

UEM v2 - Faz 5 Pattern Evolution Storage.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Protocol

from core.language.intent.types import IntentCategory
from core.language.dialogue.types import DialogueAct
from .episode_types import EpisodeLog


class EpisodeStore(Protocol):
    """
    Episode Store Protocol - Storage interface for EpisodeLogs.

    Implementations can use different backends (JSONL, SQLite, etc).
    """

    def save(self, episode: EpisodeLog) -> None:
        """
        Episode'u kaydet.

        Args:
            episode: Kaydedilecek EpisodeLog
        """
        ...

    def get_by_id(self, episode_id: str) -> Optional[EpisodeLog]:
        """
        ID'ye göre episode getir.

        Args:
            episode_id: Episode ID

        Returns:
            Optional[EpisodeLog]: Bulunan episode veya None
        """
        ...

    def get_recent(self, n: int = 10) -> List[EpisodeLog]:
        """
        Son N episode'u getir (zamana göre).

        Args:
            n: Getirilecek episode sayısı

        Returns:
            List[EpisodeLog]: Son N episode (yeniden eskiye)
        """
        ...

    def get_by_session(self, session_id: str) -> List[EpisodeLog]:
        """
        Session ID'ye göre tüm episode'ları getir.

        Args:
            session_id: Session ID

        Returns:
            List[EpisodeLog]: Session'a ait episode'lar (zamana göre sıralı)
        """
        ...

    def get_by_intent(self, intent: IntentCategory) -> List[EpisodeLog]:
        """
        Primary intent'e göre episode'ları getir.

        Args:
            intent: IntentCategory

        Returns:
            List[EpisodeLog]: Bu intent'e sahip episode'lar
        """
        ...

    def get_by_act(self, act: DialogueAct) -> List[EpisodeLog]:
        """
        Dialogue act'e göre episode'ları getir.

        Args:
            act: DialogueAct

        Returns:
            List[EpisodeLog]: Bu act'i kullanan episode'lar
        """
        ...


class JSONLEpisodeStore:
    """
    JSONL-based Episode Store - Her satır bir JSON episode.

    Format:
        {"id": "eplog_123", "session_id": "sess_456", ...}
        {"id": "eplog_124", "session_id": "sess_456", ...}
        ...

    Attributes:
        filepath: JSONL dosya yolu
    """

    def __init__(self, filepath: str = "data/episodes.jsonl"):
        """
        Initialize JSONL Episode Store.

        Args:
            filepath: JSONL dosya yolu (default: data/episodes.jsonl)
        """
        self.filepath = Path(filepath)
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Dosya ve dizin yoksa oluştur."""
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        if not self.filepath.exists():
            self.filepath.touch()

    def save(self, episode: EpisodeLog) -> None:
        """
        Episode'u JSONL dosyasına kaydet.

        Args:
            episode: Kaydedilecek EpisodeLog
        """
        episode_dict = episode.to_dict()

        with open(self.filepath, "a", encoding="utf-8") as f:
            json_line = json.dumps(episode_dict, ensure_ascii=False)
            f.write(json_line + "\n")

    def get_by_id(self, episode_id: str) -> Optional[EpisodeLog]:
        """
        ID'ye göre episode getir.

        Args:
            episode_id: Episode ID

        Returns:
            Optional[EpisodeLog]: Bulunan episode veya None
        """
        with open(self.filepath, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                data = json.loads(line)
                if data.get("id") == episode_id:
                    return EpisodeLog.from_dict(data)

        return None

    def get_recent(self, n: int = 10) -> List[EpisodeLog]:
        """
        Son N episode'u getir (zamana göre).

        Args:
            n: Getirilecek episode sayısı

        Returns:
            List[EpisodeLog]: Son N episode (yeniden eskiye)
        """
        episodes = []

        with open(self.filepath, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                data = json.loads(line)
                episode = EpisodeLog.from_dict(data)
                episodes.append(episode)

        # Zamana göre sırala (yeniden eskiye)
        episodes.sort(key=lambda e: e.timestamp, reverse=True)

        return episodes[:n]

    def get_by_session(self, session_id: str) -> List[EpisodeLog]:
        """
        Session ID'ye göre tüm episode'ları getir.

        Args:
            session_id: Session ID

        Returns:
            List[EpisodeLog]: Session'a ait episode'lar (zamana göre sıralı)
        """
        episodes = []

        with open(self.filepath, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                data = json.loads(line)
                if data.get("session_id") == session_id:
                    episode = EpisodeLog.from_dict(data)
                    episodes.append(episode)

        # Zamana göre sırala (eskiden yeniye - turn order)
        episodes.sort(key=lambda e: e.timestamp)

        return episodes

    def get_by_intent(self, intent: IntentCategory) -> List[EpisodeLog]:
        """
        Primary intent'e göre episode'ları getir.

        Args:
            intent: IntentCategory

        Returns:
            List[EpisodeLog]: Bu intent'e sahip episode'lar
        """
        episodes = []
        intent_value = intent.value

        with open(self.filepath, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                data = json.loads(line)
                if data.get("intent_primary") == intent_value:
                    episode = EpisodeLog.from_dict(data)
                    episodes.append(episode)

        # Zamana göre sırala (yeniden eskiye)
        episodes.sort(key=lambda e: e.timestamp, reverse=True)

        return episodes

    def get_by_act(self, act: DialogueAct) -> List[EpisodeLog]:
        """
        Dialogue act'e göre episode'ları getir.

        Args:
            act: DialogueAct

        Returns:
            List[EpisodeLog]: Bu act'i kullanan episode'lar
        """
        episodes = []
        act_value = act.value

        with open(self.filepath, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                data = json.loads(line)
                if data.get("dialogue_act_selected") == act_value:
                    episode = EpisodeLog.from_dict(data)
                    episodes.append(episode)

        # Zamana göre sırala (yeniden eskiye)
        episodes.sort(key=lambda e: e.timestamp, reverse=True)

        return episodes

    def get_all(self) -> List[EpisodeLog]:
        """
        Tüm episode'ları getir.

        Returns:
            List[EpisodeLog]: Tüm episode'lar (zamana göre sıralı)
        """
        episodes = []

        with open(self.filepath, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                data = json.loads(line)
                episode = EpisodeLog.from_dict(data)
                episodes.append(episode)

        # Zamana göre sırala (eskiden yeniye)
        episodes.sort(key=lambda e: e.timestamp)

        return episodes

    def count(self) -> int:
        """
        Toplam episode sayısı.

        Returns:
            int: Episode sayısı
        """
        count = 0

        with open(self.filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    count += 1

        return count

    def clear(self) -> None:
        """Tüm episode'ları sil (testing için)."""
        with open(self.filepath, "w", encoding="utf-8") as f:
            pass

    def update_episode(self, episode_id: str, updates: dict) -> bool:
        """
        Episode'u güncelle (feedback eklemek için).

        JSONL dosyasını okur, ilgili episode'u günceller ve yeniden yazar.

        Args:
            episode_id: Güncellenecek episode ID
            updates: Güncellenecek alanlar (dict)

        Returns:
            bool: Başarılı ise True, episode bulunamazsa False
        """
        # Tüm satırları oku
        lines = []
        found = False

        with open(self.filepath, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                lines.append(line)

        # Episode'u bul ve güncelle
        updated_lines = []
        for line in lines:
            data = json.loads(line)
            if data.get("id") == episode_id:
                # Bu episode'u güncelle
                data.update(updates)
                found = True
                updated_lines.append(json.dumps(data, ensure_ascii=False) + "\n")
            else:
                updated_lines.append(line)

        if not found:
            return False

        # Dosyayı yeniden yaz
        with open(self.filepath, "w", encoding="utf-8") as f:
            f.writelines(updated_lines)

        return True
