#!/usr/bin/env python3

import asyncio
import click
import json
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from typing import Optional
import os
import sys

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.story_engine import StoryEngine, ChapterConfig
from src.story.plot_manager import PlotManager

console = Console()

class StorytellerCLI:
    def __init__(self):
        self.engine = StoryEngine()
        self.console = console
        
    async def generate_chapter_interactive(self):
        """Интерактивная генерация главы"""
        self.console.print("\n[bold cyan]Генерация новой главы[/bold cyan]\n")
        
        # Запрашиваем параметры
        chapter_number = click.prompt("Номер главы", type=int, default=1)
        narrative_type = click.prompt(
            "Тип повествования (frame/inner)", 
            type=click.Choice(['frame', 'inner']),
            default='frame'
        )
        mood = click.prompt(
            "Настроение главы",
            default="mysterious"
        )
        target_words = click.prompt(
            "Целевое количество слов",
            type=int,
            default=5000
        )
        
        # Показываем доступные сюжетные точки
        self.show_available_plots()
        
        plot_to_introduce = click.prompt(
            "Сюжеты для введения (через запятую, или Enter для пропуска)",
            default=""
        )
        plot_to_resolve = click.prompt(
            "Сюжеты для разрешения (через запятую, или Enter для пропуска)",
            default=""
        )
        
        # Создаём конфигурацию
        config = ChapterConfig(
            chapter_number=chapter_number,
            narrative_type=narrative_type,
            mood=mood,
            target_word_count=target_words,
            plot_points_to_introduce=[p.strip() for p in plot_to_introduce.split(',') if p.strip()],
            plot_points_to_resolve=[p.strip() for p in plot_to_resolve.split(',') if p.strip()]
        )
        
        # Генерируем с прогресс-баром
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task(
                f"[cyan]Генерация главы {chapter_number}...", 
                total=None
            )
            
            try:
                text, metadata = await self.engine.generate_chapter(config)
                progress.update(task, completed=True)
                
                # Показываем результат
                self.console.print("\n[bold green]✓ Глава сгенерирована успешно![/bold green]\n")
                self.show_chapter_preview(text, metadata)
                
                # Предлагаем сохранить
                if click.confirm("Сохранить главу?"):
                    self.save_chapter(chapter_number, text)
                    
            except Exception as e:
                progress.update(task, completed=True)
                self.console.print(f"\n[bold red]✗ Ошибка: {e}[/bold red]\n")
    
    def show_available_plots(self):
        """Показ доступных сюжетных точек"""
        table = Table(title="Доступные сюжетные точки")
        table.add_column("ID", style="cyan")
        table.add_column("Название", style="yellow")
        table.add_column("Статус", style="green")
        table.add_column("Важность", style="magenta")
        
        for plot_id, plot in self.engine.plot_manager.plot_points.items():
            table.add_row(
                plot_id,
                plot.title,
                plot.status.value,
                plot.importance.value
            )
        
        self.console.print(table)
    
    def show_chapter_preview(self, text: str, metadata: dict):
        """Показ превью главы"""
        # Показываем первые 500 символов
        preview = text[:500] + "..." if len(text) > 500 else text
        
        panel = Panel(
            preview,
            title=f"Глава {metadata['chapter_number']} (превью)",
            subtitle=f"{metadata['word_count']} слов"
        )
        self.console.print(panel)
        
        # Показываем метаданные
        info_table = Table(show_header=False)
        info_table.add_column("Параметр", style="cyan")
        info_table.add_column("Значение", style="yellow")
        
        info_table.add_row("Тип повествования", metadata['narrative_type'])
        info_table.add_row("Слов", str(metadata['word_count']))
        if metadata.get('plot_points_introduced'):
            info_table.add_row("Введённые сюжеты", ", ".join(metadata['plot_points_introduced']))
        if metadata.get('plot_points_resolved'):
            info_table.add_row("Разрешённые сюжеты", ", ".join(metadata['plot_points_resolved']))
        
        self.console.print(info_table)
    
    def save_chapter(self, chapter_number: int, text: str):
        """Сохранение главы"""
        os.makedirs("output", exist_ok=True)
        filename = f"output/chapter_{chapter_number:02d}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"ГЛАВА {chapter_number}\n")
            f.write("=" * 50 + "\n\n")
            f.write(text)
        
        self.console.print(f"[green]Сохранено в {filename}[/green]")
    
    async def generate_book_batch(self, num_chapters: int = 5):
        """Пакетная генерация глав"""
        self.console.print(f"\n[bold cyan]Пакетная генерация {num_chapters} глав[/bold cyan]\n")
        
        for i in range(1, num_chapters + 1):
            # Чередуем типы повествования
            narrative_type = "frame" if i % 3 == 1 else "inner"
            
            config = ChapterConfig(
                chapter_number=i,
                narrative_type=narrative_type,
                target_word_count=5000,
                mood="mysterious" if narrative_type == "frame" else "adventurous"
            )
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task(
                    f"[cyan]Генерация главы {i}/{num_chapters}...", 
                    total=None
                )
                
                try:
                    text, metadata = await self.engine.generate_chapter(config)
                    progress.update(task, completed=True)
                    self.save_chapter(i, text)
                    self.console.print(f"[green]✓ Глава {i} готова ({metadata['word_count']} слов)[/green]")
                except Exception as e:
                    progress.update(task, completed=True)
                    self.console.print(f"[red]✗ Ошибка в главе {i}: {e}[/red]")
        
        # Экспортируем книгу
        self.engine.export_book("output/doors_of_stone.txt", format="txt")
        self.console.print("\n[bold green]Книга сохранена в output/doors_of_stone.txt[/bold green]")
    
    def show_stats(self):
        """Показ статистики генерации"""
        stats = self.engine.get_generation_stats()
        
        if not stats:
            self.console.print("[yellow]Нет активной сессии генерации[/yellow]")
            return
        
        table = Table(title="Статистика генерации")
        table.add_column("Параметр", style="cyan")
        table.add_column("Значение", style="yellow")
        
        table.add_row("ID сессии", stats['session_id'])
        table.add_row("Глав сгенерировано", str(stats['chapters_generated']))
        table.add_row("Всего слов", str(stats['total_words']))
        table.add_row("Среднее слов на главу", f"{stats['average_words_per_chapter']:.0f}")
        table.add_row("Активных сюжетов", str(stats['active_plots']))
        table.add_row("Разгаданных тайн", str(stats['resolved_mysteries']))
        table.add_row("Осталось тайн", str(stats['remaining_mysteries']))
        
        self.console.print(table)
    
    def show_plot_progress(self):
        """Показ прогресса сюжетных арок"""
        table = Table(title="Прогресс сюжетных арок")
        table.add_column("Арка", style="cyan")
        table.add_column("Прогресс", style="yellow")
        table.add_column("Фаза", style="green")
        
        for arc_id in self.engine.plot_manager.story_arcs:
            progress = self.engine.plot_manager.get_arc_progress(arc_id)
            if progress:
                table.add_row(
                    progress['arc_name'],
                    f"{progress['progress_percentage']:.0f}% ({progress['resolved']}/{progress['total']})",
                    progress['current_phase']
                )
        
        self.console.print(table)

