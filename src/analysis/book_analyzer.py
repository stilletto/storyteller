"""
Модуль для глубокого анализа книг серии "Хроники убийцы короля"
Создаёт сжатые представления глав, извлекает персонажей, локации, стиль
"""

import os
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import hashlib

@dataclass
class Character:
    """Представление персонажа"""
    name: str
    aliases: List[str] = field(default_factory=list)
    first_appearance: Optional[str] = None
    description: str = ""
    personality: str = ""
    relationships: Dict[str, str] = field(default_factory=dict)
    key_quotes: List[str] = field(default_factory=list)
    role: str = ""
    story_arc: str = ""
    secrets: List[str] = field(default_factory=list)
    
@dataclass
class Location:
    """Представление локации"""
    name: str
    type: str  # город, таверна, университет и т.д.
    description: str = ""
    significance: str = ""
    first_mention: Optional[str] = None
    associated_characters: List[str] = field(default_factory=list)
    key_events: List[str] = field(default_factory=list)
    atmosphere: str = ""

@dataclass
class ChapterSummary:
    """Краткое содержание главы"""
    book: int
    chapter: int
    title: Optional[str] = None
    narrative_type: str = "inner"  # inner/frame
    pov_character: str = "Квоут"
    
    # Основное содержание
    summary: str = ""
    key_events: List[str] = field(default_factory=list)
    
    # Персонажи и локации
    characters_present: List[str] = field(default_factory=list)
    new_characters: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    
    # Сюжетные элементы
    plot_developments: List[str] = field(default_factory=list)
    mysteries_introduced: List[str] = field(default_factory=list)
    mysteries_resolved: List[str] = field(default_factory=list)
    foreshadowing: List[str] = field(default_factory=list)
    
    # Стилистические элементы
    mood: str = ""
    themes: List[str] = field(default_factory=list)
    notable_quotes: List[str] = field(default_factory=list)
    
    # Важные детали
    magic_used: List[str] = field(default_factory=list)
    items_mentioned: List[str] = field(default_factory=list)
    songs_stories: List[str] = field(default_factory=list)
    
    # Примечания
    notes: str = ""
    timeline_position: Optional[str] = None
    
@dataclass
class StyleProfile:
    """Стилистический профиль текста"""
    # Лексика
    common_words: Dict[str, int] = field(default_factory=dict)
    unique_phrases: List[str] = field(default_factory=list)
    metaphor_patterns: List[str] = field(default_factory=list)
    
    # Структура
    avg_sentence_length: float = 0.0
    sentence_variety: Dict[str, int] = field(default_factory=dict)
    paragraph_patterns: List[str] = field(default_factory=list)
    
    # Диалоги
    dialogue_percentage: float = 0.0
    dialogue_tags: List[str] = field(default_factory=list)
    character_voices: Dict[str, List[str]] = field(default_factory=dict)
    
    # Описания
    description_style: List[str] = field(default_factory=list)
    sensory_details: Dict[str, List[str]] = field(default_factory=dict)
    
    # Особенности
    recurring_motifs: List[str] = field(default_factory=list)
    signature_elements: List[str] = field(default_factory=list)
    narrative_techniques: List[str] = field(default_factory=list)

