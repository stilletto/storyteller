import os
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging

from src.ai.claude_client import ClaudeNeptuneClient, GenerationConfig
from src.templates.prompts import RothfussPrompts, CharacterProfile
from src.story.plot_manager import PlotManager, PlotImportance

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ChapterConfig:
    chapter_number: int
    narrative_type: str  # "frame" или "inner"
    target_word_count: int = 5000
    plot_points_to_introduce: List[str] = field(default_factory=list)
    plot_points_to_resolve: List[str] = field(default_factory=list)
    mood: str = "mysterious"
    time_of_day: str = "night"
    key_scenes: List[str] = field(default_factory=list)

@dataclass
class GenerationSession:
    session_id: str
    start_time: datetime
    chapters_generated: List[int] = field(default_factory=list)
    total_words: int = 0
    context_history: List[Dict] = field(default_factory=list)
    quality_scores: Dict[str, float] = field(default_factory=dict)

class StoryEngine:
    def __init__(self):
        self.client = ClaudeNeptuneClient()
        self.prompts = RothfussPrompts()
        self.plot_manager = PlotManager()
        self.current_session: Optional[GenerationSession] = None
        self.generated_chapters: Dict[int, str] = {}
        self.chapter_metadata: Dict[int, Dict] = {}
        self.context_window: List[str] = []
        self.max_context_size = 50000  # символов
        
        # Загружаем персонажей
        self._initialize_characters()
        
    def _initialize_characters(self):
        """Инициализация основных персонажей"""
        self.characters = {
            "kvothe": CharacterProfile(
                name="Квоут",
                role="Главный герой, рассказчик",
                personality="Умный, талантливый, самоуверенный, но также раненый и мудрый",
                speech_patterns=[
                    "Использует музыкальные метафоры",
                    "Склонен к драматизации",
                    "Самоироничен",
                    "Образованная речь"
                ],
                current_state="Рассказывает свою историю, зная её конец",
                goals=["Рассказать правдивую историю", "Предупредить мир"],
                relationships={
                    "Денна": "Любовь всей жизни",
                    "Баст": "Ученик и друг",
                    "Хроникёр": "Слушатель и записыватель"
                }
            ),
            "denna": CharacterProfile(
                name="Денна",
                role="Загадочная возлюбленная",
                personality="Независимая, умная, скрытная, ранимая под маской силы",
                speech_patterns=[
                    "Изящная речь",
                    "Уклончивые ответы",
                    "Поэтичные обороты",
                    "Скрытый подтекст"
                ],
                current_state="Связана с таинственным покровителем",
                goals=["Выжить", "Найти своё место", "Защитить Квоута от правды"],
                relationships={
                    "Квоут": "Любовь и страх близости",
                    "Мастер Эш": "Покровитель и учитель"
                }
            ),
            "bast": CharacterProfile(
                name="Баст",
                role="Ученик Коута, принц фейри",
                personality="Игривый, опасный, преданный, нечеловеческий",
                speech_patterns=[
                    "Переключение между легкомыслием и угрозой",
                    "Фейрийские обороты",
                    "Называет Коута 'Реши'",
                    "Скрывает истинную природу"
                ],
                current_state="Пытается вернуть Коуту его силу",
                goals=["Вернуть учителя", "Защитить от опасности"],
                relationships={
                    "Коут": "Учитель и объект поклонения",
                    "Хроникёр": "Инструмент для своих целей"
                }
            )
        }
    
    def start_session(self) -> str:
        """Начало новой сессии генерации"""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session = GenerationSession(
            session_id=session_id,
            start_time=datetime.now()
        )
        logger.info(f"Начата сессия генерации: {session_id}")
        return session_id
    
    async def generate_chapter(self, config: ChapterConfig) -> Tuple[str, Dict]:
        """Генерация главы книги"""
        if not self.current_session:
            self.start_session()
        
        logger.info(f"Генерация главы {config.chapter_number}")
        
        # Подготовка контекста
        context = self._prepare_chapter_context(config)
        
        # Выбор промпта в зависимости от типа повествования
        if config.narrative_type == "frame":
            system_prompt = self.prompts.get_system_prompt_base()
            chapter_prompt = self.prompts.get_frame_narrative_prompt()
        else:
            system_prompt = self.prompts.get_system_prompt_base()
            chapter_prompt = self.prompts.get_inner_narrative_prompt()
        
        # Добавление информации о сюжете
        plot_context = self._prepare_plot_context(config)
        
        # Формирование финального промпта
        final_prompt = f"""{chapter_prompt}

КОНТЕКСТ ГЛАВЫ {config.chapter_number}:
{context}

СЮЖЕТНЫЕ ЭЛЕМЕНТЫ:
{plot_context}

Целевая длина: {config.target_word_count} слов.
Настроение: {config.mood}

Начни главу и развивай её органично, следуя стилю Ротфусса."""
        
        # Генерация
        generation_config = GenerationConfig(
            max_tokens=32000,
            temperature=0.9,
            enable_thinking=True,
            thinking_budget=30000
        )
        
        try:
            # Генерация основного текста
            chapter_text = await self.client.generate_async(
                system_prompt=system_prompt,
                messages=[{"role": "user", "content": final_prompt}],
                config=generation_config
            )
            
            # Сохранение результата
            self.generated_chapters[config.chapter_number] = chapter_text
            
            # Обновление метаданных
            metadata = {
                "chapter_number": config.chapter_number,
                "narrative_type": config.narrative_type,
                "word_count": len(chapter_text.split()),
                "generated_at": datetime.now().isoformat(),
                "plot_points_introduced": config.plot_points_to_introduce,
                "plot_points_resolved": config.plot_points_to_resolve
            }
            self.chapter_metadata[config.chapter_number] = metadata
            
            # Обновление контекста
            self._update_context(chapter_text)
            
            # Обновление сюжета
            self._update_plot_state(config)
            
            # Обновление сессии
            self.current_session.chapters_generated.append(config.chapter_number)
            self.current_session.total_words += metadata["word_count"]
            
            logger.info(f"Глава {config.chapter_number} сгенерирована: {metadata['word_count']} слов")
            
            return chapter_text, metadata
            
        except Exception as e:
            logger.error(f"Ошибка при генерации главы: {e}")
            raise
    
    def _prepare_chapter_context(self, config: ChapterConfig) -> str:
        """Подготовка контекста для главы"""
        context_parts = []
        
        # Добавляем краткое содержание предыдущих глав
        if config.chapter_number > 1:
            prev_chapter = config.chapter_number - 1
            if prev_chapter in self.generated_chapters:
                prev_text = self.generated_chapters[prev_chapter]
                # Берём последние 1000 символов предыдущей главы
                context_parts.append(f"Конец предыдущей главы:\n{prev_text[-1000:]}")
        
        # Добавляем информацию о текущем состоянии персонажей
        if config.key_scenes:
            for scene in config.key_scenes:
                if "Денна" in scene:
                    context_parts.append(f"Состояние Денны: {self.characters['denna'].current_state}")
                if "Баст" in scene:
                    context_parts.append(f"Состояние Баста: {self.characters['bast'].current_state}")
        
        # Добавляем напоминание о стиле
        if config.narrative_type == "frame" and config.chapter_number % 5 == 1:
            context_parts.append("Начни с описания тишины из трёх частей")
        
        return "\n\n".join(context_parts)
    
    def _prepare_plot_context(self, config: ChapterConfig) -> str:
        """Подготовка сюжетного контекста"""
        plot_parts = []
        
        # Активные сюжетные линии
        active_plots = self.plot_manager.get_active_plots()
        if active_plots:
            plot_summaries = [f"- {p.title}: {p.description}" 
                            for p in active_plots[:3]]  # Максимум 3
            plot_parts.append("Активные сюжетные линии:\n" + "\n".join(plot_summaries))
        
        # Сюжеты для введения
        if config.plot_points_to_introduce:
            plot_parts.append(f"Ввести в этой главе: {', '.join(config.plot_points_to_introduce)}")
        
        # Сюжеты для разрешения
        if config.plot_points_to_resolve:
            plot_parts.append(f"Разрешить в этой главе: {', '.join(config.plot_points_to_resolve)}")
        
        # Неразрешённые тайны
        mysteries = list(self.plot_manager.unresolved_mysteries)[:3]
        if mysteries:
            plot_parts.append(f"Помни о тайнах: {', '.join(mysteries)}")
        
        return "\n".join(plot_parts)
    
    def _update_context(self, new_text: str):
        """Обновление контекстного окна"""
        self.context_window.append(new_text[:5000])  # Сохраняем первые 5000 символов
        
        # Ограничиваем размер контекста
        while sum(len(t) for t in self.context_window) > self.max_context_size:
            self.context_window.pop(0)
    
    def _update_plot_state(self, config: ChapterConfig):
        """Обновление состояния сюжета"""
        # Вводим новые сюжетные точки
        for plot_id in config.plot_points_to_introduce:
            self.plot_manager.introduce_plot_point(plot_id, config.chapter_number)
        
        # Разрешаем сюжетные точки
        for plot_id in config.plot_points_to_resolve:
            self.plot_manager.resolve_plot_point(
                plot_id, 
                f"Разрешено в главе {config.chapter_number}",
                config.chapter_number
            )
    
    async def continue_chapter(self, chapter_number: int, additional_words: int = 1000) -> str:
        """Продолжение существующей главы"""
        if chapter_number not in self.generated_chapters:
            raise ValueError(f"Глава {chapter_number} не найдена")
        
        current_text = self.generated_chapters[chapter_number]
        
        continuation_prompt = self.prompts.create_continuation_prompt(
            previous_text=current_text,
            target_length=additional_words
        )
        
        config = GenerationConfig(
            max_tokens=16000,
            temperature=0.9,
            enable_thinking=True
        )
        
        continuation = await self.client.generate_async(
            system_prompt=self.prompts.get_system_prompt_base(),
            messages=[{"role": "user", "content": continuation_prompt}],
            config=config
        )
        
        # Объединяем тексты
        full_text = current_text + "\n\n" + continuation
        self.generated_chapters[chapter_number] = full_text
        
        # Обновляем метаданные
        self.chapter_metadata[chapter_number]["word_count"] = len(full_text.split())
        self.chapter_metadata[chapter_number]["last_updated"] = datetime.now().isoformat()
        
        return continuation
    
    async def edit_chapter(self, chapter_number: int, edit_instructions: str) -> str:
        """Редактирование главы"""
        if chapter_number not in self.generated_chapters:
            raise ValueError(f"Глава {chapter_number} не найдена")
        
        original_text = self.generated_chapters[chapter_number]
        
        edited_text = self.client.edit_text(
            original_text=original_text,
            edit_instructions=edit_instructions
        )
        
        self.generated_chapters[chapter_number] = edited_text
        self.chapter_metadata[chapter_number]["edited_at"] = datetime.now().isoformat()
        
        return edited_text
    
    def evaluate_chapter_quality(self, chapter_number: int) -> Dict[str, Any]:
        """Оценка качества главы"""
        if chapter_number not in self.generated_chapters:
            raise ValueError(f"Глава {chapter_number} не найдена")
        
        text = self.generated_chapters[chapter_number]
        metadata = self.chapter_metadata[chapter_number]
        
        # Проверка соответствия стилю
        style_markers = {
            "silence_description": "тишина из трех частей" in text.lower(),
            "similes": text.count("словно") + text.count("как") + text.count("будто"),
            "dialogue_quality": bool(text.count('"') > 20),  # Есть диалоги
            "narrative_voice": metadata["narrative_type"] == "inner" and "я" in text[:100]
        }
        
        # Проверка сюжета
        plot_checks = {
            "plots_introduced": len(metadata.get("plot_points_introduced", [])),
            "plots_resolved": len(metadata.get("plot_points_resolved", [])),
            "word_count_target": abs(metadata["word_count"] - 5000) < 1000
        }
        
        # Общая оценка
        style_score = sum(1 for v in style_markers.values() if v) / len(style_markers)
        plot_score = min(1.0, sum(plot_checks.values()) / 5)
        
        return {
            "chapter_number": chapter_number,
            "style_score": style_score,
            "plot_score": plot_score,
            "overall_score": (style_score + plot_score) / 2,
            "style_markers": style_markers,
            "plot_checks": plot_checks,
            "word_count": metadata["word_count"]
        }
    
    def export_book(self, output_path: str, format: str = "txt"):
        """Экспорт сгенерированной книги"""
        if format == "txt":
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("ДВЕРИ КАМНЯ\n")
                f.write("Книга третья из 'Хроник убийцы короля'\n")
                f.write("=" * 50 + "\n\n")
                
                for chapter_num in sorted(self.generated_chapters.keys()):
                    f.write(f"\nГЛАВА {chapter_num}\n")
                    f.write("-" * 30 + "\n\n")
                    f.write(self.generated_chapters[chapter_num])
                    f.write("\n\n")
        
        elif format == "json":
            export_data = {
                "title": "Двери камня",
                "author": "AI в стиле Патрика Ротфусса",
                "generated_by": "Storyteller System",
                "chapters": self.generated_chapters,
                "metadata": self.chapter_metadata,
                "plot_state": self.plot_manager.export_plot_state()
            }
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Книга экспортирована в {output_path}")
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Получение статистики генерации"""
        if not self.current_session:
            return {}
        
        return {
            "session_id": self.current_session.session_id,
            "chapters_generated": len(self.current_session.chapters_generated),
            "total_words": self.current_session.total_words,
            "average_words_per_chapter": (
                self.current_session.total_words / len(self.current_session.chapters_generated)
                if self.current_session.chapters_generated else 0
            ),
            "active_plots": len(self.plot_manager.get_active_plots()),
            "resolved_mysteries": len(self.plot_manager.revealed_secrets),
            "remaining_mysteries": len(self.plot_manager.unresolved_mysteries)
        }