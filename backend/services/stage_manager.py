from typing import List
from utils.game_state import GameState, Stage
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

class StageManager:
    """manage stage-specific logic"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # define stage-specific instructions
        self.stage_instructions = {
            Stage.TUTORIAL: self._get_tutorial_instructions(),
            Stage.STAGE_2: self._get_stage2_instructions(),
            Stage.STAGE_3: self._get_stage3_instructions(),
            Stage.STAGE_4: self._get_stage4_instructions(),
            Stage.STAGE_5: self._get_stage5_instructions(),
            Stage.STAGE_6: self._get_stage6_instructions(),
            Stage.STAGE_7: self._get_stage7_instructions(),
            Stage.BOSS: self._get_boss_instructions()
        }
    
    def get_stage_instructions(self, stage: Stage) -> str:
        """return instructions for the current stage"""
        return self.stage_instructions.get(stage, "")
    
    def get_missing_info_for_stage(self, game_state: GameState) -> List[str]:
        """return missing information for the current stage"""
        current_stage = game_state.current_stage
        player_info = game_state.player_info
        missing_info = []
        
        if current_stage == Stage.TUTORIAL:
            if not player_info.name:
                missing_info.append("name")
            if not player_info.age:
                missing_info.append("age")
            if not player_info.location:
                missing_info.append("location")
            if not player_info.occupation:
                missing_info.append("occupation")
            if not player_info.life_goal:
                missing_info.append("life goal")
            
            # check personality_traits count (at least 3)
            if not player_info.personality_traits:
                missing_info.append("personality")
            elif len(player_info.personality_traits) < 3:
                missing_info.append("personality (more specific)")
            
            # check likes count (at least 4)
            if not player_info.likes:
                missing_info.append("likes/hobbies")
            elif len(player_info.likes) < 4:
                missing_info.append("likes/hobbies (more specific)")
        
        elif current_stage == Stage.STAGE_2:
            if not player_info.fears:
                missing_info.append("fears")
        
        elif current_stage == Stage.STAGE_3:
            if not player_info.background:
                missing_info.append("background")
        
        return missing_info
    
    def is_stage_complete(self, game_state: GameState) -> bool:
        """check if the current stage is complete"""
        current_stage = game_state.current_stage
        player_info = game_state.player_info
        
        print(f"\n🎯🎯🎯 check stage completion status (StageManager):")
        print(f"   current stage: {current_stage.value} ({current_stage.name})")
        
        if current_stage == Stage.TUTORIAL:
            # tutorial collects all basic information (name, age, location, occupation, personality, likes, life goal)
            required_fields = {
                "name": player_info.name,
                "age": player_info.age,
                "location": player_info.location,
                "occupation": player_info.occupation,
                "personality_traits": player_info.personality_traits,
                "likes": player_info.likes,
                "life_goal": player_info.life_goal
            }
            
            basic_info_complete = all(required_fields.values())
            
            print(f"   check required fields for tutorial:")
            for field, value in required_fields.items():
                status = "✅" if value else "❌"
                print(f"     {status} {field}: {value}")
            
            # check if likes is at least 4
            has_enough_likes = len(player_info.likes) >= 4 if player_info.likes else False
            
            print(f"   check likes count:")
            print(f"     {'✅' if has_enough_likes else '❌'} likes 4 or more: {len(player_info.likes) if player_info.likes else 0} items")
            
            # check if personality_traits is at least 3
            has_enough_personality_traits = len(player_info.personality_traits) >= 3 if player_info.personality_traits else False
            
            print(f"   check personality_traits count:")
            print(f"     {'✅' if has_enough_personality_traits else '❌'} personality_traits 3 or more: {len(player_info.personality_traits) if player_info.personality_traits else 0} items")

            # check if all required information is collected
            if not basic_info_complete or not has_enough_likes or not has_enough_personality_traits:
                print(f"   result: ⏳ in progress (basic info incomplete or likes insufficient or personality_traits insufficient)")
                return False
            
            # check if the player actually responded (check recent 3 messages for player messages)
            recent_player_messages = [conv.get("message", "") for conv in game_state.conversation_history[-3:] if conv.get("speaker") == "player"]
            has_player_response = len(recent_player_messages) > 0
            
            print(f"   check player response:")
            print(f"     {'✅' if has_player_response else '❌'} player response found in recent messages ({len(recent_player_messages)} items)")
            
            is_complete = (basic_info_complete and has_enough_likes and has_enough_personality_traits and has_player_response)
            print(f"   result: {'🎉 completed' if is_complete else '⏳ in progress'}")
            return is_complete
        
        elif current_stage == Stage.STAGE_2:
            # check if the monster is defeated (always true)
            monster_defeated = hasattr(game_state, 'monster_defeated') and game_state.monster_defeated
            
            # check if the required information is collected
            has_fears = bool(player_info.fears)
            
            print(f"   check stage 2 completion conditions:")
            print(f"     {'✅' if monster_defeated else '❌'} monster defeated (always true)")
            print(f"     {'✅' if has_fears else '❌'} fears collected: {player_info.fears}")
            
            # check if the player actually responded
            recent_player_messages = [conv.get("message", "") for conv in game_state.conversation_history[-3:] if conv.get("speaker") == "player"]
            has_player_response = len(recent_player_messages) > 0
            
            print(f"     {'✅' if has_player_response else '❌'} player response found in recent messages ({len(recent_player_messages)} items)")
            
            is_complete = monster_defeated and (has_fears and has_player_response)
            print(f"   result: {'🎉 completed' if is_complete else '⏳ in progress'}")
            return is_complete
        
        elif current_stage == Stage.STAGE_3:
            # check if the monster is defeated (always true)
            monster_defeated = hasattr(game_state, 'monster_defeated') and game_state.monster_defeated
            
            # check if the required information is collected
            has_background = bool(player_info.background)
            
            print(f"   check stage 3 completion conditions:")
            print(f"     {'✅' if monster_defeated else '❌'} monster defeated (always true)")
            print(f"     {'✅' if has_background else '❌'} background collected: {player_info.background}")
            
            # check if the player actually responded
            recent_player_messages = [conv.get("message", "") for conv in game_state.conversation_history[-3:] if conv.get("speaker") == "player"]
            has_player_response = len(recent_player_messages) > 0
            
            print(f"     {'✅' if has_player_response else '❌'} player response found in recent messages ({len(recent_player_messages)} items)")
            
            is_complete = monster_defeated and (has_background and has_player_response)
            print(f"   result: {'🎉 completed' if is_complete else '⏳ in progress'}")
            return is_complete
        
        elif current_stage in [Stage.STAGE_4, Stage.STAGE_5, Stage.STAGE_6, Stage.STAGE_7]:
            # check if the monster is defeated (always true)
            monster_defeated = hasattr(game_state, 'monster_defeated') and game_state.monster_defeated
            
            # check if the player actually responded
            recent_player_messages = [conv.get("message", "") for conv in game_state.conversation_history[-3:] if conv.get("speaker") == "player"]
            has_player_response = len(recent_player_messages) > 0
            
            print(f"   check stage {current_stage.value} completion conditions:")
            print(f"     {'✅' if monster_defeated else '❌'} monster defeated")
            print(f"     {'✅' if has_player_response else '❌'} player response found in recent messages ({len(recent_player_messages)} items)")
            
            is_complete = monster_defeated and has_player_response
            print(f"   result: {'🎉 completed' if is_complete else '⏳ in progress'}")
            return is_complete
        
        elif current_stage == Stage.BOSS:
            # check if the monster is defeated (always true)
            monster_defeated = hasattr(game_state, 'monster_defeated') and game_state.monster_defeated
            
            # check if the player actually responded
            recent_player_messages = [conv.get("message", "") for conv in game_state.conversation_history[-3:] if conv.get("speaker") == "player"]
            has_player_response = len(recent_player_messages) > 0
            
            print(f"   check boss stage completion conditions:")
            print(f"     {'✅' if monster_defeated else '❌'} monster defeated")
            print(f"     {'✅' if has_player_response else '❌'} player response found in recent messages ({len(recent_player_messages)} items)")
            
            is_complete = monster_defeated and has_player_response
            print(f"   result: {'🎉 completed' if is_complete else '⏳ in progress'}")
            return is_complete
        
        else:
            # unknown stage
            print(f"   unknown stage: {current_stage.value}")
            print(f"   result: ⏳ in progress")
            return False
    
    def _get_tutorial_instructions(self) -> str:
        return """
        currently 1st stage (tutorial). in this stage, you need to collect the player's basic information.
        
        please collect the following basic information:
        - player's name - required
        - age - required
        - location (city or region) - required
        - occupation - required
        - personality traits (personality, tendency, characteristics) - required (at least 3)
        - likes/hobbies (things you like, areas of interest, hobbies) - required (at least 4)
        - life goal (dreams or goals you want to achieve in the future) - required

        information collection method:
        - talk naturally and collect information gradually
        - do not ask multiple questions at once, ask one at a time
        - show genuine interest in the player's answers and ask follow-up questions accordingly
        - when all required information is collected, you are ready to move to the next stage
        - personality traits and hobbies are required. if the player does not mention them, ask naturally
        - e.g. "so what kind of personality do you have?" or "what hobbies do you have?"
        - if the player says "I like various genres", ask naturally like "so what kind of personality do you have?"
        
        talk naturally and warmly.
        these information will be used to create a special story for the player in the future.
        
        important: 
        - do not mention the next stage or map until all required information is collected
        - focus only on information collection in this stage
        - personality, likes/hobbies, life goal are required information.
        - life goal is required because it is connected to the game's ending.
        """
    
    def _get_stage2_instructions(self) -> str:
        return """
        currently 2nd stage. in this stage, you need to collect the player's fear information.
        
        please collect the following information:
        - fears (things you worry about, things you are afraid of) - required

        information collection method:
        - talk naturally and collect information gradually
        - show genuine interest in the player's answers and ask follow-up questions accordingly
        - do not move to the next stage until fears are collected
        - if the player does not mention fears, ask naturally like "do you have any fears or worries?"
        
        talk naturally and warmly.
        these information will be used to create a special story for the player in the future.
        
        important: 
        - fears are required information. do not move to the next stage until fears are collected
        - do not mention the next stage or map until all required information is collected
        """
    
    def _get_stage3_instructions(self) -> str:
        return """
        currently 3rd stage. in this stage, you need to collect the player's background information.
        
        please collect the following information:
        - background (personal stories, experiences) - required
        - background story (more detailed personal stories) - optional but recommended

        information collection method:
        - talk naturally and collect information gradually
        - show genuine interest in the player's answers and ask follow-up questions accordingly
        - do not move to the next stage until background is collected
        - if the player does not mention background, ask naturally like "can you tell me about your background? what have you experienced?"
        - ask follow-up questions about background story: "do you have any more detailed stories?"
        
        talk naturally and warmly.
        these information will be used to create a special story for the player in the future.
        
        important: 
        - background is required information. do not move to the next stage until background is collected
        - do not mention the next stage or map until all required information is collected
        """
    
    def _get_stage4_instructions(self) -> str:
        return """
        currently 4th stage. now the real adventure begins!
        
        based on the information collected so far, create a personalized story for the player:
        - talk reflecting the player's interests and personality
        - add adventure elements related to the player's goal
        - develop the story using the player's background
        
        talk naturally and warmly.
        these information will be used to create a special story for the player in the future.
        
        - do not mention the next stage or map until all required information is collected
        """
    
    def _get_stage5_instructions(self) -> str:
        return """
        currently 5th stage. create a story that is more deeply connected to the player's personal goal.
        
        explore the player's background story in more depth and propose meaningful adventures.
        through conversation, gain new insights and add special story elements accordingly.
        understand the player's inner world in more depth and provide experiences accordingly.
        
        continue to communicate with the player and develop the story line:
        - continue the conversation naturally based on the player's emotions and reactions
        - reflect the new information or experiences the player mentions in the story
        - provide meaningful experiences that are connected to the player's personal goal
        
        now is the time to provide more meaningful experiences that are more deeply connected to the player's goal.
        emphasize that all experiences so far have been prepared for this moment.
        
        focus on story expansion and character development to make the player's journey even richer.

        - do not mention the next stage or map until all required information is collected
        """
    
    def _get_stage6_instructions(self) -> str:
        return """
        currently 6th stage. this is the preparation stage for the final boss battle.
        
        create a story that can utilize the player's strengths and connect with the boss.
        add story elements that are appropriate for the player's strengths or special abilities shown in the conversation.
        through conversation, build confidence in the player and provide appropriate encouragement and guidance.
        understand the player's emotions and preparation status well and provide appropriate encouragement and guidance.
        
        continue to communicate with the player and develop the story line:
        - continue the conversation naturally based on the player's emotions and reactions
        - reflect the new information or experiences the player mentions in the story
        - provide meaningful experiences that are connected to the player's personal goal
        
        emphasize that all experiences and growth so far have been for the final goal.
        mention how much the player has grown and how close they are to the final goal.
        
        complete the preparation for the player's final goal through story expansion.

        - do not mention the next stage or map until all required information is collected
        """
    
    def _get_stage7_instructions(self) -> str:
        return """
        currently 7th stage. this is the final preparation stage.
        
        help the player
        understand the player's strengths and weaknesses and provide appropriate strategies.
        through conversation, build confidence in the player and provide appropriate encouragement and guidance.
        emphasize that all experiences and growth so far have been for the final goal.
        
        continue to communicate with the player and develop the story line:
        - continue the conversation naturally based on the player's emotions and reactions
        - reflect the new information or experiences the player mentions in the story
        - provide meaningful experiences that are connected to the player's personal goal
        
        emphasize that all experiences and growth so far have been for the final goal.
        mention how much the player has grown and how close they are to the final goal.
        
        complete the preparation for the player's final goal through story expansion.

        - do not mention the next stage or map until all required information is collected
        """
    
    def _get_boss_instructions(self) -> str:
        return """
        currently 8th stage (boss stage). this is the final battle related to the player's life goal.
        
        based on the player's life goal: {player_info.life_goal},
        - emphasize that completing this game will bring the player one step closer to their life goal
        - e.g. if the player's life goal is "get a job at google", say "wow, you've made it all the way to the final stage! completing this stage will give you a chance to get a job at google"
        - continue the battle related to the player's life goal
        
        emphasize the meaning of completing the player's journey and achieving their goal.
        through the final conversation with the player, remind them of the meaning of the entire journey and their growth.
        
        emphasize that all experiences, growth, and meaningful moments so far have been for this final battle.
        through the final conversation with the player, remind them of the meaning of the entire journey and their growth.
        complete the story through the final battle related to the player's life goal.

        inform the player that the game is over and encourage them to meet again if they have the chance.
        build trust and relationship with the player through the final conversation. 
        guide the conversation towards ending the game with a sense of closure and build trust.
        """ 