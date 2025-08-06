#!/usr/bin/env python3

import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.story_engine import StoryEngine, ChapterConfig
from src.ai.claude_client import GenerationConfig
from rich.console import Console
from rich.panel import Panel

console = Console()

async def test_generation():
    """Тестовая генерация начального фрагмента 'Дверей камня'"""
    
    console.print(Panel.fit(
        "[bold cyan]Тест системы Storyteller[/bold cyan]\n"
        "Генерация начального фрагмента третьей книги",
        border_style="cyan"
    ))
    
    # Инициализация
    engine = StoryEngine()
    session_id = engine.start_session()
    console.print(f"\n[green]Сессия начата:[/green] {session_id}\n")
    
    # Конфигурация для первой главы (рамочное повествование)
    config_frame = ChapterConfig(
        chapter_number=1,
        narrative_type="frame",
        target_word_count=800,  # Короткий фрагмент для теста
        mood="ominous",
        time_of_day="night",
        plot_points_to_introduce=["skin_dancers"],
        key_scenes=["Тишина в трактире", "Коут за барной стойкой", "Баст беспокоится"]
    )
    
    try:
        console.print("[yellow]Генерация рамочного повествования...[/yellow]")
        text_frame, metadata_frame = await engine.generate_chapter(config_frame)
        
        console.print("\n[bold green]✓ Рамочное повествование сгенерировано![/bold green]")
        console.print(Panel(
            text_frame[:1000] + "..." if len(text_frame) > 1000 else text_frame,
            title="Глава 1: Рамочное повествование",
            subtitle=f"{metadata_frame['word_count']} слов"
        ))
        
        # Сохраняем
        os.makedirs("output", exist_ok=True)
        with open("output/test_chapter_01_frame.txt", "w", encoding="utf-8") as f:
            f.write(text_frame)
        
        # Конфигурация для второй главы (внутреннее повествование)
        config_inner = ChapterConfig(
            chapter_number=2,
            narrative_type="inner",
            target_word_count=800,
            mood="reflective",
            key_scenes=["Квоут начинает рассказ", "Воспоминание о Денне"]
        )
        
        console.print("\n[yellow]Генерация внутреннего повествования...[/yellow]")
        text_inner, metadata_inner = await engine.generate_chapter(config_inner)
        
        console.print("\n[bold green]✓ Внутреннее повествование сгенерировано![/bold green]")
        console.print(Panel(
            text_inner[:1000] + "..." if len(text_inner) > 1000 else text_inner,
            title="Глава 2: История Квоута",
            subtitle=f"{metadata_inner['word_count']} слов"
        ))
        
        # Сохраняем
        with open("output/test_chapter_02_inner.txt", "w", encoding="utf-8") as f:
            f.write(text_inner)
        
        # Показываем статистику
        stats = engine.get_generation_stats()
        console.print("\n[cyan]Статистика генерации:[/cyan]")
        console.print(f"• Глав сгенерировано: {stats['chapters_generated']}")
        console.print(f"• Всего слов: {stats['total_words']}")
        console.print(f"• Активных сюжетов: {stats['active_plots']}")
        
        # Экспортируем в единый файл
        engine.export_book("output/test_book.txt", format="txt")
        console.print("\n[green]✓ Тестовая книга сохранена в output/test_book.txt[/green]")
        
    except Exception as e:
        console.print(f"\n[bold red]✗ Ошибка при генерации: {e}[/bold red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")

async def test_simple_generation():
    """Простой тест генерации одного фрагмента"""
    from src.ai.claude_client import ClaudeNeptuneClient
    from src.templates.prompts import RothfussPrompts
    
    console.print("\n[cyan]Простой тест API...[/cyan]")
    
    client = ClaudeNeptuneClient()
    prompts = RothfussPrompts()
    
    # Простейший запрос
    system_prompt = prompts.get_system_prompt_base()
    user_prompt = """Напиши начало главы 'Дверей камня' в стиле Патрика Ротфусса.
    Начни с описания тишины из трёх частей в трактире 'Путеводный камень'.
    Примерно 200 слов."""
    
    try:
        result = client.generate(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            config=GenerationConfig(max_tokens=2000, temperature=0.9)
        )
        
        console.print("\n[green]✓ API работает![/green]")
        console.print(Panel(result, title="Сгенерированный фрагмент"))
        
        return True
        
    except Exception as e:
        console.print(f"\n[red]✗ Ошибка API: {e}[/red]")
        return False

async def main():
    """Основная функция тестирования"""
    
    # Сначала простой тест
    console.print("[bold]Тестирование системы Storyteller[/bold]\n")
    
    if await test_simple_generation():
        console.print("\n[cyan]Переходим к полному тесту...[/cyan]\n")
        await test_generation()
    else:
        console.print("\n[red]Базовый тест не пройден. Проверьте настройки API.[/red]")

if __name__ == "__main__":
    asyncio.run(main())