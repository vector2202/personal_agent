import sqlite3
import os
from datetime import datetime
from enum import Enum
from typing import Type, Dict, Any, Optional, List
from pydantic import BaseModel, Field
from skills.base import BaseSkill

class ExpenseAction(str, Enum):
    LOG = "LOG"
    ANALYZE = "ANALYZE"
    LIST = "LIST"

class ExpenseTrackerInput(BaseModel):
    action: ExpenseAction = Field(
        ..., 
        description="Action to perform: 'LOG' to record an expense, 'ANALYZE' to get category totals and analytics, or 'LIST' to view recent entries."
    )
    amount: Optional[float] = Field(
        default=None, 
        description="Amount of money spent (required for LOG)."
    )
    category: Optional[str] = Field(
        default=None, 
        description="Category of the expense (e.g., 'Food & Dining', 'Shopping', 'Entertainment', 'Transportation', 'Groceries', 'Utilities', 'Health')."
    )
    merchant: Optional[str] = Field(
        default=None, 
        description="Where or to whom the money was paid (e.g., 'Amazon', 'Starbucks', 'Uber')."
    )
    description: Optional[str] = Field(
        default=None, 
        description="Details or item description (e.g., 'toy for nephew', 'morning coffee')."
    )
    date: Optional[str] = Field(
        default=None, 
        description="Date in YYYY-MM-DD format. Defaults to current date if not provided."
    )
    limit: Optional[int] = Field(
        default=20, 
        description="Maximum transactions to return when listing."
    )

class ExpenseTrackerSkill(BaseSkill):
    """
    Skill for recording, persisting, and analyzing personal expenses using a local SQLite database.
    Allows unstructured conversational expense logging and deterministic financial aggregation.
    """

    def __init__(self, db_path: str = "expenses.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    merchant TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    @property
    def name(self) -> str:
        return "expense_tracker"

    @property
    def description(self) -> str:
        return (
            "Logs, tracks, and analyzes personal expenses. "
            "Use action 'LOG' whenever the user mentions spending money or buying something. "
            "Use action 'ANALYZE' when the user asks for a financial summary, expense breakdown, or insights on where they spent and could save money. "
            "Use action 'LIST' to show recent transactions."
        )

    @property
    def input_schema(self) -> Type[BaseModel]:
        return ExpenseTrackerInput

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        data = self.input_schema(**params)

        if data.action == ExpenseAction.LOG:
            if data.amount is None or data.amount <= 0:
                return {"success": False, "error": "A positive 'amount' is required to log an expense."}
            
            expense_date = data.date or datetime.now().strftime("%Y-%m-%d")
            category = data.category or "General/Uncategorized"
            merchant = data.merchant or "Unknown"
            description = data.description or ""

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO expenses (date, amount, category, merchant, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (expense_date, data.amount, category, merchant, description))
                conn.commit()
                expense_id = cursor.lastrowid

            return {
                "success": True,
                "message": f"Logged expense #{expense_id}: ${data.amount:.2f} on {category} ({merchant}) - {description}",
                "expense": {
                    "id": expense_id,
                    "date": expense_date,
                    "amount": data.amount,
                    "category": category,
                    "merchant": merchant,
                    "description": description
                }
            }

        elif data.action == ExpenseAction.ANALYZE:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Total spent
                cursor.execute("SELECT COALESCE(SUM(amount), 0), COUNT(*) FROM expenses")
                total_spent, transaction_count = cursor.fetchone()

                if transaction_count == 0:
                    return {
                        "success": True,
                        "message": "No expenses recorded yet.",
                        "total_spent": 0.0,
                        "transaction_count": 0,
                        "by_category": [],
                        "top_merchants": []
                    }

                # Breakdown by category
                cursor.execute("""
                    SELECT category, ROUND(SUM(amount), 2) as total, COUNT(*) as count
                    FROM expenses
                    GROUP BY category
                    ORDER BY total DESC
                """)
                by_category = [
                    {"category": row[0], "total": row[1], "count": row[2], "percentage": round((row[1] / total_spent) * 100, 1)}
                    for row in cursor.fetchall()
                ]

                # Top merchants
                cursor.execute("""
                    SELECT merchant, ROUND(SUM(amount), 2) as total, COUNT(*) as count
                    FROM expenses
                    WHERE merchant != 'Unknown'
                    GROUP BY merchant
                    ORDER BY total DESC
                    LIMIT 5
                """)
                top_merchants = [
                    {"merchant": row[0], "total": row[1], "count": row[2]}
                    for row in cursor.fetchall()
                ]

                # Recent transactions sample
                cursor.execute("""
                    SELECT id, date, amount, category, merchant, description
                    FROM expenses
                    ORDER BY date DESC, id DESC
                    LIMIT 15
                """)
                recent_transactions = [
                    {"id": r[0], "date": r[1], "amount": r[2], "category": r[3], "merchant": r[4], "description": r[5]}
                    for r in cursor.fetchall()
                ]

            return {
                "success": True,
                "total_spent": round(total_spent, 2),
                "transaction_count": transaction_count,
                "by_category": by_category,
                "top_merchants": top_merchants,
                "recent_transactions": recent_transactions
            }

        elif data.action == ExpenseAction.LIST:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, date, amount, category, merchant, description
                    FROM expenses
                    ORDER BY date DESC, id DESC
                    LIMIT ?
                """, (data.limit or 20,))
                transactions = [
                    {"id": r[0], "date": r[1], "amount": r[2], "category": r[3], "merchant": r[4], "description": r[5]}
                    for r in cursor.fetchall()
                ]

            return {
                "success": True,
                "count": len(transactions),
                "transactions": transactions
            }

        return {"success": False, "error": f"Unknown action '{data.action}'"}
