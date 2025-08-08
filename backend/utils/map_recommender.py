from typing import Dict, List, Optional, Any
from utils.game_state import PlayerInfo, GameState
from services.map_generator import MapGenerator
import json
from datetime import datetime
import os

class MapRecommender:
    def __init__(self):
        self.map_generator = MapGenerator()
        self.used_ai_maps = set()  # track AI generated maps
        self.recommendation_history = []  # map recommendation history
        self.recommendation_log_file = "static/generated_maps/recommendation_history.json"
        
        # initialize recommendation log file
        self._init_recommendation_log()
    
    def _init_recommendation_log(self):
        """initialize recommendation log file"""
        os.makedirs(os.path.dirname(self.recommendation_log_file), exist_ok=True)
        if not os.path.exists(self.recommendation_log_file):
            with open(self.recommendation_log_file, 'w', encoding='utf-8') as f:
                json.dump({"recommendations": []}, f, ensure_ascii=False, indent=2)
    
    def recommend_map(self, game_state: GameState) -> Dict[str, str]:
        """recommend a map based on the player's information"""
        current_stage = game_state.current_stage.value
        
        # handle tutorial map
        if current_stage == 1:
            tutorial_map = self._get_tutorial_map()
            self._log_recommendation(tutorial_map, game_state, "tutorial")
            return tutorial_map
        
        # generate AI map
        conversation_history = game_state.conversation_history
        ai_map = self.map_generator.generate_map_for_player(game_state, current_stage)
        
        # avoid duplicate AI maps
        if ai_map["map_id"] in self.used_ai_maps:
            print(f"⚠️ AI map duplicate detected: {ai_map['name']}")
            # try generating a new map
            ai_map = self.map_generator.generate_map_for_player(game_state, current_stage)
        
        # track used AI maps
        self.used_ai_maps.add(ai_map["map_id"])
        self._log_recommendation(ai_map, game_state, "ai_generated")
        
        return ai_map
    
    def _log_recommendation(self, map_data: Dict[str, Any], game_state: GameState, source: str):
        """log map recommendation"""
        recommendation_record = {
            "timestamp": datetime.now().isoformat(),
            "player_id": getattr(game_state, 'player_id', 'unknown'),
            "player_name": game_state.player_info.name,
            "stage": game_state.current_stage.value,
            "map_id": map_data.get("map_id", "unknown"),
            "map_name": map_data.get("name", "unknown"),
            "source": source,
            "player_info": {
                "name": game_state.player_info.name,
                "location": game_state.player_info.location,
                "likes": game_state.player_info.likes,
                "personality_traits": game_state.player_info.personality_traits,
                "life_goal": game_state.player_info.life_goal,
                "fears": game_state.player_info.fears
            }
        }
        
        # add additional information for AI generated maps
        if source == "ai_generated":
            recommendation_record["gpt_suggestion"] = map_data.get("gpt_suggestion", "")
        
        self.recommendation_history.append(recommendation_record)
        
        # save to file
        try:
            with open(self.recommendation_log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            data["recommendations"].append(recommendation_record)
            
            with open(self.recommendation_log_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ failed to save recommendation: {e}")
        
        print(f"✅ map recommendation: {map_data['name']} (stage {game_state.current_stage.value})")
    
    def _get_tutorial_map(self) -> Dict[str, str]:
        """return a fixed map for tutorial"""
        return {
            "map_id": "tutorial_meadow",
            "name": "tutorial meadow",
            "description": "a peaceful meadow where you can learn the basics of the game. you can learn the basics of the game in a safe and comfortable atmosphere.",
            "image_path": "https://your-s3-bucket.s3.amazonaws.com/tutorial_meadow.png"  # pre-uploaded tutorial image
        }
    
    def get_generated_maps(self) -> Dict[str, Any]:
        """return metadata of generated maps"""
        return self.map_generator.get_generated_maps()
    
    def reset_used_styles(self):
        """reset used styles"""
        self.map_generator.reset_used_styles()
    
    def reset_recommendation_history(self):
        """reset recommendation history"""
        self.recommendation_history.clear()
        self.used_ai_maps.clear()
        
        # reset file
        with open(self.recommendation_log_file, 'w', encoding='utf-8') as f:
            json.dump({"recommendations": []}, f, ensure_ascii=False, indent=2) 