class BookAnalyzer:
    """Главный класс для анализа книг"""
    
    def __init__(self, api_client=None):
        self.api_client = api_client  # Claude client для генерации summary
        self.characters: Dict[str, Character] = {}
        self.locations: Dict[str, Location] = {}
        self.chapter_summaries: List[ChapterSummary] = []
        self.style_profile = StyleProfile()
        self.timeline: List[Dict[str, Any]] = []
        self.world_state: Dict[str, Any] = {}
        
        # Известные персонажи и их вариации имён
        self.known_characters = {
            "Квоут": ["Квоут", "Коут", "Кровавый", "Бесславный", "Убийца короля", "Шестиструнный"],
            "Денна": ["Денна", "Дианна", "Дайанн", "Алора", "Донна"],
            "Баст": ["Баст", "Басти", "Принц Сумерек"],
            "Симмон": ["Сим", "Симмон", "Симм"],
            "Виллем": ["Вил", "Виллем", "Килвин"],
            "Амброз": ["Амброз", "Якис", "Амброз Якис"],
            "Элодин": ["Мастер Элодин", "Элодин"],
            "Килвин": ["Мастер Килвин", "Килвин"],
            "Хэмм": ["Мастер Хэмм", "Хэмм"],
            "Лорен": ["Мастер Лорен", "Лорен", "Архивариус"],
            "Аури": ["Аури"],
            "Темпи": ["Темпи"],
            "Хроникёр": ["Хроникёр", "Девен", "Девен Лохис"],
            "Фелуриан": ["Фелуриан"],
            "Хэлиакс": ["Хэлиакс", "Лантре", "Алаксель"],
            "Циндер": ["Циндер"],
        }
        
        # Известные локации
        self.known_locations = {
            "Университет": ["здание", "образование"],
            "Архивы": ["библиотека", "знания"],
            "Имре": ["город", "развлечения"],
            "Путеводный камень": ["трактир", "убежище"],
            "Тарбеан": ["город", "нищета"],
            "Винтас": ["королевство", "политика"],
            "Адемре": ["страна", "боевые искусства"],
            "Фейриэл": ["иной мир", "магия"],
            "Элир": ["таверна", "музыка"],
            "Сломанная лестница": ["место", "опасность"],
        }
        
    def analyze_book_files(self, book_dir: str = "book/") -> Dict[str, Any]:
        """Анализирует все файлы книг в директории"""
        results = {
            "total_chapters": 0,
            "characters_found": 0,
            "locations_found": 0,
            "summaries": [],
            "style_analysis": {},
            "timeline": []
        }
        
        # Читаем файлы книг
        book_files = sorted([f for f in os.listdir(book_dir) if f.endswith('.txt')])
        
        for book_file in book_files:
            book_num = int(book_file.split('.')[0]) if book_file[0].isdigit() else 1
            file_path = os.path.join(book_dir, book_file)
            
            print(f"Анализируем книгу {book_num}: {book_file}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Разбиваем на главы (простая эвристика)
            chapters = self._split_into_chapters(text)
            
            for i, chapter_text in enumerate(chapters[:5], 1):  # Анализируем первые 5 глав для теста
                print(f"  Обрабатываем главу {i}...")
                
                # Создаём краткое содержание
                summary = self._create_chapter_summary(book_num, i, chapter_text)
                self.chapter_summaries.append(summary)
                
                # Извлекаем персонажей и локации
                self._extract_characters(chapter_text, f"Книга {book_num}, Глава {i}")
                self._extract_locations(chapter_text, f"Книга {book_num}, Глава {i}")
                
                # Анализируем стиль
                self._analyze_style(chapter_text)
                
                results["total_chapters"] += 1
        
        # Компилируем результаты
        results["characters_found"] = len(self.characters)
        results["locations_found"] = len(self.locations)
        results["summaries"] = [asdict(s) for s in self.chapter_summaries]
        results["style_analysis"] = asdict(self.style_profile)
        results["timeline"] = self.timeline
        
        return results
    
    def _split_into_chapters(self, text: str) -> List[str]:
        """Разбивает текст на главы"""
        # Простая эвристика: делим по размеру
        # В реальности нужно искать маркеры глав
        chunk_size = 50000  # ~10-15 страниц
        chunks = []
        
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i:i+chunk_size])
        
        return chunks
    
    def _create_chapter_summary(self, book: int, chapter: int, text: str) -> ChapterSummary:
        """Создаёт краткое содержание главы"""
        summary = ChapterSummary(book=book, chapter=chapter)
        
        # Определяем тип повествования
        if "трактир" in text[:1000].lower() and "тишина" in text[:1000].lower():
            summary.narrative_type = "frame"
            summary.pov_character = "третье лицо"
        else:
            summary.narrative_type = "inner"
            summary.pov_character = "Квоут"
        
        # Извлекаем ключевую информацию
        summary.characters_present = self._find_characters_in_text(text)
        summary.locations = self._find_locations_in_text(text)
        
        # Определяем настроение
        if "тишина" in text.lower() and "тревога" in text.lower():
            summary.mood = "ominous"
        elif "смех" in text.lower() or "радость" in text.lower():
            summary.mood = "joyful"
        elif "битва" in text.lower() or "сражение" in text.lower():
            summary.mood = "intense"
        else:
            summary.mood = "neutral"
        
        # Ищем упоминания магии
        if "симпатия" in text.lower() or "алар" in text.lower():
            summary.magic_used.append("симпатия")
        if "имя ветра" in text.lower() or "именование" in text.lower():
            summary.magic_used.append("именование")
        
        # Создаём краткое описание (упрощённая версия)
        # В реальной системе здесь будет вызов API для генерации
        sentences = [s.strip() for s in text[:2000].split('.') if len(s.strip()) > 20][:3]
        summary.summary = ". ".join(sentences) + "..."
        
        # Извлекаем ключевые события (простая эвристика)
        action_words = ["встретил", "сказал", "увидел", "почувствовал", "понял", "узнал"]
        for sentence in text.split('.'):
            if any(word in sentence.lower() for word in action_words):
                if len(summary.key_events) < 5:
                    summary.key_events.append(sentence.strip()[:100])
        
        return summary
    
    def _find_characters_in_text(self, text: str) -> List[str]:
        """Находит упоминания персонажей в тексте"""
        found = []
        for main_name, variations in self.known_characters.items():
            for variant in variations:
                if variant in text:
                    if main_name not in found:
                        found.append(main_name)
                    break
        return found
    
    def _find_locations_in_text(self, text: str) -> List[str]:
        """Находит упоминания локаций в тексте"""
        found = []
        for location in self.known_locations.keys():
            if location in text:
                found.append(location)
        return found
    
    def _extract_characters(self, text: str, source: str):
        """Извлекает информацию о персонажах"""
        for main_name, variations in self.known_characters.items():
            for variant in variations:
                if variant in text:
                    if main_name not in self.characters:
                        self.characters[main_name] = Character(
                            name=main_name,
                            aliases=variations,
                            first_appearance=source
                        )
                    
                    # Ищем описания персонажа (упрощённо)
                    context_start = max(0, text.find(variant) - 200)
                    context_end = min(len(text), text.find(variant) + 200)
                    context = text[context_start:context_end]
                    
                    # Добавляем контекст в описание
                    if len(self.characters[main_name].description) < 500:
                        self.characters[main_name].description += context[:100] + "... "
                    
                    break
    
    def _extract_locations(self, text: str, source: str):
        """Извлекает информацию о локациях"""
        for location, (loc_type, significance) in self.known_locations.items():
            if location in text:
                if location not in self.locations:
                    self.locations[location] = Location(
                        name=location,
                        type=loc_type,
                        significance=significance,
                        first_mention=source
                    )
                
                # Ищем описания локации
                context_start = max(0, text.find(location) - 200)
                context_end = min(len(text), text.find(location) + 200)
                context = text[context_start:context_end]
                
                if len(self.locations[location].description) < 500:
                    self.locations[location].description += context[:100] + "... "
    
    def _analyze_style(self, text: str):
        """Анализирует стилистические особенности текста"""
        # Частотность слов
        words = text.lower().split()
        for word in words:
            if len(word) > 4:  # Игнорируем короткие слова
                self.style_profile.common_words[word] = self.style_profile.common_words.get(word, 0) + 1
        
        # Метафоры и сравнения
        if "словно" in text or "как" in text or "будто" in text:
            sentences = text.split('.')
            for sentence in sentences:
                if any(word in sentence for word in ["словно", "как", "будто"]):
                    if len(self.style_profile.metaphor_patterns) < 50:
                        self.style_profile.metaphor_patterns.append(sentence.strip()[:150])
        
        # Фирменные элементы
        if "тишина из трёх частей" in text.lower():
            self.style_profile.signature_elements.append("тишина из трёх частей")
        if "имя ветра" in text.lower():
            self.style_profile.signature_elements.append("магия именования")
        
        # Диалоги
        dialogue_count = text.count('—') + text.count('"')
        total_length = len(text)
        self.style_profile.dialogue_percentage = (dialogue_count * 50) / total_length * 100  # Примерная оценка
        
        # Средняя длина предложений
        sentences = [s for s in text.split('.') if len(s.strip()) > 10]
        if sentences:
            avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
            self.style_profile.avg_sentence_length = avg_length
    
    async def generate_summary_with_ai(self, text: str, chapter_info: Dict) -> str:
        """Генерирует краткое содержание главы с помощью AI"""
        if not self.api_client:
            return "AI клиент не инициализирован"
        
        prompt = f"""Проанализируй эту главу из "Хроник убийцы короля" и создай структурированное краткое содержание.

Глава: {chapter_info.get('book', 1)}.{chapter_info.get('chapter', 1)}

Текст главы (фрагмент):
{text[:5000]}

Создай краткое содержание в следующем формате:
1. ОСНОВНЫЕ СОБЫТИЯ (3-5 пунктов)
2. ПЕРСОНАЖИ (кто появляется, их роль)
3. ЛОКАЦИИ (где происходит действие)
4. РАЗВИТИЕ СЮЖЕТА (что изменилось)
5. ВАЖНЫЕ ДЕТАЛИ (магия, предметы, песни)
6. НАСТРОЕНИЕ И ТЕМЫ
7. ПРИМЕЧАНИЯ (тайны, предзнаменования)

Будь точен и лаконичен. Сохраняй имена и термины из оригинала."""
        
        try:
            from src.ai.claude_client import GenerationConfig
            
            summary = await self.api_client.generate_async(
                system_prompt="Ты эксперт по анализу литературных произведений. Создавай точные и информативные краткие содержания.",
                messages=[{"role": "user", "content": prompt}],
                config=GenerationConfig(max_tokens=2000, temperature=0.3)
            )
            return summary
        except Exception as e:
            return f"Ошибка генерации: {e}"
    
    def export_analysis(self, output_dir: str = "analysis_output/"):
        """Экспортирует результаты анализа"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Экспорт персонажей
        characters_data = {name: asdict(char) for name, char in self.characters.items()}
        with open(os.path.join(output_dir, "characters.json"), 'w', encoding='utf-8') as f:
            json.dump(characters_data, f, ensure_ascii=False, indent=2)
        
        # Экспорт локаций
        locations_data = {name: asdict(loc) for name, loc in self.locations.items()}
        with open(os.path.join(output_dir, "locations.json"), 'w', encoding='utf-8') as f:
            json.dump(locations_data, f, ensure_ascii=False, indent=2)
        
        # Экспорт кратких содержаний
        summaries_data = [asdict(s) for s in self.chapter_summaries]
        with open(os.path.join(output_dir, "chapter_summaries.json"), 'w', encoding='utf-8') as f:
            json.dump(summaries_data, f, ensure_ascii=False, indent=2)
        
        # Экспорт стилистического анализа
        with open(os.path.join(output_dir, "style_profile.json"), 'w', encoding='utf-8') as f:
            json.dump(asdict(self.style_profile), f, ensure_ascii=False, indent=2)
        
        # Создаём сводный отчёт
        report = {
            "analysis_date": datetime.now().isoformat(),
            "total_chapters_analyzed": len(self.chapter_summaries),
            "total_characters": len(self.characters),
            "total_locations": len(self.locations),
            "main_characters": list(self.characters.keys())[:10],
            "main_locations": list(self.locations.keys())[:10],
            "style_highlights": {
                "avg_sentence_length": self.style_profile.avg_sentence_length,
                "dialogue_percentage": self.style_profile.dialogue_percentage,
                "signature_elements": self.style_profile.signature_elements[:5],
                "top_metaphors": self.style_profile.metaphor_patterns[:3]
            }
        }
        
        with open(os.path.join(output_dir, "analysis_report.json"), 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"Анализ экспортирован в {output_dir}")
        return report
    
    def create_story_bible(self) -> Dict[str, Any]:
        """Создаёт 'библию' истории - полный справочник по миру"""
        bible = {
            "world": {
                "name": "Мир Четырёх Углов",
                "magic_systems": ["Симпатия", "Именование", "Сигилдрия", "Алхимия"],
                "major_factions": ["Университет", "Амир", "Чандриане", "Адем"],
                "languages": ["Атуран", "Тема", "Илльен", "Адемский"]
            },
            "timeline": self.timeline,
            "characters": {
                "protagonists": {},
                "antagonists": {},
                "supporting": {},
                "minor": {}
            },
            "locations": {
                "major": {},
                "minor": {}
            },
            "plot_threads": {
                "resolved": [],
                "ongoing": [],
                "foreshadowed": []
            },
            "themes": [
                "Сила историй и их опасность",
                "Цена знания",
                "Природа героизма",
                "Любовь и потеря",
                "Музыка как магия"
            ],
            "mysteries": {
                "major": [
                    "Истинная природа Чандриан",
                    "Содержимое Лэклесского ящика",
                    "Личность покровителя Денны",
                    "Что за Дверями Камня"
                ],
                "minor": []
            }
        }
        
        # Категоризируем персонажей
        for name, char in self.characters.items():
            if name in ["Квоут", "Денна", "Баст"]:
                bible["characters"]["protagonists"][name] = asdict(char)
            elif name in ["Амброз", "Хэлиакс", "Циндер"]:
                bible["characters"]["antagonists"][name] = asdict(char)
            elif name in ["Симмон", "Виллем", "Аури", "Темпи"]:
                bible["characters"]["supporting"][name] = asdict(char)
            else:
                bible["characters"]["minor"][name] = asdict(char)
        
        # Категоризируем локации
        for name, loc in self.locations.items():
            if name in ["Университет", "Путеводный камень", "Имре"]:
                bible["locations"]["major"][name] = asdict(loc)
            else:
                bible["locations"]["minor"][name] = asdict(loc)
        
        return bible