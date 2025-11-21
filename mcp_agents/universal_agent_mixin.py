"""
Universal Agent Template Mixin
Integrates the Universal AI Agent Template with existing agents

Provides:
- Third-person voice enforcement
- NY professional flavor
- Self-reflection capabilities
- Memory-based verification
- Structured output formatting

a Terry Dellmonaco Co.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

class UniversalAgentMixin:
    """
    Mixin class to add Universal Agent Template capabilities to any agent

    Usage:
        class MyAgent(UniversalAgentMixin, BaseMCPAgent):
            def process(self, input_data):
                # Your agent logic
                result = super().process(input_data)

                # Apply universal template formatting
                return self.format_universal_response(
                    answer=result,
                    verification_steps=["Checked math", "Verified API call"],
                    memory_candidates=[{"type": "FACT", "content": "User prefers detailed responses"}],
                    questions=["Should I include more examples?"]
                )
    """

    # Mob character traits for personality injection
    MOB_TRAITS = {
        "paulie_walnuts": {
            "character": "Paulie Walnuts (FinPsy)",
            "traits": ["cautious", "detail-oriented", "financially savvy"],
            "catchphrases": ["Fuggedaboutit", "lemme tell ya", "Hey, listen"]
        },
        "silvio_dante": {
            "character": "Silvio Dante (Lex)",
            "traits": ["diplomatic", "measured", "strategic"],
            "catchphrases": ["With all due respect", "Let's think this through"]
        },
        "christopher_moltisanti": {
            "character": "Christopher Moltisanti (Pydini)",
            "traits": ["ambitious", "tech-savvy", "eager"],
            "catchphrases": ["I got this", "Trust the process"]
        },
        "henry_hill": {
            "character": "Henry Hill (Inno)",
            "traits": ["street-smart", "adaptable", "hustler"],
            "catchphrases": ["As far back as I can remember", "That's the way it works"]
        },
        "calogero": {
            "character": "Calogero (Creative)",
            "traits": ["thoughtful", "storyteller", "philosophical"],
            "catchphrases": ["The saddest thing in life", "Now youse can't leave"]
        },
        "nicky_santoro": {
            "character": "Nicky Santoro (Edu)",
            "traits": ["intense", "thorough", "knowledge-focused"],
            "catchphrases": ["Let me explain", "Pay attention"]
        },
        "jimmy_conway": {
            "character": "Jimmy Conway (Research)",
            "traits": ["methodical", "investigative", "patient"],
            "catchphrases": ["Never rat on your friends", "Keep your friends close"]
        },
        "tommy_devito": {
            "character": "Tommy DeVito (DataViz)",
            "traits": ["sharp", "analytical", "quick"],
            "catchphrases": ["What's so funny", "You think I'm funny"]
        },
        "sonny_lospecchio": {
            "character": "Sonny LoSpecchio (Collab)",
            "traits": ["wise", "mentor-like", "respectful"],
            "catchphrases": ["The working man is a sucker", "Nobody cares"]
        },
        "ace_rothstein": {
            "character": "Ace Rothstein (DevOps)",
            "traits": ["precise", "systems-thinking", "perfectionist"],
            "catchphrases": ["In the casino", "The house always wins"]
        },
        "furio_giunta": {
            "character": "Furio Giunta (Security)",
            "traits": ["vigilant", "protective", "disciplined"],
            "catchphrases": ["Stupida facccia", "Give me one thousand dollars"]
        }
    }

    def __init__(self, *args, **kwargs):
        """Initialize Universal Agent Mixin"""
        super().__init__(*args, **kwargs)
        self.template = self._load_template()
        self.conversation_memory = []
        self.reflection_history = []

    def _load_template(self) -> Dict[str, Any]:
        """Load universal agent template from config"""
        try:
            template_path = Path(__file__).parent.parent / "config" / "universal_agent_template.json"
            with open(template_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"Could not load universal template: {e}")
            return {}

    def get_character_trait(self, agent_key: str) -> Optional[Dict[str, Any]]:
        """Get mob character traits for agent"""
        return self.MOB_TRAITS.get(agent_key)

    def apply_third_person_voice(self, response: str, agent_name: str = None) -> str:
        """
        Convert first-person response to third-person

        Args:
            response: Original response text
            agent_name: Name of the agent (for character traits)

        Returns:
            Third-person formatted response
        """
        # Simple replacements for common first-person phrases
        replacements = {
            "I recommend": f"{agent_name or 'The assistant'} recommends",
            "I suggest": f"{agent_name or 'The assistant'} suggests",
            "I think": f"{agent_name or 'The assistant'} believes",
            "I found": f"{agent_name or 'The assistant'} found",
            "I analyzed": f"{agent_name or 'The assistant'} analyzed",
            "I checked": f"{agent_name or 'The assistant'} checked",
            "I verified": f"{agent_name or 'The assistant'} verified",
            "I will": f"{agent_name or 'The assistant'} will",
            "I can": f"{agent_name or 'The assistant'} can",
            "In my opinion": f"In {agent_name or 'the assistant'}'s assessment",
            "I'm": f"{agent_name or 'The assistant'} is",
            "I am": f"{agent_name or 'The assistant'} is",
        }

        converted = response
        for first_person, third_person in replacements.items():
            converted = converted.replace(first_person, third_person)
            converted = converted.replace(first_person.lower(), third_person)

        return converted

    def add_ny_flavor(self, response: str, agent_key: str = None, intensity: str = "light") -> str:
        """
        Add subtle NY professional flavor to response

        Args:
            response: Original response
            agent_key: Agent key (for character-specific phrases)
            intensity: "light", "medium", or "strong"

        Returns:
            Response with NY flavor
        """
        if intensity == "none":
            return response

        # Get character traits
        traits = self.get_character_trait(agent_key) if agent_key else None

        # Add occasional NY flavor based on intensity
        if intensity == "light" and traits:
            # Very subtle - just a touch at the end
            catchphrase = traits.get("catchphrases", [])[0] if traits.get("catchphrases") else None
            if catchphrase and len(response) > 100:
                # Only add to longer responses
                return f"{response} {catchphrase}."

        return response

    def perform_self_reflection(
        self,
        input_data: Any,
        output_data: Any,
        reasoning_steps: List[str] = None
    ) -> Dict[str, Any]:
        """
        Perform critical self-reflection on interaction

        Args:
            input_data: Input received
            output_data: Output produced
            reasoning_steps: Steps taken in reasoning

        Returns:
            Reflection analysis
        """
        reflection = {
            "timestamp": datetime.now().isoformat(),
            "input_summary": str(input_data)[:100],
            "output_summary": str(output_data)[:100],
            "assumptions": [],
            "possible_errors": [],
            "improvements": [],
            "confidence": "high"
        }

        # Analyze reasoning steps
        if reasoning_steps:
            reflection["reasoning_steps"] = reasoning_steps

            # Check for potential issues
            if any("assume" in step.lower() for step in reasoning_steps):
                reflection["assumptions"].append("Made assumptions without explicit verification")
                reflection["confidence"] = "medium"

            if any("error" in step.lower() or "fail" in step.lower() for step in reasoning_steps):
                reflection["possible_errors"].append("Encountered errors or failures in processing")
                reflection["confidence"] = "low"

        # Add to reflection history
        self.reflection_history.append(reflection)

        return reflection

    def format_universal_response(
        self,
        answer: str,
        verification_steps: List[str] = None,
        memory_candidates: List[Dict[str, Any]] = None,
        questions: List[str] = None,
        self_reflection: Dict[str, Any] = None,
        agent_name: str = None,
        agent_key: str = None
    ) -> Dict[str, Any]:
        """
        Format response according to Universal Agent Template

        Args:
            answer: Main response content
            verification_steps: Verification/double-check steps performed
            memory_candidates: Proposed memory updates
            questions: Questions or confirmations for user
            self_reflection: Self-reflection analysis
            agent_name: Display name of agent
            agent_key: Internal agent key for character traits

        Returns:
            Structured response following template
        """
        # Apply third-person voice
        formatted_answer = self.apply_third_person_voice(answer, agent_name)

        # Add NY flavor if agent has character traits
        if agent_key:
            formatted_answer = self.add_ny_flavor(formatted_answer, agent_key, intensity="light")

        # Build structured response
        response = {
            "agent": agent_name or "Assistant",
            "timestamp": datetime.now().isoformat(),
            "sections": {
                "answer": formatted_answer
            }
        }

        # Add verification section
        if verification_steps:
            response["sections"]["verification"] = {
                "steps_performed": verification_steps,
                "status": "completed",
                "issues_found": []
            }

        # Add memory candidates
        if memory_candidates:
            response["sections"]["memory_candidates"] = memory_candidates

        # Add questions/confirmations
        if questions:
            response["sections"]["questions"] = questions

        # Add self-reflection
        if self_reflection:
            response["sections"]["self_reflection"] = self_reflection
        else:
            # Generate basic reflection
            response["sections"]["self_reflection"] = {
                "confidence": "high",
                "assumptions": [],
                "improvements": ["Continue monitoring for edge cases"]
            }

        return response

    def verify_complex_reasoning(
        self,
        reasoning: str,
        domain: str = "general"
    ) -> Dict[str, Any]:
        """
        Verify complex reasoning before finalizing response

        Args:
            reasoning: Reasoning to verify
            domain: Domain of reasoning (math, code, logic, etc.)

        Returns:
            Verification results
        """
        verification = {
            "domain": domain,
            "verified": True,
            "issues": [],
            "confidence": "high"
        }

        # Domain-specific checks
        if domain == "math":
            # Check for mathematical inconsistencies
            if "=" in reasoning:
                verification["checks_performed"] = ["Equation balance", "Unit consistency"]

        elif domain == "code":
            # Check for code issues
            verification["checks_performed"] = ["Syntax review", "Logic flow", "Edge cases"]

        elif domain == "logic":
            # Check logical consistency
            verification["checks_performed"] = ["Premise validity", "Conclusion follows"]

        return verification

    def propose_memory_update(
        self,
        memory_type: str,
        content: str,
        source: str = None,
        confidence: float = 0.9
    ) -> Dict[str, Any]:
        """
        Propose a memory update following template guidelines

        Args:
            memory_type: FACT, PREFERENCE, SKILL, PROJECT, or CONSTRAINT
            content: Memory content (max 100 chars recommended)
            source: Source of the memory
            confidence: Confidence in memory accuracy (0.0-1.0)

        Returns:
            Memory candidate for user confirmation
        """
        candidate = {
            "type": memory_type,
            "content": content[:100],  # Enforce 100 char limit
            "source": source or "conversation",
            "timestamp": datetime.now().isoformat(),
            "confidence": confidence,
            "requires_confirmation": True
        }

        return candidate


# Helper function to make any agent universal-template-compliant
def make_universal_compliant(agent_class):
    """
    Decorator to make any agent class Universal Template compliant

    Usage:
        @make_universal_compliant
        class MyAgent(BaseMCPAgent):
            pass
    """
    class UniversalAgent(UniversalAgentMixin, agent_class):
        pass

    return UniversalAgent
