import os
import platform
import shutil
import time
from typing import Type, Dict, Any, List
from pydantic import BaseModel, Field
from skills.base import BaseSkill

class HealthMonitorInput(BaseModel):
    include_disk: bool = Field(default=True, description="Whether to include disk usage statistics.")
    include_system_info: bool = Field(default=True, description="Whether to include OS and architecture metadata.")

class SystemHealthMonitor(BaseSkill):
    """
    Monitors machine resources, platform info, memory, and disk usage for real-time telemetry.
    """

    @property
    def name(self) -> str:
        return "system_health_monitor"

    @property
    def description(self) -> str:
        return "Inspects and reports system resource utilization, memory, disk usage, and host OS health metrics."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return HealthMonitorInput

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        data = self.input_schema(**params)
        
        report: Dict[str, Any] = {
            "success": True,
            "timestamp": time.time()
        }

        if data.include_system_info:
            report["system"] = {
                "os": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
                "python_version": platform.python_version(),
                "cpu_count": os.cpu_count()
            }

        if data.include_disk:
            total, used, free = shutil.disk_usage("/")
            report["disk_usage_gb"] = {
                "total": round(total / (1024 ** 3), 2),
                "used": round(used / (1024 ** 3), 2),
                "free": round(free / (1024 ** 3), 2),
                "used_percentage": round((used / total) * 100, 1)
            }

        return report
