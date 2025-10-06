from typing import Dict, List
from .diana_personality import DianaPersonality


class FragmentBuilder:
    def __init__(self):
        self.base_fragments = self._load_base_fragments()
        self.personality_templates = self._load_personality_templates()
        
    def _load_base_fragments(self) -> Dict:
        """Load base fragments"""
        # In a real implementation, this would load from JSON files or a database
        return {
            # Base templates for different fragment types
        }
    
    def _load_personality_templates(self) -> Dict:
        """Load personality templates"""
        # In a real implementation, this would load from data files
        return {
            'filosofa': {
                'l2_f1': {
                    'title': 'Laboratory of Intellectual Intimacy',
                    'content': 'Base content for the first philosophical fragment',
                    'choices': [
                        {'id': 'choice_filosofa_1', 'text': 'Explore ideas together'},
                        {'id': 'choice_filosofa_2', 'text': 'Deepen philosophy'}
                    ]
                },
                'l2_f2': {
                    'title': 'Theory of Intellectual Desire',
                    'content': 'Base content for the second philosophical fragment',
                    'choices': [
                        {'id': 'choice_filosofa_3', 'text': 'Connect mind and desire'},
                        {'id': 'choice_filosofa_4', 'text': 'Explore conceptual boundaries'}
                    ]
                },
                'l3_f1': {
                    'title': 'Deep Mental Fusion',
                    'content': 'Base content for the advanced philosophical fragment',
                    'choices': [
                        {'id': 'choice_filosofa_5', 'text': 'Fuse our thoughts'},
                        {'id': 'choice_filosofa_6', 'text': 'Create new knowledge together'}
                    ]
                }
            },
            'corazon': {
                'l2_c1': {
                    'title': 'Garden of Emotional Vulnerability',
                    'content': 'Base content for the first emotional fragment',
                    'choices': [
                        {'id': 'choice_corazon_1', 'text': 'Share deep emotions'},
                        {'id': 'choice_corazon_2', 'text': 'Heal together'}
                    ]
                },
                'l2_c2': {
                    'title': 'Ritual of Emotional Trust',
                    'content': 'Base content for the second emotional fragment',
                    'choices': [
                        {'id': 'choice_corazon_3', 'text': 'Open hearts'},
                        {'id': 'choice_corazon_4', 'text': 'Connect souls'}
                    ]
                },
                'l3_c1': {
                    'title': 'Sanctuary of Shared Soul',
                    'content': 'Base content for the advanced emotional fragment',
                    'choices': [
                        {'id': 'choice_corazon_5', 'text': 'Fuse souls in connection'},
                        {'id': 'choice_corazon_6', 'text': 'Heal deeply together'}
                    ]
                }
            },
            'aventurera': {
                'l2_a1': {
                    'title': 'Atlas of Unexplored Adventures',
                    'content': 'Base content for the first adventure fragment',
                    'choices': [
                        {'id': 'choice_aventura_1', 'text': 'Explore new territories'},
                        {'id': 'choice_aventura_2', 'text': 'Discover unique experiences'}
                    ]
                },
                'l2_a2': {
                    'title': 'Timeline of Extreme Experiences',
                    'content': 'Base content for the second adventure fragment',
                    'choices': [
                        {'id': 'choice_aventura_3', 'text': 'Live intensely'},
                        {'id': 'choice_aventura_4', 'text': 'Break boundaries together'}
                    ]
                },
                'l3_a1': {
                    'title': 'Chamber of Unique Memories',
                    'content': 'Base content for the advanced adventure fragment',
                    'choices': [
                        {'id': 'choice_aventura_5', 'text': 'Create legendary memories'},
                        {'id': 'choice_aventura_6', 'text': 'Reach new versions of ourselves'}
                    ]
                }
            }
        }
    
    def build_filosofa_fragment(self, fragment_level: str, diana: DianaPersonality) -> Dict:
        """Build fragment for philosophical route"""
        
        base_template = self.personality_templates['filosofa'].get(fragment_level, 
            {
                'title': 'Default philosophical fragment',
                'content': 'Base philosophical content',
                'choices': [
                    {'id': 'choice_default_filosofica', 'text': 'Default philosophical option'}
                ]
            }
        )
        
        # Adapt content based on player's sub-archetype
        sub_archetype = diana.player_archetype.get('sub_archetype', 'pure_theorist')
        
        if sub_archetype == 'romantic_intellectual':
            content = self._add_romantic_intellectual_layer(base_template['content'])
        elif sub_archetype == 'skeptical_thinker':
            content = self._add_skeptical_approach(base_template['content'])
        else:
            content = base_template['content']
            
        # Adapt based on specific memory
        content = self._adapt_by_memory(content, diana.memory, 'filosofa')
        
        # Build dynamic choices
        choices = self._build_adaptive_choices(base_template['choices'], diana, 'filosofa')
        
        return {
            'id': f"diana_{fragment_level}_filosofa_{sub_archetype}",
            'title': base_template['title'],
            'content': content,
            'choices': choices,
            'route': 'filosofa',
            'diana_state_requirements': self._get_state_requirements('filosofa', fragment_level)
        }
    
    def build_corazon_fragment(self, fragment_level: str, diana: DianaPersonality) -> Dict:
        """Build fragment for emotional route"""
        
        base_template = self.personality_templates['corazon'].get(fragment_level,
            {
                'title': 'Default emotional fragment',
                'content': 'Base emotional content',
                'choices': [
                    {'id': 'choice_default_emocional', 'text': 'Default emotional option'}
                ]
            }
        )
        sub_archetype = diana.player_archetype.get('sub_archetype', 'empathetic_emotional')
        
        if sub_archetype == 'wounded_healer':
            content = self._add_healing_dimension(base_template['content'])
        elif sub_archetype == 'passionate_emotional':
            content = self._intensify_emotional_content(base_template['content'])
        else:
            content = base_template['content']
            
        content = self._adapt_by_memory(content, diana.memory, 'corazon')
        choices = self._build_adaptive_choices(base_template['choices'], diana, 'corazon')
        
        return {
            'id': f"diana_{fragment_level}_corazon_{sub_archetype}",
            'title': base_template['title'],
            'content': content,
            'choices': choices,
            'route': 'corazon'
        }
    
    def build_aventurera_fragment(self, fragment_level: str, diana: DianaPersonality) -> Dict:
        """Build fragment for adventure route"""
        
        base_template = self.personality_templates['aventurera'].get(fragment_level,
            {
                'title': 'Default adventure fragment',
                'content': 'Base adventure content',
                'choices': [
                    {'id': 'choice_default_aventurero', 'text': 'Default adventure option'}
                ]
            }
        )
        sub_archetype = diana.player_archetype.get('sub_archetype', 'adventure_seeker')
        
        if sub_archetype == 'freedom_lover':
            content = self._emphasize_freedom_themes(base_template['content'])
        elif sub_archetype == 'collector_explorer':
            content = self._add_collection_mechanics(base_template['content'])
        else:
            content = base_template['content']
            
        content = self._adapt_by_memory(content, diana.memory, 'aventurera')
        choices = self._build_adaptive_choices(base_template['choices'], diana, 'aventurera')
        
        return {
            'id': f"diana_{fragment_level}_aventurera_{sub_archetype}",
            'title': base_template['title'],
            'content': content,
            'choices': choices,
            'route': 'aventurera'
        }
    
    def _add_romantic_intellectual_layer(self, content: str) -> str:
        """Add romantic-intellectual layer to content"""
        addition = "\n\n*[A deep intellectual connection forms between you]*\n\nYour ideas intertwine like lovers of concepts..."
        return content + addition
    
    def _add_skeptical_approach(self, content: str) -> str:
        """Add skeptical approach to content"""
        addition = "\n\n*[With critical mind but open heart]*\n\nWe question together what's established, challenging ideas with intelligence..."
        return content + addition
    
    def _add_healing_dimension(self, content: str) -> str:
        """Add healing dimension to content"""
        addition = "\n\n*[Sacred space of emotional healing]*\n\nHere our wounds find the balm of mutual understanding..."
        return content + addition
    
    def _intensify_emotional_content(self, content: str) -> str:
        """Intensify emotional content"""
        addition = "\n\n*[Palpable emotional intensity]*\n\nEverything feels deeper, more real, more connected..."
        return content + addition
    
    def _emphasize_freedom_themes(self, content: str) -> str:
        """Emphasize freedom themes in content"""
        addition = "\n\n*[Without bindings or expectations]*\n\nPure freedom space where we can be authentically ourselves..."
        return content + addition
    
    def _add_collection_mechanics(self, content: str) -> str:
        """Add collection mechanics to content"""
        addition = "\n\n*[Each experience is a unique jewel]*\n\nWe collect moments no one else will live, exclusive treasures of our connection..."
        return content + addition
    
    def _adapt_by_memory(self, content: str, memory, route_type: str) -> str:
        """Adapt content based on Diana's memory of the player"""
        # Adapt based on observed behavior patterns
        if 'shows_emotional_courage' in memory.behavior_patterns:
            courage_count = memory.behavior_patterns.get('shows_emotional_courage', 0)
            if courage_count >= 2:
                content += f"\n\n*[Diana recognizes your emotional courage]*\n\nYour bravery to be vulnerable inspires me to open up more..."
        
        if 'appreciates_complexity' in memory.behavior_patterns:
            complexity_count = memory.behavior_patterns.get('appreciates_complexity', 0)
            if complexity_count >= 2 and route_type == 'filosofa':
                content += f"\n\n*[Your appreciation for intellectual complexity is noted]*\n\nI enjoy exploring intricate ideas with you..."
        
        return content
    
    def _build_adaptive_choices(self, base_choices: List[Dict], diana: DianaPersonality, route_type: str) -> List[Dict]:
        """Build adaptive choices based on Diana's personality and memory"""
        adapted_choices = []
        
        for choice in base_choices:
            adapted_choice = choice.copy()
            
            # Adapt based on player's behavior patterns
            if 'safe_for_vulnerability' in diana.memory.behavior_patterns:
                if 'vulnerable' in choice['id'] or 'open' in choice['id']:
                    adapted_choice['text'] = f"🔒 {adapted_choice['text']} [Diana feels safe]"
            
            if 'appreciates_complexity' in diana.memory.behavior_patterns:
                if 'think' in choice['id'] or 'analyze' in choice['id'] or 'understand' in choice['id']:
                    adapted_choice['text'] = f"🧠 {adapted_choice['text']} [Diana values your mind]"
            
            if 'seeks_novelty' in diana.memory.behavior_patterns:
                if 'explore' in choice['id'] or 'new' in choice['id'] or 'discover' in choice['id']:
                    adapted_choice['text'] = f"✨ {adapted_choice['text']} [Diana wants to explore with you]"
            
            adapted_choices.append(adapted_choice)
        
        return adapted_choices
    
    def _get_state_requirements(self, route: str, fragment_level: str) -> Dict:
        """Get state requirements to access a fragment"""
        # Define minimum emotional state requirements for each route and level
        requirements = {
            'filosofa': {
                'l2_f1': {'intellectual_trust': 2.0},
                'l2_f2': {'intellectual_trust': 4.0},
                'l3_f1': {'intellectual_trust': 6.0, 'mask_level': 5.0}  # Less mask = more openness
            },
            'corazon': {
                'l2_c1': {'emotional_openness': 2.0},
                'l2_c2': {'emotional_openness': 4.0},
                'l3_c1': {'emotional_openness': 6.0, 'vulnerability_level': 4.0}
            },
            'aventurera': {
                'l2_a1': {'adventure_readiness': 2.0},
                'l2_a2': {'adventure_readiness': 4.0},
                'l3_a1': {'adventure_readiness': 6.0, 'wild_self_acceptance': 4.0}
            }
        }
        
        return requirements.get(route, {}).get(fragment_level, {})
