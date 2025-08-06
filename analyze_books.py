#!/usr/bin/env python3
"""
Скрипт для анализа книг серии "Хроники убийцы короля"
Создаёт базу знаний для системы генерации
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.analysis.book_analyzer import BookAnalyzer
from src.ai.claude_client import ClaudeNeptuneClient

console = Console()

async def run_analysis():
    """Запускает полный анализ книг"""
    console.print(Panel.fit(
        "[bold cyan]Анализатор книг 'Хроники убийцы короля'[/bold cyan]\n"
        "Создание базы знаний для генерации третьей книги",
        border_style="cyan"
    ))
    
    # Инициализация
    try:
        client = ClaudeNeptuneClient()
        console.print("[green]✓ AI клиент инициализирован[/green]")
    except Exception as e:
        console.print(f"[yellow]⚠ AI клиент недоступен: {e}[/yellow]")
        client = None
    
    analyzer = BookAnalyzer(api_client=client)
    
    # Запуск анализа
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Анализируем тексты книг...", total=None)
        
        try:
            results = analyzer.analyze_book_files("book/")
            progress.update(task, completed=True)
            
            console.print(f"\n[green]✓ Анализ завершён![/green]")
            
            # Показываем результаты
            show_results(results, analyzer)
            
            # Экспортируем результаты
            progress.add_task("[cyan]Экспортируем результаты...", total=None)
            report = analyzer.export_analysis()
            
            # Создаём библию истории
            bible = analyzer.create_story_bible()
            with open("analysis_output/story_bible.json", 'w', encoding='utf-8') as f:
                json.dump(bible, f, ensure_ascii=False, indent=2)
            
            console.print("\n[green]✓ Результаты сохранены в analysis_output/[/green]")
            
            return results, bible
            
        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"\n[red]✗ Ошибка при анализе: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
            return None, None

def show_results(results: dict, analyzer: BookAnalyzer):
    """Показывает результаты анализа"""
    
    # Общая статистика
    stats_table = Table(title="Статистика анализа")
    stats_table.add_column("Параметр", style="cyan")
    stats_table.add_column("Значение", style="yellow")
    
    stats_table.add_row("Проанализировано глав", str(results["total_chapters"]))
    stats_table.add_row("Найдено персонажей", str(results["characters_found"]))
    stats_table.add_row("Найдено локаций", str(results["locations_found"]))
    
    console.print("\n", stats_table)
    
    # Главные персонажи
    if analyzer.characters:
        char_table = Table(title="Основные персонажи")
        char_table.add_column("Имя", style="cyan")
        char_table.add_column("Псевдонимы", style="yellow")
        char_table.add_column("Первое появление", style="green")
        
        for name, char in list(analyzer.characters.items())[:10]:
            aliases = ", ".join(char.aliases[:3]) if char.aliases else "-"
            char_table.add_row(name, aliases, char.first_appearance or "-")
        
        console.print("\n", char_table)
    
    # Главные локации
    if analyzer.locations:
        loc_table = Table(title="Основные локации")
        loc_table.add_column("Название", style="cyan")
        loc_table.add_column("Тип", style="yellow")
        loc_table.add_column("Значимость", style="green")
        
        for name, loc in list(analyzer.locations.items())[:10]:
            loc_table.add_row(name, loc.type, loc.significance[:30] + "...")
        
        console.print("\n", loc_table)
    
    # Стилистический анализ
    if analyzer.style_profile.signature_elements:
        console.print("\n[bold cyan]Фирменные элементы стиля:[/bold cyan]")
        for element in analyzer.style_profile.signature_elements[:5]:
            console.print(f"  • {element}")
    
    if analyzer.style_profile.metaphor_patterns:
        console.print("\n[bold cyan]Примеры метафор:[/bold cyan]")
        for metaphor in analyzer.style_profile.metaphor_patterns[:3]:
            console.print(f"  • {metaphor[:100]}...")
    
    # Краткие содержания
    if analyzer.chapter_summaries:
        console.print(f"\n[bold cyan]Создано кратких содержаний: {len(analyzer.chapter_summaries)}[/bold cyan]")
        
        # Показываем пример
        sample = analyzer.chapter_summaries[0]
        panel = Panel(
            f"Книга {sample.book}, Глава {sample.chapter}\n"
            f"Тип: {sample.narrative_type}\n"
            f"Настроение: {sample.mood}\n"
            f"Персонажи: {', '.join(sample.characters_present[:5])}\n"
            f"Локации: {', '.join(sample.locations[:3])}\n"
            f"Краткое содержание: {sample.summary[:200]}...",
            title="Пример краткого содержания"
        )
        console.print("\n", panel)

def create_enhanced_context():
    """Создаёт улучшенный контекст для генерации"""
    console.print("\n[bold cyan]Создание улучшенного контекста...[/bold cyan]")
    
    # Загружаем результаты анализа
    try:
        with open("analysis_output/story_bible.json", 'r', encoding='utf-8') as f:
            bible = json.load(f)
        
        with open("analysis_output/chapter_summaries.json", 'r', encoding='utf-8') as f:
            summaries = json.load(f)
        
        # Создаём компактный контекст для промптов
        context = {
            "world_info": bible["world"],
            "main_characters": list(bible["characters"]["protagonists"].keys()),
            "main_locations": list(bible["locations"]["major"].keys()),
            "ongoing_mysteries": bible["mysteries"]["major"],
            "themes": bible["themes"],
            "last_events": [s["summary"] for s in summaries[-3:]] if len(summaries) > 3 else [],
            "style_notes": {
                "signature_elements": ["тишина из трёх частей", "музыкальные метафоры"],
                "narrative_types": ["frame (третье лицо)", "inner (первое лицо от Квоута)"],
                "magic_systems": ["симпатия (научная)", "именование (мистическое)"]
            }
        }
        
        # Сохраняем компактный контекст
        with open("analysis_output/generation_context.json", 'w', encoding='utf-8') as f:
            json.dump(context, f, ensure_ascii=False, indent=2)
        
        console.print("[green]✓ Контекст для генерации создан[/green]")
        
        # Показываем размер контекста
        context_str = json.dumps(context, ensure_ascii=False)
        console.print(f"[yellow]Размер контекста: {len(context_str)} символов[/yellow]")
        
        return context
        
    except Exception as e:
        console.print(f"[red]✗ Ошибка создания контекста: {e}[/red]")
        return None

def integrate_with_story_engine():
    """Интегрирует результаты анализа с основной системой"""
    console.print("\n[bold cyan]Интеграция с системой генерации...[/bold cyan]")
    
    # Обновляем StoryEngine для использования контекста
    integration_code = '''
# Добавить в src/core/story_engine.py

def load_story_bible(self, bible_path: str = "analysis_output/story_bible.json"):
    """Загружает базу знаний о мире"""
    with open(bible_path, 'r', encoding='utf-8') as f:
        self.story_bible = json.load(f)
    
    # Обновляем персонажей
    for char_name, char_data in self.story_bible["characters"]["protagonists"].items():
        if char_name in self.characters:
            self.characters[char_name].description = char_data.get("description", "")
            self.characters[char_name].relationships = char_data.get("relationships", {})

def load_chapter_summaries(self, summaries_path: str = "analysis_output/chapter_summaries.json"):
    """Загружает краткие содержания предыдущих глав"""
    with open(summaries_path, 'r', encoding='utf-8') as f:
        self.previous_chapters = json.load(f)
    
    # Используем для контекста
    self.context_window = [s["summary"] for s in self.previous_chapters[-5:]]
'''
    
    console.print("[yellow]Код интеграции:[/yellow]")
    console.print(Panel(integration_code, title="Добавить в StoryEngine"))
    
    # Создаём улучшенные промпты
    enhanced_prompts = '''
# Улучшенные промпты с контекстом

def get_context_aware_prompt(self, chapter_config):
    """Создаёт промпт с полным контекстом мира"""
    
    context = {
        "previous_events": self.previous_chapters[-3:],
        "active_characters": self.story_bible["characters"],
        "current_location": chapter_config.location,
        "unresolved_mysteries": self.story_bible["mysteries"]["major"]
    }
    
    prompt = f"""
    Ты пишешь главу {chapter_config.chapter_number} книги "Двери камня".
    
    КОНТЕКСТ МИРА:
    {json.dumps(self.story_bible["world"], ensure_ascii=False)}
    
    ПРЕДЫДУЩИЕ СОБЫТИЯ:
    {json.dumps(context["previous_events"], ensure_ascii=False)}
    
    АКТИВНЫЕ ТАЙНЫ:
    {json.dumps(context["unresolved_mysteries"], ensure_ascii=False)}
    
    Продолжай историю, учитывая весь контекст.
    """
    
    return prompt
'''
    
    console.print("\n[yellow]Улучшенные промпты:[/yellow]")
    console.print(Panel(enhanced_prompts, title="Контекстно-зависимые промпты"))
    
    console.print("\n[green]✓ Инструкции по интеграции созданы[/green]")

async def main():
    """Главная функция"""
    # Запускаем анализ
    results, bible = await run_analysis()
    
    if results:
        # Создаём улучшенный контекст
        context = create_enhanced_context()
        
        # Показываем инструкции по интеграции
        integrate_with_story_engine()
        
        console.print("\n[bold green]Анализ завершён успешно![/bold green]")
        console.print("Теперь система может использовать:")
        console.print("• Базу персонажей и локаций")
        console.print("• Краткие содержания глав")
        console.print("• Стилистические паттерны")
        console.print("• Хронологию событий")
        console.print("• Библию мира")
        
        # Показываем итоговую статистику
        stats_panel = Panel(
            f"Персонажей: {len(bible['characters']['protagonists']) + len(bible['characters']['antagonists']) + len(bible['characters']['supporting'])}\n"
            f"Локаций: {len(bible['locations']['major']) + len(bible['locations']['minor'])}\n"
            f"Тайн: {len(bible['mysteries']['major'])}\n"
            f"Тем: {len(bible['themes'])}",
            title="База знаний создана"
        )
        console.print("\n", stats_panel)

if __name__ == "__main__":
    asyncio.run(main())