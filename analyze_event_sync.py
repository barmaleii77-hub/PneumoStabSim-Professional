"""
Analyze Python↔QML event synchronization
Reads events JSON and generates detailed sync report
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def load_latest_events(logs_dir: Path | str = "logs") -> Dict[str, Any]:
    """Загружает последний файл событий"""
    logs_dir = Path(logs_dir)
    
    if not logs_dir.exists():
        print(f"❌ Директория логов не найдена: {logs_dir}")
        return {}
    
    # Находим последний файл events_*.json
    event_files = sorted(logs_dir.glob("events_*.json"), reverse=True)
    
    if not event_files:
        print(f"❌ Файлы событий не найдены в: {logs_dir}")
        return {}
    
    latest_file = event_files[0]
    print(f"📁 Загружаем: {latest_file.name}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def analyze_event_pairs(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Анализ пар Python→QML событий"""
    pairs = []
    
    for i, event in enumerate(events):
        if event["event_type"] != "SIGNAL_EMIT":
            continue
        
        signal_name = event["action"].replace("emit_", "")
        emit_time = datetime.fromisoformat(event["timestamp"])
        
        # Ищем соответствующий SIGNAL_RECEIVED в QML
        found = False
        for j in range(i+1, min(i+100, len(events))):  # Ищем в следующих 100 событиях
            next_event = events[j]
            recv_time = datetime.fromisoformat(next_event["timestamp"])
            
            if (recv_time - emit_time).total_seconds() > 1.0:
                break  # Слишком поздно
            
            if (next_event["event_type"] == "SIGNAL_RECEIVED" and
                signal_name.lower() in next_event["action"].lower()):
                
                latency_ms = (recv_time - emit_time).total_seconds() * 1000
                pairs.append({
                    "python_event": event,
                    "qml_event": next_event,
                    "latency_ms": latency_ms,
                    "status": "synced"
                })
                found = True
                break
        
        if not found:
            pairs.append({
                "python_event": event,
                "qml_event": None,
                "latency_ms": None,
                "status": "missing_qml"
            })
    
    return {
        "pairs": pairs,
        "total": len(pairs),
        "synced": sum(1 for p in pairs if p["status"] == "synced"),
        "missing": sum(1 for p in pairs if p["status"] == "missing_qml")
    }


