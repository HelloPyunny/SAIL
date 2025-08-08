from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from enum import Enum
import json
from datetime import datetime

class Stage(Enum):
    TUTORIAL = 1
    STAGE_2 = 2
    STAGE_3 = 3
    STAGE_4 = 4
    STAGE_5 = 5
    STAGE_6 = 6
    STAGE_7 = 7
    BOSS = 8

class PlayerInfo(BaseModel):
    # basic information (collected in tutorial)
    name: str = ""
    age: Optional[int] = None
    location: str = ""
    occupation: str = ""
    personality_traits: List[str] = []
    likes: List[str] = []  # interests, hobbies, things you like
    life_goal: str = ""  # life goal (collected in tutorial)
    
    # fears (collected in stage 2)
    fears: List[str] = []
    
    # background (collected in stage 3)
    background: str = ""
    
    # additional information (collected in stage 3)
    extra_info: List[str] = []
    
    def to_dict(self) -> Dict[str, Any]:
        return self.dict()
    
    def get_collection_status(self) -> Dict[str, bool]:
        """returns the collection status of each stage"""
        return {
            "tutorial_complete": bool(self.name and self.location and self.occupation and self.personality_traits and self.likes),
            "stage2_complete": bool(self.fears),
            "stage3_complete": bool(self.background)
        }

class GameState(BaseModel):
    player_id: Optional[str] = None  # player ID
    current_stage: Stage = Stage.TUTORIAL
    player_info: PlayerInfo = PlayerInfo()
    stage_progress: Dict[int, bool] = {i: False for i in range(1, 9)}
    conversation_history: List[Dict[str, str]] = []
    current_map: Optional[str] = None
    boss_goal: Optional[str] = None
    game_started: bool = False
    game_completed: bool = False

    monster_defeated: bool = False  # monster defeated status (updated by frontend)
    
    # track elements used for map recommendation (to avoid duplicates)
    used_map_elements: Dict[str, List[str]] = {
        "personality_traits": [],
        "likes": [],
        "fears": [],
        "locations": [],
        "occupations": [],
        "life_goals": [],
        "backgrounds": []
    }
    
    def add_conversation(self, speaker: str, message: str):
        """adds conversation history"""
        self.conversation_history.append({
            "speaker": speaker,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    def update_player_info(self, **kwargs):
        """updates player info"""
        for key, value in kwargs.items():
            if hasattr(self.player_info, key):
                setattr(self.player_info, key, value)
    
    def advance_stage(self):
        """advances to the next stage"""
        current_num = self.current_stage.value
        if current_num < 8:
            self.stage_progress[current_num] = True
            self.current_stage = Stage(current_num + 1)
    
    def get_stage_context(self) -> Dict[str, Any]:
        """returns the context of the current stage"""
        return {
            "stage": self.current_stage.value,
            "stage_name": self.current_stage.name,
            "player_info": self.player_info.to_dict(),
            "conversation_history": self.conversation_history[-15:],  # last 15 conversations
            "current_map": self.current_map,
            "boss_goal": self.boss_goal
        } 