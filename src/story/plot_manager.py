from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

class PlotStatus(Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    RESOLVED = "resolved"
    ABANDONED = "abandoned"
    BACKGROUND = "background"

class PlotImportance(Enum):
    CRITICAL = "critical"  # Основная сюжетная линия
    MAJOR = "major"        # Важные подсюжеты
    MINOR = "minor"        # Второстепенные линии
    FLAVOR = "flavor"      # Атмосферные детали

@dataclass
class PlotPoint:
    id: str
    title: str
    description: str
    importance: PlotImportance
    status: PlotStatus
    chapter_introduced: Optional[int] = None
    chapter_resolved: Optional[int] = None
    dependencies: List[str] = field(default_factory=list)
    consequences: List[str] = field(default_factory=list)
    characters_involved: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    foreshadowing: List[str] = field(default_factory=list)
    revelations: List[str] = field(default_factory=list)
    notes: str = ""

@dataclass
class StoryArc:
    id: str
    name: str
    description: str
    plot_points: List[str] = field(default_factory=list)
    start_chapter: Optional[int] = None
    end_chapter: Optional[int] = None
    climax_chapter: Optional[int] = None
    themes: List[str] = field(default_factory=list)
    emotional_journey: Dict[str, str] = field(default_factory=dict)

@dataclass
class Timeline:
    frame_narrative: List[Dict[str, Any]] = field(default_factory=list)
    inner_narrative: List[Dict[str, Any]] = field(default_factory=list)
    synchronization_points: List[Dict[str, Any]] = field(default_factory=list)

class PlotManager:
    def __init__(self):
        self.plot_points: Dict[str, PlotPoint] = {}
        self.story_arcs: Dict[str, StoryArc] = {}
        self.timeline = Timeline()
        self.current_chapter = 1
        self.unresolved_mysteries: Set[str] = set()
        self.revealed_secrets: Set[str] = set()
        self._initialize_book_three_plots()
    
    def _initialize_book_three_plots(self):
        """Инициализация основных сюжетных линий для 'Дверей камня'"""
        
        # Критические сюжетные точки
        critical_plots = [
            PlotPoint(
                id="king_killing",
                title="Убийство короля",
                description="Как и почему Квоут убил короля",
                importance=PlotImportance.CRITICAL,
                status=PlotStatus.PLANNED,
                characters_involved=["Квоут", "Король Винтаса"],
                revelations=["Истинная причина убийства", "Последствия для мира"]
            ),
            PlotPoint(
                id="chandrian_confrontation",
                title="Финальная встреча с Чандрианами",
                description="Квоут наконец встречается с убийцами своей семьи",
                importance=PlotImportance.CRITICAL,
                status=PlotStatus.PLANNED,
                characters_involved=["Квоут", "Хэлиакс", "Циндер"],
                dependencies=["amyr_truth", "denna_secret"]
            ),
            PlotPoint(
                id="doors_of_stone",
                title="Тайна Дверей Камня",
                description="Что скрывается за Дверями Камня",
                importance=PlotImportance.CRITICAL,
                status=PlotStatus.PLANNED,
                revelations=["Природа Дверей", "Связь с Иаксом", "Ключ к победе"]
            ),
            PlotPoint(
                id="kvothe_transformation",
                title="Превращение Квоута в Коута",
                description="Как легендарный герой стал сломленным трактирщиком",
                importance=PlotImportance.CRITICAL,
                status=PlotStatus.PLANNED,
                consequences=["Потеря магии", "Изменение имени", "Самоизгнание"]
            ),
            PlotPoint(
                id="denna_revelation",
                title="Правда о Денне",
                description="Раскрытие тайны Денны и её покровителя",
                importance=PlotImportance.CRITICAL,
                status=PlotStatus.PLANNED,
                characters_involved=["Квоут", "Денна", "Мастер Эш"],
                revelations=["Личность Мастера Эша", "Истинные цели Денны"]
            )
        ]
        
        # Основные сюжетные арки
        main_arcs = [
            StoryArc(
                id="return_of_power",
                name="Возвращение силы",
                description="Коут постепенно возвращает свои способности",
                themes=["Идентичность", "Искупление", "Принятие прошлого"],
                emotional_journey={
                    "начало": "отрицание",
                    "середина": "борьба",
                    "конец": "принятие"
                }
            ),
            StoryArc(
                id="chandrian_hunt",
                name="Охота на Чандриан",
                description="Поиски и финальная конфронтация с Чандрианами",
                themes=["Месть", "Справедливость", "Цена мести"],
                plot_points=["chandrian_confrontation", "amyr_truth"]
            ),
            StoryArc(
                id="love_tragedy",
                name="Трагедия любви",
                description="Финал отношений Квоута и Денны",
                themes=["Любовь", "Предательство", "Прощение"],
                plot_points=["denna_revelation", "denna_choice"]
            ),
            StoryArc(
                id="legend_vs_man",
                name="Легенда против человека",
                description="Конфликт между Квоутом-легендой и Коутом-человеком",
                themes=["Идентичность", "Слава", "Человечность"],
                plot_points=["kvothe_transformation", "final_choice"]
            )
        ]
        
        # Добавляем в менеджер
        for plot in critical_plots:
            self.add_plot_point(plot)
        
        for arc in main_arcs:
            self.add_story_arc(arc)
        
        # Инициализируем неразрешенные тайны из первых двух книг
        self.unresolved_mysteries = {
            "lackless_box",
            "amyr_purpose",
            "chandrian_curse",
            "cthaeh_prophecy",
            "auri_nature",
            "bast_plans",
            "skin_dancers",
            "scrael_origin",
            "waystone_significance"
        }
    
    def add_plot_point(self, plot_point: PlotPoint):
        """Добавление новой сюжетной точки"""
        self.plot_points[plot_point.id] = plot_point
        if plot_point.status == PlotStatus.ACTIVE:
            self.unresolved_mysteries.add(plot_point.id)
    
    def add_story_arc(self, arc: StoryArc):
        """Добавление сюжетной арки"""
        self.story_arcs[arc.id] = arc
    
    def resolve_plot_point(self, plot_id: str, resolution: str, chapter: int):
        """Разрешение сюжетной точки"""
        if plot_id in self.plot_points:
            plot = self.plot_points[plot_id]
            plot.status = PlotStatus.RESOLVED
            plot.chapter_resolved = chapter
            plot.notes += f"\nРазрешено в главе {chapter}: {resolution}"
            
            if plot_id in self.unresolved_mysteries:
                self.unresolved_mysteries.remove(plot_id)
                self.revealed_secrets.add(plot_id)
            
            # Активируем зависимые сюжеты
            for other_plot in self.plot_points.values():
                if plot_id in other_plot.dependencies:
                    if other_plot.status == PlotStatus.PLANNED:
                        other_plot.status = PlotStatus.ACTIVE
                        self.unresolved_mysteries.add(other_plot.id)
    
    def introduce_plot_point(self, plot_id: str, chapter: int):
        """Введение сюжетной точки в повествование"""
        if plot_id in self.plot_points:
            plot = self.plot_points[plot_id]
            plot.chapter_introduced = chapter
            if plot.status == PlotStatus.PLANNED:
                plot.status = PlotStatus.ACTIVE
                self.unresolved_mysteries.add(plot_id)
    
    def get_active_plots(self) -> List[PlotPoint]:
        """Получение активных сюжетных линий"""
        return [p for p in self.plot_points.values() 
                if p.status == PlotStatus.ACTIVE]
    
    def get_plots_for_chapter(self, chapter: int) -> Dict[str, List[PlotPoint]]:
        """Получение сюжетных точек для конкретной главы"""
        return {
            "introduce": [p for p in self.plot_points.values() 
                         if p.chapter_introduced == chapter],
            "resolve": [p for p in self.plot_points.values() 
                       if p.chapter_resolved == chapter],
            "active": [p for p in self.plot_points.values() 
                      if p.status == PlotStatus.ACTIVE and 
                      p.chapter_introduced and 
                      p.chapter_introduced <= chapter and
                      (not p.chapter_resolved or p.chapter_resolved > chapter)]
        }
    
    def check_dependencies(self, plot_id: str) -> bool:
        """Проверка, готов ли сюжет к активации"""
        if plot_id not in self.plot_points:
            return False
        
        plot = self.plot_points[plot_id]
        for dep_id in plot.dependencies:
            if dep_id in self.plot_points:
                dep_plot = self.plot_points[dep_id]
                if dep_plot.status != PlotStatus.RESOLVED:
                    return False
        return True
    
    def add_foreshadowing(self, plot_id: str, hint: str, chapter: int):
        """Добавление предзнаменования"""
        if plot_id in self.plot_points:
            self.plot_points[plot_id].foreshadowing.append(
                f"Глава {chapter}: {hint}"
            )
    
    def synchronize_timelines(self, chapter: int, frame_event: str, inner_event: str):
        """Синхронизация событий между временными линиями"""
        sync_point = {
            "chapter": chapter,
            "frame_narrative": frame_event,
            "inner_narrative": inner_event,
            "timestamp": datetime.now().isoformat()
        }
        self.timeline.synchronization_points.append(sync_point)
    
    def get_arc_progress(self, arc_id: str) -> Dict[str, Any]:
        """Получение прогресса сюжетной арки"""
        if arc_id not in self.story_arcs:
            return {}
        
        arc = self.story_arcs[arc_id]
        total_plots = len(arc.plot_points)
        resolved_plots = sum(1 for pid in arc.plot_points 
                           if pid in self.plot_points and 
                           self.plot_points[pid].status == PlotStatus.RESOLVED)
        
        return {
            "arc_name": arc.name,
            "progress_percentage": (resolved_plots / total_plots * 100) if total_plots > 0 else 0,
            "resolved": resolved_plots,
            "total": total_plots,
            "current_phase": self._determine_arc_phase(arc, resolved_plots, total_plots)
        }
    
    def _determine_arc_phase(self, arc: StoryArc, resolved: int, total: int) -> str:
        """Определение текущей фазы сюжетной арки"""
        if total == 0:
            return "не начата"
        
        progress = resolved / total
        if progress == 0:
            return "экспозиция"
        elif progress < 0.3:
            return "развитие"
        elif progress < 0.6:
            return "усложнение"
        elif progress < 0.8:
            return "кульминация"
        elif progress < 1.0:
            return "развязка"
        else:
            return "завершена"
    
    def suggest_next_plot_development(self) -> Dict[str, Any]:
        """Предложение следующего развития сюжета"""
        suggestions = {
            "immediate": [],  # Что нужно разрешить срочно
            "ready": [],      # Готовые к введению
            "building": []    # Требуют подготовки
        }
        
        # Ищем перегруженные активные сюжеты
        active_critical = [p for p in self.get_active_plots() 
                          if p.importance == PlotImportance.CRITICAL]
        if len(active_critical) > 3:
            suggestions["immediate"] = active_critical[:2]
        
        # Ищем готовые к активации
        for plot_id, plot in self.plot_points.items():
            if plot.status == PlotStatus.PLANNED and self.check_dependencies(plot_id):
                suggestions["ready"].append(plot)
        
        # Ищем требующие подготовки
        for plot in self.plot_points.values():
            if plot.status == PlotStatus.PLANNED and plot.dependencies:
                unresolved_deps = [d for d in plot.dependencies 
                                 if d not in self.revealed_secrets]
                if unresolved_deps:
                    suggestions["building"].append({
                        "plot": plot,
                        "needs": unresolved_deps
                    })
        
        return suggestions
    
    def export_plot_state(self) -> str:
        """Экспорт состояния сюжета в JSON"""
        state = {
            "current_chapter": self.current_chapter,
            "plot_points": {pid: {
                "title": p.title,
                "status": p.status.value,
                "importance": p.importance.value,
                "introduced": p.chapter_introduced,
                "resolved": p.chapter_resolved
            } for pid, p in self.plot_points.items()},
            "story_arcs": {aid: {
                "name": a.name,
                "progress": self.get_arc_progress(aid)
            } for aid, a in self.story_arcs.items()},
            "unresolved_mysteries": list(self.unresolved_mysteries),
            "revealed_secrets": list(self.revealed_secrets)
        }
        return json.dumps(state, ensure_ascii=False, indent=2)