def analyze_by_category(events: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """Группировка событий по категориям"""
    categories = {}
    
    for event in events:
        component = event.get("component", "unknown")
        
        if component not in categories:
            categories[component] = {
                "total": 0,
                "user_clicks": 0,
                "user_sliders": 0,  # ✅ НОВОЕ
                "user_combos": 0,   # ✅ НОВОЕ
                "user_colors": 0,   # ✅ НОВОЕ
                "state_changes": 0,
                "signals_emit": 0,
                "signals_received": 0,
                "functions_called": 0,
                "properties_changed": 0,
                "mouse_press": 0,      # ✅ НОВОЕ
                "mouse_drag": 0,       # ✅ НОВОЕ
                "mouse_wheel": 0,      # ✅ НОВОЕ
                "mouse_release": 0     # ✅ НОВОЕ
            }
        
        categories[component]["total"] += 1
        
        event_type = event["event_type"]
        if event_type == "USER_CLICK":
            categories[component]["user_clicks"] += 1
        elif event_type == "USER_SLIDER":
            categories[component]["user_sliders"] += 1
        elif event_type == "USER_COMBO":
            categories[component]["user_combos"] += 1
        elif event_type == "USER_COLOR":
            categories[component]["user_colors"] += 1
        elif event_type == "STATE_CHANGE":
            categories[component]["state_changes"] += 1
        elif event_type == "SIGNAL_EMIT":
            categories[component]["signals_emit"] += 1
        elif event_type == "SIGNAL_RECEIVED":
            categories[component]["signals_received"] += 1
        elif event_type == "FUNCTION_CALLED":
            categories[component]["functions_called"] += 1
        elif event_type == "PROPERTY_CHANGED":
            categories[component]["properties_changed"] += 1
        elif event_type == "MOUSE_PRESS":
            categories[component]["mouse_press"] += 1
        elif event_type == "MOUSE_DRAG":
            categories[component]["mouse_drag"] += 1
        elif event_type == "MOUSE_WHEEL":
            categories[component]["mouse_wheel"] += 1
        elif event_type == "MOUSE_RELEASE":
            categories[component]["mouse_release"] += 1
    
    return categories


def find_slow_updates(pairs: List[Dict[str, Any]], threshold_ms: float = 50.0) -> List[Dict[str, Any]]:
    """Находит медленные обновления (задержка > threshold)"""
    slow = []
    
    for pair in pairs:
        if pair["status"] == "synced" and pair["latency_ms"] > threshold_ms:
            slow.append({
                "signal": pair["python_event"]["action"],
                "latency_ms": pair["latency_ms"],
                "timestamp": pair["python_event"]["timestamp"]
            })
    
    return sorted(slow, key=lambda x: x["latency_ms"], reverse=True)


def print_analysis_report(events: List[Dict[str, Any]]) -> None:
    """Печать детального отчета"""
    print("\n" + "="*60)
    print("📊 АНАЛИЗ СОБЫТИЙ Python↔QML")
    print("="*60)
    
    if not events:
        print("❌ Нет событий для анализа")
        return
    
    # Общая статистика
    total_events = len(events)
    user_clicks = sum(1 for e in events if e["event_type"] == "USER_CLICK")
    user_sliders = sum(1 for e in events if e["event_type"] == "USER_SLIDER")
    user_combos = sum(1 for e in events if e["event_type"] == "USER_COMBO")
    user_colors = sum(1 for e in events if e["event_type"] == "USER_COLOR")
    state_changes = sum(1 for e in events if e["event_type"] == "STATE_CHANGE")
    signals_emit = sum(1 for e in events if e["event_type"] == "SIGNAL_EMIT")
    signals_received = sum(1 for e in events if e["event_type"] == "SIGNAL_RECEIVED")
    functions_called = sum(1 for e in events if e["event_type"] == "FUNCTION_CALLED")
    properties_changed = sum(1 for e in events if e["event_type"] == "PROPERTY_CHANGED")
    mouse_press = sum(1 for e in events if e["event_type"] == "MOUSE_PRESS")
    mouse_drag = sum(1 for e in events if e["event_type"] == "MOUSE_DRAG")
    mouse_wheel = sum(1 for e in events if e["event_type"] == "MOUSE_WHEEL")
    mouse_release = sum(1 for e in events if e["event_type"] == "MOUSE_RELEASE")
    
    print(f"\n📈 Общая статистика:")
    print(f"   Всего событий: {total_events}")
    
    # Группируем UI события
    ui_events = user_clicks + user_sliders + user_combos + user_colors
    print(f"   ├─ UI элементы: {ui_events}")
    if user_clicks > 0:
        print(f"   │  ├─ Клики (QCheckBox): {user_clicks}")
    if user_sliders > 0:
        print(f"   │  ├─ Слайдеры: {user_sliders}")
    if user_combos > 0:
        print(f"   │  ├─ Комбобоксы: {user_combos}")
    if user_colors > 0:
        print(f"   │  └─ Выбор цвета: {user_colors}")
    
    # Группируем мышь
    mouse_events = mouse_press + mouse_drag + mouse_wheel + mouse_release
    if mouse_events > 0:
        print(f"   ├─ События мыши: {mouse_events}")
        if mouse_press > 0:
            print(f"   │  ├─ Нажатия: {mouse_press}")
        if mouse_drag > 0:
            print(f"   │  ├─ Перетаскивание: {mouse_drag}")
        if mouse_wheel > 0:
            print(f"   │  ├─ Прокрутка (zoom): {mouse_wheel}")
        if mouse_release > 0:
            print(f"   │  └─ Отпускание: {mouse_release}")
    
    # State и сигналы
    print(f"   ├─ Изменения state: {state_changes}")
    print(f"   ├─ Вызовы emit(): {signals_emit}")
    print(f"   ├─ Получение сигналов в QML: {signals_received}")
    print(f"   ├─ Вызовы функций QML: {functions_called}")
    print(f"   └─ Изменения свойств QML: {properties_changed}")
    
    # Анализ синхронизации
    sync_analysis = analyze_event_pairs(events)
    print(f"\n🔗 Синхронизация Python→QML:")
    print(f"   Всего сигналов emit: {sync_analysis['total']}")
    print(f"   ├─ Успешно синхронизировано: {sync_analysis['synced']}")
    print(f"   └─ Пропущено QML: {sync_analysis['missing']}")
    
    if sync_analysis['total'] > 0:
        sync_rate = (sync_analysis['synced'] / sync_analysis['total']) * 100
        print(f"   📊 Процент синхронизации: {sync_rate:.1f}%")
        
        if sync_rate < 100.0:
            print(f"   ⚠️  Обнаружены проблемы синхронизации!")
    
    # Задержки
    synced_pairs = [p for p in sync_analysis['pairs'] if p['status'] == 'synced']
    if synced_pairs:
        latencies = [p['latency_ms'] for p in synced_pairs]
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        min_latency = min(latencies)
        
        print(f"\n⏱️  Задержки Python→QML:")
        print(f"   Средняя: {avg_latency:.2f} мс")
        print(f"   Минимальная: {min_latency:.2f} мс")
        print(f"   Максимальная: {max_latency:.2f} мс")
    
    # Медленные обновления
    slow = find_slow_updates(sync_analysis['pairs'])
    if slow:
        print(f"\n🐌 Медленные обновления (>50ms):")
        for item in slow[:5]:  # Показываем топ-5
            print(f"   • {item['signal']}: {item['latency_ms']:.2f} мс")
    
    # По категориям
    categories = analyze_by_category(events)
    print(f"\n📂 По компонентам:")
    for component, stats in sorted(categories.items(), key=lambda x: x[1]['total'], reverse=True):
        print(f"   {component}:")
        print(f"      Всего событий: {stats['total']}")
        if stats['user_clicks'] > 0:
            print(f"      Клики: {stats['user_clicks']}")
        if stats['state_changes'] > 0:
            print(f"      State: {stats['state_changes']}")
        if stats['signals_emit'] > 0:
            print(f"      Emit: {stats['signals_emit']}")
        if stats['signals_received'] > 0:
            print(f"      Received: {stats['signals_received']}")
    
    # Пропущенные сигналы
    missing_pairs = [p for p in sync_analysis['pairs'] if p['status'] == 'missing_qml']
    if missing_pairs:
        print(f"\n⚠️  Пропущенные сигналы QML ({len(missing_pairs)}):")
        for pair in missing_pairs[:10]:  # Показываем первые 10
            event = pair['python_event']
            print(f"   • {event['action']} @ {event['timestamp']}")
            if event.get('new_value'):
                print(f"      Payload: {event['new_value']}")
    
    print("="*60)


def export_html_report(events: List[Dict[str, Any]], output_file: Path | str = "logs/event_analysis.html") -> None:
    """Экспорт отчета в HTML"""
    output_file = Path(output_file)
    
    sync_analysis = analyze_event_pairs(events)
    categories = analyze_by_category(events)
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Event Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2 {{ color: #333; }}
        .summary {{ background: #f0f0f0; padding: 15px; border-radius: 5px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background: white; border-radius: 3px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #4CAF50; color: white; }}
        .warning {{ color: orange; }}
        .error {{ color: red; }}
        .success {{ color: green; }}
    </style>
</head>
<body>
    <h1>📊 Python↔QML Event Analysis</h1>
    
    <div class="summary">
        <h2>Summary</h2>
        <div class="metric">
            <strong>Total Events:</strong> {len(events)}
        </div>
        <div class="metric">
            <strong>Sync Rate:</strong> 
            <span class="{'success' if sync_analysis['missing'] == 0 else 'warning'}">
                {(sync_analysis['synced'] / max(sync_analysis['total'], 1) * 100):.1f}%
            </span>
        </div>
        <div class="metric">
            <strong>Missing QML:</strong> 
            <span class="{'error' if sync_analysis['missing'] > 0 else 'success'}">
                {sync_analysis['missing']}
            </span>
        </div>
    </div>
    
    <h2>Event Timeline</h2>
    <table>
        <tr>
            <th>Timestamp</th>
            <th>Type</th>
            <th>Component</th>
            <th>Action</th>
            <th>Value</th>
        </tr>
"""
    
    for event in events[:100]:  # Первые 100 событий
        html += f"""        <tr>
            <td>{event['timestamp']}</td>
            <td>{event['event_type']}</td>
            <td>{event['component']}</td>
            <td>{event['action']}</td>
            <td>{str(event.get('new_value', ''))[:50]}</td>
        </tr>
"""
    
    html += """    </table>
</body>
</html>"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n📄 HTML отчет экспортирован: {output_file}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze Python↔QML event synchronization")
    parser.add_argument('--logs-dir', type=str, default='logs', help='Logs directory')
    parser.add_argument('--html', action='store_true', help='Generate HTML report')
    
    args = parser.parse_args()
    
    # Загружаем события
    events = load_latest_events(args.logs_dir)
    
    if not events:
        print("❌ No events found")
        return 1
    
    # Печатаем анализ
    print_analysis_report(events)
    
    # HTML отчет
    if args.html:
        export_html_report(events)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
