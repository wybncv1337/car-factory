# src/alerts/alert_manager.py

import sqlite3
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertManager:
    """Менеджер для создания и проверки алертов"""

    def __init__(self, db_path: str = 'car_factory.db'):
        self.db_path = db_path

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def create_alert(self, name: str, conditions: Dict) -> int:
        """
        Создает новый алерт

        Args:
            name: название алерта
            conditions: {
                'company': 'Tesla',  # опционально
                'alert_type': 'vacancy',  # vacancy/release/price
                'keywords': 'Python, engineer',  # через запятую
                'language': 'ru',  # ru/en/any
                'frequency': 'daily',  # hourly/daily/weekly
                'user_id': 'default'
            }

        Returns:
            id созданного алерта
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
                       INSERT INTO alerts (name, company, alert_type, keywords, language,
                                           frequency, user_id, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                       ''', (
                           name,
                           conditions.get('company'),
                           conditions.get('alert_type'),
                           conditions.get('keywords'),
                           conditions.get('language', 'any'),
                           conditions.get('frequency', 'daily'),
                           conditions.get('user_id', 'default'),
                           datetime.now()
                       ))

        alert_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"✅ Алерт '{name}' создан с ID={alert_id}")
        return alert_id

    def get_alerts(self, user_id: str = 'default') -> List[Dict]:
        """Получает все алерты пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
                       SELECT id,
                              name,
                              company,
                              alert_type,
                              keywords, language, frequency, is_active, created_at, last_triggered_at
                       FROM alerts
                       WHERE user_id = ? AND is_active = 1
                       ORDER BY created_at DESC
                       ''', (user_id,))

        rows = cursor.fetchall()
        conn.close()

        alerts = []
        for row in rows:
            alerts.append({
                'id': row[0],
                'name': row[1],
                'company': row[2],
                'type': row[3],
                'keywords': row[4].split(',') if row[4] else [],
                'language': row[5],
                'frequency': row[6],
                'is_active': bool(row[7]),
                'created_at': row[8],
                'last_triggered_at': row[9]
            })

        return alerts

    def delete_alert(self, alert_id: int, user_id: str = 'default') -> bool:
        """Удаляет алерт"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
                       DELETE
                       FROM alerts
                       WHERE id = ?
                         AND user_id = ?
                       ''', (alert_id, user_id))

        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()

        if deleted:
            logger.info(f"✅ Алерт {alert_id} удален")
        return deleted

    def toggle_alert(self, alert_id: int, active: bool) -> bool:
        """Включает/выключает алерт"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
                       UPDATE alerts
                       SET is_active = ?
                       WHERE id = ?
                       ''', (1 if active else 0, alert_id))

        conn.commit()
        conn.close()
        return True

    def check_alert(self, alert: Dict, text: str) -> Optional[Dict]:
        """
        Проверяет, срабатывает ли алерт на тексте

        Returns:
            Dict с информацией о срабатывании или None
        """
        text_lower = text.lower()

        # Проверка компании
        if alert['company']:
            if alert['company'].lower() not in text_lower:
                return None

        # Проверка типа (вакансия/релиз/цена)
        if alert['type'] and alert['type'] != 'any':
            type_markers = {
                'vacancy': ['ваканс', 'hire', 'job', 'salary', 'зарплат'],
                'release': ['выпуст', 'release', 'новая модель', 'релиз'],
                'price': ['цена', 'price', 'стоимост', 'руб', '$']
            }
            markers = type_markers.get(alert['type'], [])
            if not any(m in text_lower for m in markers):
                return None

        # Проверка ключевых слов
        if alert['keywords']:
            keywords = [k.strip().lower() for k in alert['keywords']]
            if not any(kw in text_lower for kw in keywords):
                return None

        # Проверка языка (упрощенно)
        if alert['language'] and alert['language'] != 'any':
            has_russian = any(c in text_lower for c in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
            if alert['language'] == 'ru' and not has_russian:
                return None
            elif alert['language'] == 'en' and has_russian:
                return None

        # Найдено совпадение
        return {
            'alert_id': alert['id'],
            'alert_name': alert['name'],
            'matched_text': text[:200],
            'matched_by': {
                'company': alert['company'],
                'type': alert['type'],
                'keywords': alert['keywords'],
                'language': alert['language']
            },
            'triggered_at': datetime.now().isoformat()
        }

    def check_all_alerts(self, text: str, doc_id: int = None) -> List[Dict]:
        """Проверяет все активные алерты на тексте"""
        alerts = self.get_alerts()
        triggers = []

        for alert in alerts:
            result = self.check_alert(alert, text)
            if result:
                triggers.append(result)
                self.save_trigger(alert['id'], doc_id, text)

        return triggers

    def save_trigger(self, alert_id: int, doc_id: int, text: str):
        """Сохраняет срабатывание в историю"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
                       UPDATE alerts
                       SET last_triggered_at = ?
                       WHERE id = ?
                       ''', (datetime.now(), alert_id))

        cursor.execute('''
                       INSERT INTO alert_triggers (alert_id, matched_doc_id, matched_text)
                       VALUES (?, ?, ?)
                       ''', (alert_id, doc_id, text[:500]))

        conn.commit()
        conn.close()

    def get_trigger_history(self, alert_id: int = None, limit: int = 50) -> List[Dict]:
        """Получает историю срабатываний"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if alert_id:
            cursor.execute('''
                           SELECT id, alert_id, matched_text, triggered_at
                           FROM alert_triggers
                           WHERE alert_id = ?
                           ORDER BY triggered_at DESC LIMIT ?
                           ''', (alert_id, limit))
        else:
            cursor.execute('''
                           SELECT id, alert_id, matched_text, triggered_at
                           FROM alert_triggers
                           ORDER BY triggered_at DESC LIMIT ?
                           ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [{
            'id': row[0],
            'alert_id': row[1],
            'matched_text': row[2],
            'triggered_at': row[3]
        } for row in rows]

    def get_stats(self) -> Dict:
        """Получает статистику по алертам"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM alerts WHERE is_active = 1')
        total_alerts = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM alert_triggers')
        total_triggers = cursor.fetchone()[0]

        cursor.execute('''
                       SELECT alert_id, COUNT(*) as count
                       FROM alert_triggers
                       GROUP BY alert_id
                       ORDER BY count DESC
                           LIMIT 5
                       ''')
        top_alerts = [{'alert_id': row[0], 'triggers': row[1]} for row in cursor.fetchall()]

        conn.close()

        return {
            'total_active_alerts': total_alerts,
            'total_triggers': total_triggers,
            'top_alerts': top_alerts
        }