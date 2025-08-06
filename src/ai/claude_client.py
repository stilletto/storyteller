import os
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import anthropic
from anthropic import AsyncAnthropic
from dotenv import load_dotenv
import json
import logging

load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class GenerationConfig:
    max_tokens: int = 32000
    temperature: float = 1.0
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    enable_thinking: bool = True
    thinking_budget: int = 50000

class ClaudeNeptuneClient:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        self.model = os.getenv("MODEL_NAME", "claude-neptune-v4")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.async_client = AsyncAnthropic(api_key=self.api_key)
        
        self.default_config = GenerationConfig()
        
    def _prepare_thinking_params(self, enable_thinking: bool, budget: int) -> Dict:
        if not enable_thinking:
            return {}
        
        return {
            "thinking": {
                "type": "enabled",
                "budget_tokens": budget
            }
        }
    
    def generate(
        self, 
        system_prompt: str,
        messages: List[Dict[str, Any]],
        config: Optional[GenerationConfig] = None
    ) -> str:
        config = config or self.default_config
        
        try:
            thinking_params = self._prepare_thinking_params(
                config.enable_thinking, 
                config.thinking_budget
            )
            
            params = {
                "model": self.model,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                "system": system_prompt,
                "messages": messages
            }
            
            if thinking_params:
                params.update(thinking_params)
            
            if config.top_p is not None:
                params["top_p"] = config.top_p
            if config.top_k is not None:
                params["top_k"] = config.top_k
            
            response = self.client.messages.create(**params)
            
            if hasattr(response, 'content') and response.content:
                if isinstance(response.content, list):
                    text_content = []
                    for block in response.content:
                        if hasattr(block, 'type'):
                            if block.type == 'text':
                                text_content.append(block.text)
                    return '\n'.join(text_content)
                else:
                    return str(response.content)
            
            return ""
            
        except Exception as e:
            logger.error(f"Generation error: {e}")
            raise
    
    async def generate_async(
        self,
        system_prompt: str,
        messages: List[Dict[str, Any]],
        config: Optional[GenerationConfig] = None
    ) -> str:
        config = config or self.default_config
        
        try:
            thinking_params = self._prepare_thinking_params(
                config.enable_thinking,
                config.thinking_budget
            )
            
            params = {
                "model": self.model,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                "system": system_prompt,
                "messages": messages
            }
            
            if thinking_params:
                params.update(thinking_params)
            
            if config.top_p is not None:
                params["top_p"] = config.top_p
            if config.top_k is not None:
                params["top_k"] = config.top_k
            
            response = await self.async_client.messages.create(**params)
            
            if hasattr(response, 'content') and response.content:
                if isinstance(response.content, list):
                    text_content = []
                    for block in response.content:
                        if hasattr(block, 'type'):
                            if block.type == 'text':
                                text_content.append(block.text)
                    return '\n'.join(text_content)
                else:
                    return str(response.content)
            
            return ""
            
        except Exception as e:
            logger.error(f"Async generation error: {e}")
            raise
    
    def generate_with_context(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Optional[str] = None,
        previous_messages: Optional[List[Dict]] = None,
        config: Optional[GenerationConfig] = None
    ) -> str:
        messages = previous_messages or []
        
        if context:
            context_message = {
                "role": "user",
                "content": f"Контекст:\n{context}\n\n{user_prompt}"
            }
        else:
            context_message = {
                "role": "user", 
                "content": user_prompt
            }
        
        messages.append(context_message)
        
        return self.generate(system_prompt, messages, config)
    
    def continue_generation(
        self,
        previous_text: str,
        continuation_prompt: str = "Продолжай писать с того места, где остановился. Не повторяй уже написанное.",
        config: Optional[GenerationConfig] = None
    ) -> str:
        system_prompt = """Ты писатель, продолжающий работу над книгой в стиле Патрика Ротфусса.
        Сохраняй стиль, тон и атмосферу предыдущего текста.
        Продолжай повествование органично, без резких переходов."""
        
        messages = [
            {
                "role": "user",
                "content": f"Вот текст, который нужно продолжить:\n\n{previous_text}\n\n{continuation_prompt}"
            }
        ]
        
        return self.generate(system_prompt, messages, config)
    
    def edit_text(
        self,
        original_text: str,
        edit_instructions: str,
        config: Optional[GenerationConfig] = None
    ) -> str:
        system_prompt = """Ты редактор, работающий с текстом в стиле Патрика Ротфусса.
        Вноси изменения согласно инструкциям, сохраняя авторский стиль и голос."""
        
        messages = [
            {
                "role": "user",
                "content": f"Оригинальный текст:\n{original_text}\n\nИнструкции для редактирования:\n{edit_instructions}"
            }
        ]
        
        return self.generate(system_prompt, messages, config)
    
    def validate_consistency(
        self,
        text: str,
        context: Dict[str, Any],
        config: Optional[GenerationConfig] = None
    ) -> Dict[str, Any]:
        system_prompt = """Ты эксперт по вселенной "Хроник убийцы короля".
        Проверь текст на соответствие установленному канону, внутреннюю логику и согласованность."""
        
        context_str = json.dumps(context, ensure_ascii=False, indent=2)
        
        messages = [
            {
                "role": "user",
                "content": f"""Проверь следующий текст на согласованность:

{text}

Контекст мира:
{context_str}

Верни результат в формате JSON:
{{
    "is_consistent": true/false,
    "issues": ["список проблем"],
    "suggestions": ["список предложений по исправлению"]
}}"""
            }
        ]
        
        result = self.generate(system_prompt, messages, config)
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {
                "is_consistent": False,
                "issues": ["Не удалось распарсить ответ"],
                "suggestions": []
            }