@click.group()
def cli():
    """Storyteller - Система генерации книги 'Двери камня'"""
    pass

@cli.command()
def generate():
    """Интерактивная генерация главы"""
    cli_app = StorytellerCLI()
    asyncio.run(cli_app.generate_chapter_interactive())

@cli.command()
@click.option('--chapters', '-n', default=5, help='Количество глав для генерации')
def batch(chapters):
    """Пакетная генерация глав"""
    cli_app = StorytellerCLI()
    asyncio.run(cli_app.generate_book_batch(chapters))

@cli.command()
def stats():
    """Показать статистику генерации"""
    cli_app = StorytellerCLI()
    cli_app.show_stats()

@cli.command()
def plots():
    """Показать прогресс сюжетных линий"""
    cli_app = StorytellerCLI()
    cli_app.show_plot_progress()

@cli.command()
def demo():
    """Демонстрация генерации фрагмента"""
    async def run_demo():
        cli_app = StorytellerCLI()
        console.print("\n[bold cyan]Демонстрация генерации фрагмента 'Дверей камня'[/bold cyan]\n")
        
        # Генерируем начало книги
        config = ChapterConfig(
            chapter_number=1,
            narrative_type="frame",
            target_word_count=1000,
            mood="mysterious",
            plot_points_to_introduce=["skin_dancers"]
        )
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Генерация демо-фрагмента...", total=None)
            
            try:
                text, metadata = await cli_app.engine.generate_chapter(config)
                progress.update(task, completed=True)
                
                # Показываем полный текст демо
                panel = Panel(
                    text,
                    title="Демо-фрагмент: Начало 'Дверей камня'",
                    subtitle=f"{metadata['word_count']} слов"
                )
                console.print(panel)
                
                # Сохраняем
                cli_app.save_chapter(1, text)
                console.print("\n[green]Демо-фрагмент сохранён в output/chapter_01.txt[/green]")
                
            except Exception as e:
                progress.update(task, completed=True)
                console.print(f"\n[red]Ошибка: {e}[/red]")
    
    asyncio.run(run_demo())

if __name__ == "__main__":
    # Создаём необходимые директории
    os.makedirs("output", exist_ok=True)
    os.makedirs("sessions", exist_ok=True)
    
    # Показываем приветствие
    console.print(Panel.fit(
        "[bold cyan]Storyteller[/bold cyan]\n"
        "Система генерации третьей книги 'Хроник убийцы короля'\n"
        "[dim]'Двери камня' в стиле Патрика Ротфусса[/dim]",
        border_style="cyan"
    ))
    
    cli()