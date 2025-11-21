"""
CreativeMCP - Creative Content Generation & Optimization System
================================================================

Complete production implementation for creative content generation including
scripts, visual design, music composition, and engagement optimization.

This system:
- Generates creative scripts and narratives
- Designs visual styles and palettes
- Composes music and soundscapes
- Optimizes content for engagement
- Provides A/B testing recommendations
"""

import json
import os
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import logging
import random
from collections import defaultdict

from .base_agent import BaseMCPAgent

# Optional: OpenAI for advanced content generation
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# =============================================================================
# SCRIPT GENERATOR AGENT
# =============================================================================

class ScriptGeneratorAgent(BaseMCPAgent):
    """
    Generate creative scripts for various media formats
    """

    def __init__(self, db_dsn: str = None, openai_api_key: str = None):
        super().__init__(
            agent_id='mcp_creative_scriptgen',
            mcp_system='creative',
            db_dsn=db_dsn
        )
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        if OPENAI_AVAILABLE and self.openai_api_key:
            openai.api_key = self.openai_api_key

    def process(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process script generation

        Args:
            task_input: {
                'content_type': str ('video', 'podcast', 'article', 'social'),
                'topic': str,
                'tone': str (optional: 'professional', 'casual', 'humorous'),
                'length': str (optional: 'short', 'medium', 'long'),
                'target_audience': str (optional)
            }

        Returns:
            Dict with generated script
        """
        content_type = task_input.get('content_type', 'article')
        topic = task_input.get('topic', '')
        tone = task_input.get('tone', 'professional')
        length = task_input.get('length', 'medium')
        audience = task_input.get('target_audience', 'general')

        script = self.generate_script(content_type, topic, tone, length, audience)

        return {
            'content_type': content_type,
            'script': script
        }

    def generate_script(
        self,
        content_type: str,
        topic: str,
        tone: str,
        length: str,
        audience: str
    ) -> Dict[str, Any]:
        """
        Generate creative script

        Args:
            content_type: Type of content
            topic: Script topic
            tone: Desired tone
            length: Script length
            audience: Target audience

        Returns:
            Dict with generated script
        """
        script = {
            'title': '',
            'hook': '',
            'body': '',
            'call_to_action': '',
            'metadata': {}
        }

        # Use AI if available
        if OPENAI_AVAILABLE and self.openai_api_key:
            script = self._generate_script_ai(
                content_type, topic, tone, length, audience
            )
        else:
            script = self._generate_script_template(
                content_type, topic, tone, length, audience
            )

        # Add metadata
        script['metadata'] = {
            'word_count': self._count_words(script),
            'estimated_duration_minutes': self._estimate_duration(script, content_type),
            'tone_analysis': self._analyze_tone(script),
            'readability_score': self._calculate_readability(script)
        }

        return script

    def _generate_script_ai(
        self,
        content_type: str,
        topic: str,
        tone: str,
        length: str,
        audience: str
    ) -> Dict[str, Any]:
        """Generate script using OpenAI"""
        try:
            length_guidance = {
                'short': '100-200 words',
                'medium': '300-500 words',
                'long': '800-1200 words'
            }

            prompt = f"""Create a {content_type} script about "{topic}" with the following specifications:

- Tone: {tone}
- Length: {length_guidance.get(length, '300-500 words')}
- Target Audience: {audience}

Structure:
1. Compelling hook/opening
2. Main content body
3. Strong call-to-action

Return as JSON with keys: title, hook, body, call_to_action
"""

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a {tone} content creator specializing in {content_type} scripts."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.8,
                max_tokens=2000
            )

            result = response.choices[0].message.content

            # Try to parse as JSON
            try:
                script = json.loads(result)
            except:
                # Fallback to text parsing
                script = {
                    'title': f"{topic.title()}",
                    'hook': result[:200],
                    'body': result[200:],
                    'call_to_action': "Learn more and take action today!"
                }

            return script

        except Exception as e:
            self.logger.error(f"AI script generation failed: {e}")
            return self._generate_script_template(content_type, topic, tone, length, audience)

    def _generate_script_template(
        self,
        content_type: str,
        topic: str,
        tone: str,
        length: str,
        audience: str
    ) -> Dict[str, Any]:
        """Generate script using templates"""
        hooks = {
            'professional': f"Understanding {topic} is crucial for modern {audience}.",
            'casual': f"Let's talk about {topic} - it's actually pretty interesting!",
            'humorous': f"You won't believe what I just learned about {topic}!"
        }

        bodies = {
            'short': f"In today's landscape, {topic} plays a vital role. Recent studies show significant impact across industries. Key benefits include improved efficiency and better outcomes.",
            'medium': f"When it comes to {topic}, there are several critical factors to consider. First, understanding the fundamentals provides a solid foundation. Second, practical application drives real results. Third, continuous improvement ensures long-term success. Let's explore each of these in detail.",
            'long': f"The comprehensive guide to {topic} begins with understanding its historical context and evolution. Over the years, approaches have shifted dramatically, influenced by technological advances and changing market demands. Today's best practices incorporate lessons learned from past experiences while embracing innovation. From a strategic perspective, successful implementation requires careful planning, stakeholder alignment, and measurable objectives. Case studies demonstrate that organizations achieving the best results combine proven methodologies with adaptive frameworks. Looking ahead, emerging trends suggest even greater opportunities for those willing to evolve their approach."
        }

        ctas = {
            'video': "Don't forget to like, subscribe, and hit that notification bell!",
            'podcast': "Subscribe to our podcast for more insights!",
            'article': "Want to learn more? Check out our comprehensive guide.",
            'social': "Share your thoughts in the comments below!"
        }

        return {
            'title': f"{topic.title()}: {audience.title()} Guide",
            'hook': hooks.get(tone, hooks['professional']),
            'body': bodies.get(length, bodies['medium']),
            'call_to_action': ctas.get(content_type, ctas['article'])
        }

    def _count_words(self, script: Dict[str, Any]) -> int:
        """Count total words in script"""
        total = 0
        for key in ['title', 'hook', 'body', 'call_to_action']:
            text = script.get(key, '')
            total += len(text.split())
        return total

    def _estimate_duration(self, script: Dict[str, Any], content_type: str) -> float:
        """Estimate content duration in minutes"""
        word_count = self._count_words(script)

        # Average speaking rates
        rates = {
            'video': 150,  # words per minute
            'podcast': 130,
            'article': 200,  # reading speed
            'social': 180
        }

        rate = rates.get(content_type, 150)
        return round(word_count / rate, 1)

    def _analyze_tone(self, script: Dict[str, Any]) -> str:
        """Analyze script tone"""
        text = ' '.join([script.get(k, '') for k in ['hook', 'body', 'call_to_action']])
        text_lower = text.lower()

        # Simple keyword-based analysis
        if any(word in text_lower for word in ['crucial', 'important', 'significant', 'professional']):
            return 'professional'
        elif any(word in text_lower for word in ['hey', 'cool', 'awesome', 'check out']):
            return 'casual'
        elif any(word in text_lower for word in ['funny', 'hilarious', 'joke', 'laugh']):
            return 'humorous'
        else:
            return 'neutral'

    def _calculate_readability(self, script: Dict[str, Any]) -> float:
        """Calculate readability score (simplified Flesch)"""
        text = ' '.join([script.get(k, '') for k in ['body']])
        words = text.split()
        sentences = re.split(r'[.!?]+', text)

        if not words or not sentences:
            return 50.0

        avg_words_per_sentence = len(words) / max(1, len(sentences))

        # Simplified score (higher = easier to read)
        score = 100 - (avg_words_per_sentence * 2)

        return max(0, min(100, score))


# =============================================================================
# VISUAL STYLE AGENT
# =============================================================================

class VisualStyleAgent(BaseMCPAgent):
    """
    Design visual styles and color palettes
    """

    def __init__(self, db_dsn: str = None):
        super().__init__(
            agent_id='mcp_creative_visual',
            mcp_system='creative',
            db_dsn=db_dsn
        )

    def process(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process visual style generation

        Args:
            task_input: {
                'brand_identity': str,
                'mood': str (optional: 'energetic', 'calm', 'professional'),
                'industry': str (optional),
                'include_palette': bool (optional)
            }

        Returns:
            Dict with visual style guide
        """
        brand = task_input.get('brand_identity', '')
        mood = task_input.get('mood', 'professional')
        industry = task_input.get('industry', 'technology')
        include_palette = task_input.get('include_palette', True)

        style_guide = self.create_style_guide(brand, mood, industry, include_palette)

        return {
            'brand_identity': brand,
            'style_guide': style_guide
        }

    def create_style_guide(
        self,
        brand: str,
        mood: str,
        industry: str,
        include_palette: bool
    ) -> Dict[str, Any]:
        """
        Create comprehensive visual style guide

        Args:
            brand: Brand identity
            mood: Desired mood
            industry: Industry sector
            include_palette: Include color palette

        Returns:
            Dict with style guide
        """
        guide = {
            'color_palette': {},
            'typography': {},
            'visual_elements': {},
            'layout_principles': []
        }

        # Color palette
        if include_palette:
            guide['color_palette'] = self._generate_color_palette(mood, industry)

        # Typography
        guide['typography'] = self._recommend_typography(mood, industry)

        # Visual elements
        guide['visual_elements'] = self._suggest_visual_elements(mood, industry)

        # Layout principles
        guide['layout_principles'] = self._define_layout_principles(mood)

        return guide

    def _generate_color_palette(self, mood: str, industry: str) -> Dict[str, Any]:
        """Generate color palette"""
        # Mood-based color palettes
        palettes = {
            'energetic': {
                'primary': '#FF6B6B',
                'secondary': '#4ECDC4',
                'accent': '#FFE66D',
                'neutral': '#F7F7F7',
                'dark': '#2C3E50'
            },
            'calm': {
                'primary': '#6C5CE7',
                'secondary': '#A29BFE',
                'accent': '#74B9FF',
                'neutral': '#DFE6E9',
                'dark': '#2D3436'
            },
            'professional': {
                'primary': '#0984E3',
                'secondary': '#6C5CE7',
                'accent': '#00B894',
                'neutral': '#B2BEC3',
                'dark': '#2D3436'
            },
            'creative': {
                'primary': '#FD79A8',
                'secondary': '#FDCB6E',
                'accent': '#6C5CE7',
                'neutral': '#DFE6E9',
                'dark': '#2D3436'
            }
        }

        base_palette = palettes.get(mood, palettes['professional'])

        # Industry adjustments
        industry_overrides = {
            'finance': {'primary': '#0984E3', 'accent': '#00B894'},
            'health': {'primary': '#00B894', 'accent': '#55EFC4'},
            'education': {'primary': '#6C5CE7', 'accent': '#A29BFE'},
            'entertainment': {'primary': '#FD79A8', 'accent': '#FDCB6E'}
        }

        if industry in industry_overrides:
            base_palette.update(industry_overrides[industry])

        return {
            'colors': base_palette,
            'usage_guidelines': {
                'primary': 'Main brand color for headers and CTAs',
                'secondary': 'Supporting elements and backgrounds',
                'accent': 'Highlights and important UI elements',
                'neutral': 'Body text and subtle backgrounds',
                'dark': 'Text and strong contrast elements'
            }
        }

    def _recommend_typography(self, mood: str, industry: str) -> Dict[str, Any]:
        """Recommend typography"""
        fonts = {
            'energetic': {
                'headings': 'Montserrat',
                'body': 'Open Sans',
                'accent': 'Raleway'
            },
            'calm': {
                'headings': 'Playfair Display',
                'body': 'Lora',
                'accent': 'Merriweather'
            },
            'professional': {
                'headings': 'Roboto',
                'body': 'Inter',
                'accent': 'Lato'
            },
            'creative': {
                'headings': 'Poppins',
                'body': 'Nunito',
                'accent': 'Quicksand'
            }
        }

        font_set = fonts.get(mood, fonts['professional'])

        return {
            'font_families': font_set,
            'size_scale': {
                'h1': '2.5rem',
                'h2': '2rem',
                'h3': '1.5rem',
                'body': '1rem',
                'small': '0.875rem'
            },
            'line_height': {
                'headings': 1.2,
                'body': 1.6
            },
            'font_weights': {
                'light': 300,
                'regular': 400,
                'medium': 500,
                'bold': 700
            }
        }

    def _suggest_visual_elements(self, mood: str, industry: str) -> Dict[str, Any]:
        """Suggest visual elements"""
        elements = {
            'energetic': {
                'shapes': 'Angular, dynamic shapes',
                'imagery_style': 'High contrast, vibrant',
                'icons': 'Bold, filled icons',
                'patterns': 'Geometric patterns'
            },
            'calm': {
                'shapes': 'Soft, rounded shapes',
                'imagery_style': 'Muted tones, peaceful',
                'icons': 'Minimal, line icons',
                'patterns': 'Organic, flowing patterns'
            },
            'professional': {
                'shapes': 'Clean, geometric shapes',
                'imagery_style': 'Professional photography',
                'icons': 'Simple, outlined icons',
                'patterns': 'Grid-based layouts'
            }
        }

        return elements.get(mood, elements['professional'])

    def _define_layout_principles(self, mood: str) -> List[str]:
        """Define layout principles"""
        principles = {
            'energetic': [
                'Use asymmetric layouts for visual interest',
                'Incorporate bold typography and large imagery',
                'Maintain high contrast between elements',
                'Use whitespace strategically to create impact'
            ],
            'calm': [
                'Emphasize balance and symmetry',
                'Use generous whitespace for breathing room',
                'Create visual hierarchy through subtle size differences',
                'Maintain consistent spacing throughout'
            ],
            'professional': [
                'Follow grid-based layouts for consistency',
                'Use clear visual hierarchy',
                'Maintain proper alignment across elements',
                'Balance text and visual content'
            ]
        }

        return principles.get(mood, principles['professional'])


# =============================================================================
# MUSIC COMPOSER AGENT
# =============================================================================

class MusicComposerAgent(BaseMCPAgent):
    """
    Compose music and soundscapes for content
    """

    def __init__(self, db_dsn: str = None):
        super().__init__(
            agent_id='mcp_creative_music',
            mcp_system='creative',
            db_dsn=db_dsn
        )

    def process(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process music composition

        Args:
            task_input: {
                'mood': str,
                'duration_seconds': int,
                'genre': str (optional),
                'instruments': list (optional)
            }

        Returns:
            Dict with music composition spec
        """
        mood = task_input.get('mood', 'upbeat')
        duration = task_input.get('duration_seconds', 60)
        genre = task_input.get('genre', 'electronic')
        instruments = task_input.get('instruments', [])

        composition = self.compose_music(mood, duration, genre, instruments)

        return {
            'mood': mood,
            'composition': composition
        }

    def compose_music(
        self,
        mood: str,
        duration: int,
        genre: str,
        instruments: List[str]
    ) -> Dict[str, Any]:
        """
        Create music composition specification

        Args:
            mood: Musical mood
            duration: Duration in seconds
            genre: Music genre
            instruments: Instruments to use

        Returns:
            Dict with composition spec
        """
        composition = {
            'structure': self._create_structure(duration),
            'tempo_bpm': self._determine_tempo(mood, genre),
            'key': self._suggest_key(mood),
            'instrumentation': self._select_instruments(genre, instruments),
            'arrangement': self._create_arrangement(mood, genre),
            'production_notes': []
        }

        # Add production notes
        composition['production_notes'] = self._add_production_notes(mood, genre)

        return composition

    def _create_structure(self, duration: int) -> List[Dict[str, Any]]:
        """Create musical structure"""
        # Standard structure based on duration
        if duration <= 30:
            # Short piece
            structure = [
                {'section': 'intro', 'duration_seconds': 5},
                {'section': 'main', 'duration_seconds': 20},
                {'section': 'outro', 'duration_seconds': 5}
            ]
        elif duration <= 60:
            # Medium piece
            structure = [
                {'section': 'intro', 'duration_seconds': 8},
                {'section': 'verse', 'duration_seconds': 15},
                {'section': 'chorus', 'duration_seconds': 15},
                {'section': 'verse', 'duration_seconds': 12},
                {'section': 'outro', 'duration_seconds': 10}
            ]
        else:
            # Long piece
            structure = [
                {'section': 'intro', 'duration_seconds': 10},
                {'section': 'verse', 'duration_seconds': 20},
                {'section': 'chorus', 'duration_seconds': 20},
                {'section': 'bridge', 'duration_seconds': 15},
                {'section': 'chorus', 'duration_seconds': 20},
                {'section': 'outro', 'duration_seconds': 15}
            ]

        return structure

    def _determine_tempo(self, mood: str, genre: str) -> int:
        """Determine appropriate tempo"""
        tempo_ranges = {
            'upbeat': (120, 140),
            'calm': (60, 80),
            'energetic': (140, 160),
            'dramatic': (90, 110),
            'ambient': (70, 90)
        }

        min_tempo, max_tempo = tempo_ranges.get(mood, (100, 120))
        return random.randint(min_tempo, max_tempo)

    def _suggest_key(self, mood: str) -> str:
        """Suggest musical key"""
        # Major keys for upbeat, minor for dramatic/calm
        major_keys = ['C', 'G', 'D', 'A', 'E', 'F']
        minor_keys = ['Am', 'Em', 'Dm', 'Bm', 'F#m', 'Cm']

        if mood in ['upbeat', 'energetic']:
            return random.choice(major_keys) + ' Major'
        else:
            return random.choice(minor_keys)

    def _select_instruments(self, genre: str, requested: List[str]) -> List[str]:
        """Select instruments for composition"""
        if requested:
            return requested

        # Genre-based instrument selection
        genre_instruments = {
            'electronic': ['Synthesizer', 'Drum Machine', 'Bass Synth', 'Pad'],
            'acoustic': ['Acoustic Guitar', 'Piano', 'Strings', 'Light Percussion'],
            'orchestral': ['Strings', 'Brass', 'Woodwinds', 'Timpani', 'Piano'],
            'ambient': ['Pad', 'Atmospheric Synth', 'Subtle Percussion', 'Field Recordings'],
            'corporate': ['Piano', 'Soft Synth', 'Light Strings', 'Subtle Percussion']
        }

        return genre_instruments.get(genre, genre_instruments['electronic'])

    def _create_arrangement(self, mood: str, genre: str) -> Dict[str, List[str]]:
        """Create arrangement notes"""
        return {
            'intro': [
                'Start with ambient pads',
                'Gradually introduce melodic elements',
                'Build anticipation'
            ],
            'main': [
                'Full instrumentation',
                'Establish main theme',
                'Develop harmonic progression'
            ],
            'outro': [
                'Reduce elements gradually',
                'Return to ambient texture',
                'Fade smoothly'
            ]
        }

    def _add_production_notes(self, mood: str, genre: str) -> List[str]:
        """Add production notes"""
        notes = [
            f'Target {mood} emotional tone throughout',
            f'Use {genre}-appropriate production techniques',
            'Apply subtle reverb for depth',
            'Balance frequencies for clarity',
            'Master for streaming platforms'
        ]

        return notes


# =============================================================================
# ENGAGEMENT OPTIMIZER AGENT
# =============================================================================

class EngagementOptimizerAgent(BaseMCPAgent):
    """
    Optimize content for engagement and performance
    """

    def __init__(self, db_dsn: str = None):
        super().__init__(
            agent_id='mcp_creative_engagement',
            mcp_system='creative',
            db_dsn=db_dsn
        )

    def process(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process engagement optimization

        Args:
            task_input: {
                'content': dict or str,
                'platform': str,
                'metrics': dict (optional: current performance),
                'goals': list (optional)
            }

        Returns:
            Dict with optimization recommendations
        """
        content = task_input.get('content', {})
        platform = task_input.get('platform', 'website')
        metrics = task_input.get('metrics', {})
        goals = task_input.get('goals', ['increase_engagement'])

        recommendations = self.optimize_engagement(content, platform, metrics, goals)

        return {
            'platform': platform,
            'recommendations': recommendations
        }

    def optimize_engagement(
        self,
        content: Any,
        platform: str,
        metrics: Dict[str, float],
        goals: List[str]
    ) -> Dict[str, Any]:
        """
        Generate engagement optimization recommendations

        Args:
            content: Content to optimize
            platform: Target platform
            metrics: Current performance metrics
            goals: Optimization goals

        Returns:
            Dict with recommendations
        """
        recommendations = {
            'content_improvements': [],
            'timing_recommendations': {},
            'ab_test_suggestions': [],
            'engagement_tactics': [],
            'predicted_impact': {}
        }

        # Content improvements
        recommendations['content_improvements'] = self._suggest_content_improvements(
            content, platform
        )

        # Timing recommendations
        recommendations['timing_recommendations'] = self._recommend_timing(platform)

        # A/B test suggestions
        recommendations['ab_test_suggestions'] = self._suggest_ab_tests(content, platform)

        # Engagement tactics
        recommendations['engagement_tactics'] = self._suggest_engagement_tactics(platform, goals)

        # Predicted impact
        recommendations['predicted_impact'] = self._predict_impact(
            recommendations, metrics
        )

        return recommendations

    def _suggest_content_improvements(
        self,
        content: Any,
        platform: str
    ) -> List[Dict[str, str]]:
        """Suggest content improvements"""
        improvements = []

        # Platform-specific recommendations
        if platform == 'social':
            improvements.extend([
                {
                    'aspect': 'Hook',
                    'recommendation': 'Start with a compelling question or statement',
                    'priority': 'high'
                },
                {
                    'aspect': 'Length',
                    'recommendation': 'Keep under 280 characters for maximum engagement',
                    'priority': 'medium'
                },
                {
                    'aspect': 'Hashtags',
                    'recommendation': 'Use 3-5 relevant hashtags',
                    'priority': 'medium'
                }
            ])

        elif platform == 'video':
            improvements.extend([
                {
                    'aspect': 'First 3 seconds',
                    'recommendation': 'Hook viewers immediately with visual impact',
                    'priority': 'high'
                },
                {
                    'aspect': 'Captions',
                    'recommendation': 'Add captions for accessibility and silent viewing',
                    'priority': 'high'
                },
                {
                    'aspect': 'Length',
                    'recommendation': 'Aim for 60-90 seconds for social platforms',
                    'priority': 'medium'
                }
            ])

        elif platform == 'website':
            improvements.extend([
                {
                    'aspect': 'Headlines',
                    'recommendation': 'Use numbers and power words',
                    'priority': 'high'
                },
                {
                    'aspect': 'Formatting',
                    'recommendation': 'Break content into scannable sections with subheadings',
                    'priority': 'medium'
                },
                {
                    'aspect': 'Visuals',
                    'recommendation': 'Include relevant images every 300-500 words',
                    'priority': 'medium'
                }
            ])

        return improvements

    def _recommend_timing(self, platform: str) -> Dict[str, Any]:
        """Recommend optimal posting times"""
        # Platform-specific optimal times
        timing = {
            'social': {
                'best_days': ['Tuesday', 'Wednesday', 'Thursday'],
                'best_times': ['9:00 AM', '1:00 PM', '5:00 PM'],
                'timezone': 'Local audience timezone',
                'frequency': 'Daily or 3-5 times per week'
            },
            'video': {
                'best_days': ['Friday', 'Saturday', 'Sunday'],
                'best_times': ['7:00 PM', '9:00 PM'],
                'timezone': 'Audience primary timezone',
                'frequency': 'Weekly or bi-weekly'
            },
            'website': {
                'best_days': ['Monday', 'Tuesday'],
                'best_times': ['Morning: 8-10 AM'],
                'timezone': 'Not time-sensitive',
                'frequency': 'Weekly or as needed'
            },
            'email': {
                'best_days': ['Tuesday', 'Wednesday', 'Thursday'],
                'best_times': ['10:00 AM', '2:00 PM'],
                'timezone': 'Recipient timezone',
                'frequency': 'Weekly or bi-weekly'
            }
        }

        return timing.get(platform, timing['website'])

    def _suggest_ab_tests(self, content: Any, platform: str) -> List[Dict[str, Any]]:
        """Suggest A/B tests"""
        tests = []

        if platform == 'social':
            tests.extend([
                {
                    'test_element': 'Image vs Video',
                    'variant_a': 'Static image with text overlay',
                    'variant_b': 'Short video (5-10 seconds)',
                    'metric_to_track': 'Engagement rate'
                },
                {
                    'test_element': 'CTA Placement',
                    'variant_a': 'CTA at beginning',
                    'variant_b': 'CTA at end',
                    'metric_to_track': 'Click-through rate'
                }
            ])

        elif platform == 'email':
            tests.extend([
                {
                    'test_element': 'Subject Line',
                    'variant_a': 'Question format',
                    'variant_b': 'Statement format',
                    'metric_to_track': 'Open rate'
                },
                {
                    'test_element': 'Send Time',
                    'variant_a': 'Morning (9 AM)',
                    'variant_b': 'Afternoon (2 PM)',
                    'metric_to_track': 'Open rate'
                }
            ])

        elif platform == 'website':
            tests.extend([
                {
                    'test_element': 'Headline',
                    'variant_a': 'How-to format',
                    'variant_b': 'List format',
                    'metric_to_track': 'Time on page'
                },
                {
                    'test_element': 'CTA Button Color',
                    'variant_a': 'Blue',
                    'variant_b': 'Green',
                    'metric_to_track': 'Conversion rate'
                }
            ])

        return tests

    def _suggest_engagement_tactics(
        self,
        platform: str,
        goals: List[str]
    ) -> List[str]:
        """Suggest engagement tactics"""
        tactics = []

        if 'increase_engagement' in goals:
            tactics.extend([
                'Ask questions to encourage comments',
                'Use interactive elements (polls, quizzes)',
                'Respond to comments within first hour',
                'Create shareable, valuable content'
            ])

        if 'build_community' in goals:
            tactics.extend([
                'Highlight user-generated content',
                'Create consistent content series',
                'Host live Q&A sessions',
                'Build exclusive communities or groups'
            ])

        if 'drive_conversions' in goals:
            tactics.extend([
                'Use clear, compelling CTAs',
                'Offer limited-time incentives',
                'Showcase social proof and testimonials',
                'Simplify conversion process'
            ])

        return tactics

    def _predict_impact(
        self,
        recommendations: Dict[str, Any],
        current_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """Predict impact of recommendations"""
        # Simulated impact prediction
        baseline_engagement = current_metrics.get('engagement_rate', 2.0)
        baseline_reach = current_metrics.get('reach', 1000)

        improvements = recommendations['content_improvements']
        high_priority_count = sum(1 for i in improvements if i.get('priority') == 'high')

        # Estimate improvements
        engagement_lift = 5 + (high_priority_count * 3)  # Percentage
        reach_lift = 10 + (high_priority_count * 5)  # Percentage

        return {
            'engagement_rate': {
                'current': baseline_engagement,
                'predicted': round(baseline_engagement * (1 + engagement_lift / 100), 2),
                'lift_percent': engagement_lift
            },
            'reach': {
                'current': baseline_reach,
                'predicted': int(baseline_reach * (1 + reach_lift / 100)),
                'lift_percent': reach_lift
            },
            'confidence': 'medium',
            'timeframe': '2-4 weeks'
        }


# =============================================================================
# CREATIVE ORCHESTRATOR
# =============================================================================

class CreativeOrchestrator:
    """
    Orchestrator for CreativeMCP content generation system

    Coordinates all creative agents:
    1. ScriptGeneratorAgent - Script creation
    2. VisualStyleAgent - Visual design
    3. MusicComposerAgent - Music composition
    4. EngagementOptimizerAgent - Engagement optimization
    """

    def __init__(self, db_dsn: str = None, openai_api_key: str = None):
        """
        Initialize Creative orchestrator

        Args:
            db_dsn: Database connection string
            openai_api_key: OpenAI API key
        """
        self.db_dsn = db_dsn or os.getenv(
            "DATABASE_URL",
            "postgresql://mcp_user:change-this-in-production-use-strong-password@postgres:5432/mcp"
        )
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        self.logger = logging.getLogger("CreativeOrchestrator")
        self.logger.info("Initializing CreativeMCP Orchestrator")

        # Initialize agents
        self.agents = {}
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize all Creative agents"""
        try:
            self.agents['script'] = ScriptGeneratorAgent(
                db_dsn=self.db_dsn,
                openai_api_key=self.openai_api_key
            )
            self.agents['visual'] = VisualStyleAgent(db_dsn=self.db_dsn)
            self.agents['music'] = MusicComposerAgent(db_dsn=self.db_dsn)
            self.agents['engagement'] = EngagementOptimizerAgent(db_dsn=self.db_dsn)

            self.logger.info(f"Initialized {len(self.agents)} Creative agents")

        except Exception as e:
            self.logger.error(f"Failed to initialize agents: {e}")

    def execute_task(
        self,
        task_type: str,
        task_input: Dict[str, Any],
        material_id: Optional[uuid.UUID] = None,
        priority: int = 5
    ) -> Dict[str, Any]:
        """
        Execute a Creative task

        Args:
            task_type: Type of task
            task_input: Task input data
            material_id: Optional related material
            priority: Task priority

        Returns:
            Dict with task results
        """
        self.logger.info(f"Executing Creative task: {task_type}")

        try:
            if task_type == 'content_generation':
                return self.agents['script'].execute_task(
                    task_type, task_input, material_id, priority
                )

            elif task_type == 'script_writing':
                return self.agents['script'].execute_task(
                    task_type, task_input, material_id, priority
                )

            elif task_type == 'visual_design':
                return self.agents['visual'].execute_task(
                    task_type, task_input, material_id, priority
                )

            elif task_type == 'music_composition':
                return self.agents['music'].execute_task(
                    task_type, task_input, material_id, priority
                )

            elif task_type == 'engagement_optimization':
                return self.agents['engagement'].execute_task(
                    task_type, task_input, material_id, priority
                )

            elif task_type == 'complete_campaign':
                return self.create_complete_campaign(task_input)

            else:
                return {
                    'status': 'error',
                    'error': f'Unknown task type: {task_type}'
                }

        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def create_complete_campaign(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create complete creative campaign

        Args:
            task_input: {
                'topic': str,
                'platform': str,
                'brand_identity': str (optional),
                'include_visuals': bool (optional),
                'include_music': bool (optional)
            }

        Returns:
            Dict with complete campaign
        """
        topic = task_input.get('topic', '')
        platform = task_input.get('platform', 'social')
        brand = task_input.get('brand_identity', topic)
        include_visuals = task_input.get('include_visuals', True)
        include_music = task_input.get('include_music', False)

        campaign = {}

        # Step 1: Generate script
        script_result = self.agents['script'].execute_task(
            task_type='content_generation',
            task_input={
                'content_type': platform,
                'topic': topic,
                'tone': 'professional'
            }
        )
        campaign['script'] = script_result['output']['script']

        # Step 2: Visual style guide (if requested)
        if include_visuals:
            visual_result = self.agents['visual'].execute_task(
                task_type='visual_design',
                task_input={
                    'brand_identity': brand,
                    'mood': 'professional'
                }
            )
            campaign['visual_guide'] = visual_result['output']['style_guide']

        # Step 3: Music composition (if requested)
        if include_music and platform in ['video', 'podcast']:
            music_result = self.agents['music'].execute_task(
                task_type='music_composition',
                task_input={
                    'mood': 'upbeat',
                    'duration_seconds': 60,
                    'genre': 'corporate'
                }
            )
            campaign['music'] = music_result['output']['composition']

        # Step 4: Engagement optimization
        engagement_result = self.agents['engagement'].execute_task(
            task_type='engagement_optimization',
            task_input={
                'content': campaign['script'],
                'platform': platform
            }
        )
        campaign['optimization'] = engagement_result['output']['recommendations']

        return {
            'status': 'completed',
            'campaign': campaign
        }

    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return {
            'system': 'creative',
            'status': 'active',
            'agents': list(self.agents.keys()),
            'agent_count': len(self.agents)
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_creative_orchestrator(
    db_dsn: str = None,
    openai_api_key: str = None
) -> CreativeOrchestrator:
    """
    Factory function to create Creative orchestrator

    Args:
        db_dsn: Database connection string
        openai_api_key: OpenAI API key

    Returns:
        CreativeOrchestrator instance
    """
    return CreativeOrchestrator(
        db_dsn=db_dsn,
        openai_api_key=openai_api_key
    )


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

if __name__ == "__main__":
    # Initialize orchestrator
    orchestrator = create_creative_orchestrator()

    # Example: Create complete campaign
    result = orchestrator.create_complete_campaign({
        'topic': 'AI in Healthcare',
        'platform': 'video',
        'brand_identity': 'HealthTech Innovations',
        'include_visuals': True,
        'include_music': True
    })

    print("Campaign Result:", json.dumps(result, indent=2, default=str))
