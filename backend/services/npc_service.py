from openai import OpenAI
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv
from utils.game_state import GameState
from utils.map_recommender import MapRecommender
from vector_db.vector_store import VectorStore
from services.stage_manager import StageManager
from services.info_collector import InfoCollector
from services.prompt_builder import PromptBuilder

load_dotenv()

class NPCService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.map_recommender = MapRecommender()
        self.vector_store = VectorStore()
        
        # initialize new services
        self.stage_manager = StageManager()
        self.info_collector = InfoCollector()
        self.prompt_builder = PromptBuilder(self.stage_manager)
    
    def generate_response(self, player_message: str, game_state: GameState, player_id: str) -> str:
        """generate NPC response to player message"""
        
        # add player message to conversation history
        game_state.add_conversation("player", player_message)
        
        # save conversation to vector DB
        self.vector_store.add_conversation(player_id, {
            "speaker": "player",
            "message": player_message,
            "timestamp": game_state.conversation_history[-1]["timestamp"]
        })
        
        # check and guide info collection
        info_collection_response = self._check_and_guide_info_collection(game_state)
        if info_collection_response:
            print(f"🎯🎯🎯 info collection response: {info_collection_response[:100]}...")
            response = info_collection_response
        else:
            print(f"🎮🎮🎮 generate normal response")
            # generate response based on current stage
            response = self._generate_stage_specific_response(player_message, game_state, player_id)
        
        # add NPC response to conversation history
        game_state.add_conversation("npc", response)
        
        # save NPC response to vector DB
        self.vector_store.add_conversation(player_id, {
            "speaker": "npc",
            "message": response,
            "timestamp": game_state.conversation_history[-1]["timestamp"]
        })
        
        return response
    
    def _generate_stage_specific_response(self, player_message: str, game_state: GameState, player_id: str) -> str:
        """generate stage-specific response"""
        
        # search player history
        player_history = self.vector_store.get_player_history(player_id, limit=10)
        
        # build system prompt
        system_prompt = self.prompt_builder.build_system_prompt(game_state, player_history)
        user_prompt = self.prompt_builder.build_user_prompt(player_message, game_state)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def extract_player_info(self, player_message: str, game_state: GameState) -> Dict[str, Any]:
        """extract information from player message"""
        return self.info_collector.extract_player_info(player_message, game_state)
    
    def recommend_map_for_stage(self, game_state: GameState) -> Dict[str, str]:
        """recommend map based on current stage and player info"""
        return self.map_recommender.recommend_map(game_state)
    
    def _check_and_guide_info_collection(self, game_state: GameState) -> Optional[str]:
        """check and guide info collection"""
        
        print(f"\n🔍🔍🔍 check info collection status:")
        print(f"   current stage: {game_state.current_stage.value} ({game_state.current_stage.name})")
        
        # check missing info
        missing_info = self.stage_manager.get_missing_info_for_stage(game_state)
        
        print(f"   missing info: {missing_info}")
        
        if missing_info:
            print(f"   ✅ missing info found - generating AI question...")
            # generate AI question
            question = self.info_collector.generate_info_collection_question(game_state, missing_info)
            print(f"   💬 generated question: {question[:100]}...")
            return question
        else:
            print(f"   ✅ all required info collected")
        
        return None
    
    def generate_stage_intro(self, prompt: str, game_state: GameState, player_id: str) -> str:
        """generate stage intro message"""
        
        try:
            # search player history (latest 5)
            player_history = self.vector_store.get_player_history(player_id, limit=5)
            
            # build system prompt
            system_prompt = self.prompt_builder.build_stage_intro_prompt(game_state, player_history)
            
            # call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.8
            )
            
            stage_intro_message = response.choices[0].message.content.strip()
            
            # add generated message to conversation history
            game_state.add_conversation("npc", stage_intro_message)
            
            # save stage intro message to vector DB
            self.vector_store.add_conversation(player_id, {
                "speaker": "npc",
                "message": stage_intro_message,
                "timestamp": game_state.conversation_history[-1]["timestamp"],
                "type": "stage_intro"
            })
            
            print(f"✅✅✅ stage intro message: {stage_intro_message}")
            return stage_intro_message
            
        except Exception as e:
            print(f"❌❌❌ stage intro message generation error: {e}")
            # fallback message
            return f"""
congratulations! you have completed {game_state.current_stage.value - 1} stages!

now {game_state.current_stage.value} stage. your personal journey continues.
you will experience even more special adventures through new adventures.
""" 