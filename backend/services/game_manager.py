from typing import Dict, Any, Optional
import uuid
from utils.game_state import GameState, Stage
from services.npc_service import NPCService
import logging

# set logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GameManager:
    def __init__(self):
        self.npc_service = NPCService()
        self.active_games: Dict[str, GameState] = {}
    
    def create_new_game(self, player_id: Optional[str] = None) -> str:
        """create new game"""
        if not player_id:
            player_id = str(uuid.uuid4())
        
        game_state = GameState()
        game_state.player_id = player_id  # add player_id
        self.active_games[player_id] = game_state
        
        # reset used_ai_maps (new game start)
        self.npc_service.map_recommender.used_ai_maps.clear()
        # reset used_styles
        self.npc_service.map_recommender.reset_used_styles()
        # reset recommendation history
        self.npc_service.map_recommender.reset_recommendation_history()
        # reset metadata files
        self._reset_metadata_files()
        
        # initial NPC welcome message
        welcome_message = self._generate_welcome_message()
        game_state.add_conversation("npc", welcome_message)
        
        # save initial state to vector DB
        initial_context = {
            "game_started": True,
            "stage": game_state.current_stage.value,
            "player_info": game_state.player_info.to_dict()
        }
        self.npc_service.vector_store.add_player_context(player_id, initial_context)
        
        logger.info(f"new game created: player_id={player_id}")
        logger.info(f"initial context saved: {initial_context}")
        
        return player_id
    
    def process_player_message(self, player_id: str, message: str) -> Dict[str, Any]:
        """process player message and return response"""
        
        if player_id not in self.active_games:
            return {"error": "game not found. please start a new game."}
        
        game_state = self.active_games[player_id]
        
        logger.info(f"process player message: player_id={player_id}, message='{message[:50]}...'")
        
        # extract player info (all stages)
        self._extract_and_update_player_info(message, game_state)
        
        # check stage progress (after info extraction)
        stage_progress = self._check_stage_progress(game_state, message, player_id)
        
        # generate NPC response (only if stage transition is not pending)
        if not stage_progress.get("stage_completed", False) and not stage_progress.get("stage_transition_pending", False):
            npc_response = self.npc_service.generate_response(message, game_state, player_id)
        else:
            npc_response = ""
            
        # map recommendation (only if stage transition is not pending or should_recommend_map is True)
        map_recommendation = None
        if stage_progress.get("stage_completed", False):
            # use already generated map recommendation for stage transition
            map_recommendation = stage_progress.get("map_recommendation")
        elif stage_progress.get("should_recommend_map", False):
            # general map recommendation
            map_recommendation = self.npc_service.recommend_map_for_stage(game_state)
            game_state.current_map = map_recommendation["name"]
        
        # check game completion
        game_completed = game_state.game_completed
        
        # save conversation to vector DB
        conversation_data = {
            "speaker": "player",
            "message": message,
            "timestamp": game_state.conversation_history[-1]["timestamp"] if game_state.conversation_history else None
        }
        self.npc_service.vector_store.add_conversation(player_id, conversation_data)
        logger.info(f"player conversation saved: {conversation_data}")
        
        # save NPC response to vector DB
        npc_conversation_data = {
            "speaker": "npc",
            "message": npc_response,
            "timestamp": game_state.conversation_history[-1]["timestamp"] if game_state.conversation_history else None
        }
        self.npc_service.vector_store.add_conversation(player_id, npc_conversation_data)
        logger.info(f"NPC conversation saved: {npc_conversation_data}")
        
        # if stage progress is completed and stage intro message is present, add stage intro message to NPC response
        if stage_progress.get("stage_completed", False) and stage_progress.get("stage_intro_message"):
            # add stage intro message to NPC response
            combined_response = stage_progress["stage_intro_message"] + "\n\n" + npc_response
            logger.info(f"add stage intro message: {stage_progress['stage_intro_message'][:100]}...")
        elif stage_progress.get("stage_transition_pending", False):
            # if stage transition is pending, only show transition message
            combined_response = stage_progress.get("message", "")
            logger.info(f"stage transition pending: {combined_response[:100]}...")
        else:
            combined_response = npc_response
        
        return {
            "npc_response": combined_response,
            "stage_progress": stage_progress,
            "map_recommendation": map_recommendation,
            "game_completed": game_completed,
            "current_stage": game_state.current_stage.value,
            "player_info": game_state.player_info.to_dict()
        }
    
    def _generate_welcome_message(self) -> str:
        """generate welcome message"""
        return """
        Hello, brave adventurer! I am the NPC guiding your journey. 
        
        This is a special world for you, brave adventurer. 
        You will create your own unique story through 8 stages.
        
        First, I would like to know you better. 
        Who are you? Where do you live?
        """
    
    def _extract_and_update_player_info(self, message: str, game_state: GameState):
        """extract and update player info from player message. collect all info regardless of stage."""
        print(f"\n🔄🔄🔄 start info update process:")
        print(f"   original message: {message}")
        print(f"   current stage: {game_state.current_stage.value} ({game_state.current_stage.name})")
        
        # log current state before update
        print(f"📊📊📊 before update player info:")
        current_info = game_state.player_info.to_dict()
        for key, value in current_info.items():
            if value:  # print only fields with values
                print(f"   {key}: {value}")
        
        extracted_info = self.npc_service.extract_player_info(message, game_state)
        
        if extracted_info:
            print(f"✅✅✅ info extraction success:")
            for key, value in extracted_info.items():
                print(f"   {key}: {value}")
            
            # collect info for all fields (regardless of stage)
            updated_fields = []
            
            # basic info fields (fields managed as lists)
            list_fields = ["personality_traits", "likes", "fears", "extra_info"]
            
            # single value fields
            single_fields = ["name", "age", "location", "occupation", "life_goal"]
            
            # text accumulate fields (add to existing content)
            text_accumulate_fields = ["background"]
            
            # process list fields
            for key in list_fields:
                if key in extracted_info and extracted_info[key]:
                    value = extracted_info[key]
                    current_list = getattr(game_state.player_info, key) or []
                    print(f"🔄 processing list field: {key}")
                    print(f"   current value: {current_list}")
                    print(f"   new value: {value}")
                    
                    if isinstance(value, str):
                        # convert comma-separated string to list
                        new_items = [x.strip() for x in value.split(",")]
                        # add without duplicates
                        combined_list = current_list + [item for item in new_items if item not in current_list]
                        setattr(game_state.player_info, key, combined_list)
                        updated_fields.append(f"{key}: {combined_list}")
                        print(f"   updated: {combined_list}")
                    elif isinstance(value, list):
                        combined_list = current_list + [item for item in value if item not in current_list]
                        setattr(game_state.player_info, key, combined_list)
                        updated_fields.append(f"{key}: {combined_list}")
                        print(f"   updated: {combined_list}")
            
            # process single value fields (update with more specific info)
            for key in single_fields:
                if key in extracted_info and extracted_info[key]:
                    current_value = getattr(game_state.player_info, key)
                    new_value = extracted_info[key]
                    
                    print(f"🔄 processing single value field: {key}")
                    print(f"   current value: '{current_value}'")
                    print(f"   new value: '{new_value}'")
                    
                    # update if existing value is empty or new value is more specific
                    should_update = False
                    if not current_value:
                        should_update = True
                        print(f"   update reason: existing value is empty")
                    elif key == "location":
                        # update with more specific location info (e.g. "서울" -> "서울 노원구")
                        if len(new_value) > len(current_value) and current_value in new_value:
                            should_update = True
                            print(f"   update reason: more specific location info")
                    elif key == "age":
                        # update if age is different
                        if new_value != current_value:
                            should_update = True
                            print(f"   update reason: age changed")
                    elif key == "name":
                        # update if name is different
                        if new_value != current_value:
                            should_update = True
                            print(f"   update reason: name changed")
                    elif key == "occupation":
                        # update with more specific occupation info
                        if len(new_value) > len(current_value) and current_value in new_value:
                            should_update = True
                            print(f"   update reason: more specific occupation info")
                        elif new_value != current_value:
                            should_update = True
                            print(f"   update reason: occupation changed")
                    
                    if should_update:
                        setattr(game_state.player_info, key, new_value)
                        updated_fields.append(f"{key}: {new_value}")
                        print(f"   ✅ updated: '{current_value}' -> '{new_value}'")
                    else:
                        print(f"   ⏭️ skipped update")
            
            # process text accumulate fields (add to existing content)
            for key in text_accumulate_fields:
                if key in extracted_info and extracted_info[key]:
                    new_value = extracted_info[key].strip()
                    current_value = getattr(game_state.player_info, key)
                    
                    print(f"🔄 processing text accumulate field: {key}")
                    print(f"   current value: '{current_value}'")
                    print(f"   new value: '{new_value}'")
                    
                    if current_value:
                        updated_value = f"{current_value} {new_value}"
                        setattr(game_state.player_info, key, updated_value)
                        print(f"   ✅ accumulated: '{updated_value}'")
                    else:
                        setattr(game_state.player_info, key, new_value)
                        print(f"   ✅ new value set: '{new_value}'")
                    
                    updated_fields.append(f"{key}: {getattr(game_state.player_info, key)}")
            
            # check stage completion (stage_manager)
            self.npc_service.stage_manager.is_stage_complete(game_state)
            
            print(f"\n📊📊📊 after update player info:")
            final_info = game_state.player_info.to_dict()
            for key, value in final_info.items():
                if value:  # print only fields with values
                    print(f"   {key}: {value}")
            
            print(f"\n✅✅✅ info update completed!")
            print(f"   updated fields: {len(updated_fields)}")
            if updated_fields:
                print(f"   updated fields: {updated_fields}")
        else:
            print(f"❌❌❌ no extracted player info")
    
    def _check_stage_progress(self, game_state: GameState, message: str, player_id: str) -> Dict[str, Any]:
        """check stage progress"""
        print(f"\n🔄🔄🔄 _check_stage_progress 호출:")
        print(f"   current_stage: {game_state.current_stage.value} ({game_state.current_stage.name})")
        print(f"   monster_defeated: {getattr(game_state, 'monster_defeated', False)}")
        
        # 스테이지 완료 조건 체크
        is_stage_complete = self.npc_service.stage_manager.is_stage_complete(game_state)
        
        # 튜토리얼 스테이지는 추가로 monster_defeated 체크
        if game_state.current_stage == Stage.TUTORIAL:
            monster_defeated = getattr(game_state, 'monster_defeated', False)
            is_stage_complete = is_stage_complete and monster_defeated
            print(f"   tutorial stage - monster_defeated required: {monster_defeated}")
        
        print(f"   final stage_completed: {is_stage_complete}")
        
        return {"stage_completed": is_stage_complete}
    
    def get_game_status(self, player_id: str) -> Optional[Dict[str, Any]]:
        """return game status"""
        if player_id not in self.active_games:
            return None
        
        game_state = self.active_games[player_id]
        
        return {
            "current_stage": game_state.current_stage.value,
            "stage_name": game_state.current_stage.name,
            "player_info": game_state.player_info.to_dict(),
            "current_map": game_state.current_map,
            "boss_goal": game_state.boss_goal,
            "game_completed": game_state.game_completed,
            "conversation_count": len(game_state.conversation_history)
        }
    
    def save_game(self, player_id: str):
        """save game state to vector DB"""
        if player_id in self.active_games:
            game_state = self.active_games[player_id]
            
            # save game state to vector DB
            self.npc_service.vector_store.add_player_context(player_id, {
                "game_state": game_state.dict(),
                "last_saved": True
            })
    
    def load_game(self, player_id: str) -> bool:
        """load saved game"""
        try:
            # search game state in vector DB
            history = self.npc_service.vector_store.get_player_history(player_id, limit=1)
            
            if history:
                # restore game state (more secure parsing needed in actual implementation)
                return True
            
            return False

        except Exception as e:
            print(f"game load error: {e}")
            return False
    
    def advance_to_next_stage(self, player_id: str) -> Dict[str, Any]:
        """advance to next stage. check each stage condition."""
        
        if player_id not in self.active_games:
            return {"error": "game not found. please start a new game."}
        
        game_state = self.active_games[player_id]
        current_stage = game_state.current_stage
        
        # NOTE: monster_defeated 상태는 프론트엔드에서 '/game/enemy-defeated' API로 업데이트됩니다.
        # 테스트를 위해 임시로 True 설정 (실제 게임에서는 이 라인을 제거)
        # game_state.monster_defeated = True  # TODO: 프론트엔드 적 시스템 완성 후 제거
        
        print(f"\n🔄 check stage transition: {current_stage.name} -> next stage")
        
        # 1 stage (tutorial) -> 2 stage: collect required info + monster defeated true
        if current_stage == Stage.TUTORIAL:
            # check stage completion condition (print included)
            is_complete = self.npc_service.stage_manager.is_stage_complete(game_state)
            if not is_complete:
                missing_info = self.npc_service.stage_manager.get_missing_info_for_stage(game_state)
                return {"error": f"튜토리얼을 완료하려면 다음 정보가 필요합니다: {', '.join(missing_info)}"}
            
            print("✅ tutorial -> stage 2: collect required info + monster defeated true")
            return self._handle_stage_advancement(game_state, player_id)
        
        # 2 stage -> 3 stage: collect required info + monster defeated true
        elif current_stage == Stage.STAGE_2:
            # check stage completion condition (print included)
            is_complete = self.npc_service.stage_manager.is_stage_complete(game_state)
            if not is_complete:
                return {"error": "stage 2 completion requires fear info."}
            
            print("✅ stage 2 -> stage 3: collect required info + monster defeated true")
            return self._handle_stage_advancement(game_state, player_id)
        
        # 3 stage -> 4 stage: collect required info + monster defeated true
        elif current_stage == Stage.STAGE_3:
            # check stage completion condition (print included)
            is_complete = self.npc_service.stage_manager.is_stage_complete(game_state)
            if not is_complete:
                return {"error": "stage 3 completion requires background info."}
            
            print("✅ stage 3 -> stage 4: collect required info + monster defeated true")
            return self._handle_stage_advancement(game_state, player_id)
        
        # 4 stage -> 5 stage: monster defeated true + check player response (npc and player conversation 1 or more)
        elif current_stage == Stage.STAGE_4:
            # check stage completion condition (print included)
            is_complete = self.npc_service.stage_manager.is_stage_complete(game_state)
            if not is_complete: 
                return {"error": "stage 4 completion requires npc and player conversation 1 or more."}
            
            print("✅ stage 4 -> stage 5: monster defeated true + check player response (npc and player conversation 1 or more)")
            return self._handle_stage_advancement(game_state, player_id)
        
        # 5 stage -> 6 stage: monster defeated true + check player response (npc and player conversation 1 or more)
        elif current_stage == Stage.STAGE_5:
            # check stage completion condition (print included)
            is_complete = self.npc_service.stage_manager.is_stage_complete(game_state)
            if not is_complete:
                return {"error": "stage 5 completion requires npc and player conversation 1 or more."}
            
            print("✅ stage 5 -> stage 6: monster defeated true + check player response (npc and player conversation 1 or more)")
            return self._handle_stage_advancement(game_state, player_id)
        
        # 6 stage -> 7 stage: monster defeated true + check player response (npc and player conversation 1 or more)
        elif current_stage == Stage.STAGE_6:
            # check stage completion condition (print included)
            is_complete = self.npc_service.stage_manager.is_stage_complete(game_state)
            if not is_complete:
                return {"error": "stage 6 completion requires npc and player conversation 1 or more."}
            
            print("✅ stage 6 -> stage 7: monster defeated true + check player response (npc and player conversation 1 or more)")
            return self._handle_stage_advancement(game_state, player_id)
        
        # 7 stage -> 8 stage (boss): monster defeated true + check player response (npc and player conversation 1 or more)
        elif current_stage == Stage.STAGE_7:
            # check stage completion condition (print included)
            is_complete = self.npc_service.stage_manager.is_stage_complete(game_state)
            if not is_complete:
                return {"error": "stage 7 completion requires npc and player conversation 1 or more."}
            
            print("✅ stage 7 -> boss stage: monster defeated true + check player response (npc and player conversation 1 or more)")
            return self._handle_stage_advancement(game_state, player_id)
        
        # 8 stage (boss): monster defeated true -> game end
        elif current_stage == Stage.BOSS:
            # boss defeated -> game end
            game_state.game_completed = True
            
            # generate boss stage completion message
            stage_intro_message = self._generate_stage_intro_message(game_state, None, player_id)
            game_state.add_conversation("npc", stage_intro_message)
            
            # save boss stage completion message to vector DB
            self.npc_service.vector_store.add_conversation(player_id, {
                "speaker": "npc",
                "message": stage_intro_message,
                "timestamp": game_state.conversation_history[-1]["timestamp"],
                "type": "stage_completion"
            })
            
            print("🎉 boss stage completed: game end condition met")
            
            return {
                "stage_progress": {
                    "stage_completed": True,
                    "game_completed": True,
                    "message": "Congratulations! You have defeated the boss and completed the game!"
                },
                "map_recommendation": None,
                "game_completed": True,
                "current_stage": game_state.current_stage.value,
                "player_info": game_state.player_info.to_dict(),
                "stage_intro_message": stage_intro_message
            }
        
        else:
            return {"error": "unknown stage."}
    
    def _handle_stage_advancement(self, game_state: GameState, player_id: str) -> Dict[str, Any]:
        """
        handle map recommendation -> creation -> description flow when stage changes.
        """
        # advance stage
        game_state.advance_stage()
        
        # 새 스테이지 시작 시 적 처치 상태 초기화
        game_state.monster_defeated = False
        print(f"🔄 새 스테이지 시작 - 적 처치 상태 초기화: Stage {game_state.current_stage.value}")
        
        # monster
        map_recommendation = self.npc_service.recommend_map_for_stage(game_state)
        game_state.current_map = map_recommendation["name"]
        
        # generate stage introduction message (include map recommendation)
        stage_intro_message = self._generate_stage_intro_message(game_state, map_recommendation, player_id)
        
        return {
            "stage_progress": {
                "stage_completed": True,
                "new_stage": game_state.current_stage.value,
                "message": f"stage {game_state.current_stage.value} started!"
            },
            "map_recommendation": map_recommendation,
            "stage_intro_message": stage_intro_message,
            "current_stage": game_state.current_stage.value,
            "player_info": game_state.player_info.to_dict(),
            "game_completed": game_state.game_completed
        }
    
    def _generate_stage_intro_message(self, game_state: GameState, map_recommendation: Optional[Dict[str, Any]], player_id: str) -> str:
        """generate stage introduction message using OpenAI API"""
        
        # prepare player info
        player_info = game_state.player_info
        current_stage = game_state.current_stage
        
        # special handling for boss stage or no map
        if not map_recommendation:
            return f"Congratulations! {player_info.name} has achieved their final goal '{player_info.life_goal}'! 🎉"
        
        # prepare map info
        map_name = map_recommendation.get('name', '신비로운 장소') if map_recommendation else '신비로운 장소'
        map_description = map_recommendation.get('description', '신비로운 장소') if map_recommendation else '신비로운 장소'
        map_reasoning = map_recommendation.get('reasoning', '당신의 모험과 성장을 위해 최적의 환경이기 때문입니다.') if map_recommendation else '당신의 모험과 성장을 위해 최적의 환경이기 때문입니다.'
        
        # generate stage-specific prompt
        stage_context = {
            Stage.STAGE_2: "first adventure completed and the journey begins",
            Stage.STAGE_3: "the adventure becomes more interesting and the player's growth becomes more noticeable",
            Stage.STAGE_4: "the adventure begins and the player's skills are put to the test",
            Stage.STAGE_5: "the adventure reaches its climax and a big challenge awaits",
            Stage.STAGE_6: "the final goal is getting closer and the final preparations are being made",
            Stage.STAGE_7: "the final boss battle is approaching and the tension is building up",
            Stage.BOSS: "the final boss battle is approaching and the tension is building up"
        }
        
        context_description = stage_context.get(current_stage, "a new adventure begins")
        
        # get stage instructions
        stage_instructions = self.npc_service.stage_manager.get_stage_instructions(current_stage)
        
        # prepare stage-specific info collection requirements
        info_collection_requirements = ""
        if current_stage == Stage.STAGE_2:
            info_collection_requirements = "it is important to learn about the player's 'fear' in this stage. ask naturally about things they fear or worry about."
        elif current_stage == Stage.STAGE_3:
            info_collection_requirements = "it is important to learn more about the player's 'background' in this stage. ask naturally about personal stories, past experiences, educational background, etc."
        elif current_stage in [Stage.STAGE_4, Stage.STAGE_5, Stage.STAGE_6, Stage.STAGE_7]:
            info_collection_requirements = "it is important to create a richer story through conversations with the player. ask naturally about the player's emotions, experiences, and thoughts."
        elif current_stage == Stage.BOSS:
            info_collection_requirements = "this is the final stage. have a final conversation with the player to achieve their final goal, review the journey so far, and check the preparation status for the final challenge."
        
        # prepare prompt for OpenAI API request
        prompt = f"""
            {player_info.name}, you have entered {context_description}.

            New map: {map_name}
            Map features: {map_description}
            Recommendation reason: {map_reasoning}

            Stage instructions: {stage_instructions}

            Important conversation goals: {info_collection_requirements}

            Explain how {player_info.name}'s journey is connected to this map and what adventure awaits in this new stage.
            Create an engaging and personalized story to immerse the player.
            Make sure to end with a message that guides the player to ask questions or engage in conversations that align with the 'important conversation goals'.

            Additional information:
            Explain how {player_info.name}'s journey is connected to this map and what adventure awaits in this new stage.
            Create an engaging and personalized story to immerse the player.
            Make sure to end with a message that guides the player to ask questions or engage in conversations that align with the 'important conversation goals'.
        """
        
        # call NPC service's generate_stage_intro method
        try:
            stage_intro_message = self.npc_service.generate_stage_intro(prompt, game_state, player_id)
            logger.info(f"✅ stage introduction message generated: {stage_intro_message[:100]}...")
            return stage_intro_message
        except Exception as e:
            logger.error(f"❌ stage introduction message generation failed: {e}")
            # return fallback message
            fallback_message = f"""
                🎉 Congratulations! You have completed stage {current_stage.value - 1}!

                🗺️ New map recommendation: {map_name}

                Now you are moving to stage {current_stage.value}. {player_info.name}'s {map_reasoning}

                A new adventure begins! What do you want to experience in this new environment?
                """
            return fallback_message.strip()
    
    def _reset_metadata_files(self):
        """reset metadata files when a new game starts"""
        import os
        import json
        
        try:
            # initialize maps_metadata.json
            maps_metadata_file = "static/generated_maps/maps_metadata.json"
            os.makedirs(os.path.dirname(maps_metadata_file), exist_ok=True)
            with open(maps_metadata_file, 'w', encoding='utf-8') as f:
                json.dump({"maps": {}, "used_styles": []}, f, ensure_ascii=False, indent=2)
            
            # initialize recommendation_history.json
            recommendation_file = "static/generated_maps/recommendation_history.json"
            with open(recommendation_file, 'w', encoding='utf-8') as f:
                json.dump({"recommendations": []}, f, ensure_ascii=False, indent=2)
            
            logger.info("✅ metadata files initialized")
            
        except Exception as e:
            logger.error(f"❌ metadata files initialization failed: {e}")
    
