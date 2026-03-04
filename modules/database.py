"""
Case History Database Module
Stores and retrieves verification case history using SQLite.
"""

import sqlite3
import json
from typing import Dict, Any, List
import os

class CaseDatabase:
    """Manages case history storage and retrieval."""
    
    def __init__(self, db_path: str = "data/case_history.db"):
        """Initialize database connection."""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Create database schema if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT,
                scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ai_findings TEXT,
                doctor_findings TEXT,
                verification_results TEXT,
                comparison_report TEXT,
                medical_narrative TEXT,
                image_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_case(self, case_data: Dict[str, Any]) -> int:
        """
        Save a verification case to the database.
        
        Args:
            case_data: Dictionary containing case information
            
        Returns:
            Case ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO cases (
                patient_id, ai_findings, doctor_findings,
                verification_results, comparison_report,
                medical_narrative, image_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            case_data.get('patient_id', 'UNKNOWN'),
            json.dumps(case_data.get('ai_findings', {})),
            json.dumps(case_data.get('doctor_findings', {})),
            json.dumps(case_data.get('verification_results', {})),
            case_data.get('comparison_report', ''),
            case_data.get('medical_narrative', ''),
            case_data.get('image_path', '')
        ))
        
        case_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return case_id
    
    def get_case(self, case_id: int) -> Dict[str, Any]:
        """Retrieve a specific case by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM cases WHERE id = ?', (case_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_dict(row)
        return None
    
    def get_recent_cases(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent cases."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM cases 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def search_cases(self, patient_id: str = None, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """Search cases by criteria."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM cases WHERE 1=1'
        params = []
        
        if patient_id:
            query += ' AND patient_id = ?'
            params.append(patient_id)
        
        if start_date:
            query += ' AND scan_date >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND scan_date <= ?'
            params.append(end_date)
        
        query += ' ORDER BY created_at DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert database row to dictionary."""
        return {
            'id': row[0],
            'patient_id': row[1],
            'scan_date': row[2],
            'ai_findings': json.loads(row[3]) if row[3] else {},
            'doctor_findings': json.loads(row[4]) if row[4] else {},
            'verification_results': json.loads(row[5]) if row[5] else {},
            'comparison_report': row[6],
            'medical_narrative': row[7],
            'image_path': row[8],
            'created_at': row[9]
        }
