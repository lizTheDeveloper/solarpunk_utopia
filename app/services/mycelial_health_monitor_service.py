"""
Mycelial Health Monitor Service

Monitors the physical health of mesh network nodes:
- Battery health (charge cycles, capacity degradation)
- Storage health (I/O errors, free space)
- Temperature monitoring
- Power outage detection
- Predictive failure alerts

Publishes hardware maintenance needs to ValueFlows when intervention required.
Privacy-preserving: only hardware health data, no location or usage tracking.
"""

import logging
import platform
import psutil
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class MycelialHealthMonitorService:
    """
    Monitors hardware health metrics for mesh network nodes.

    Designed for Android phones but works on any platform with degraded functionality.
    Uses psutil for cross-platform metrics and Android-specific APIs when available.
    """

    def __init__(self, db_path: str = "node_health.db"):
        self.db_path = db_path
        self.platform = platform.system()
        self.is_android = self.platform == "Linux" and Path("/system/build.prop").exists()
        logger.info(f"MycelialHealthMonitor initialized (platform: {self.platform}, android: {self.is_android})")

        # Health thresholds
        self.battery_cycle_warning = 500  # Warn when charge cycles > 500
        self.battery_degradation_warning = 0.80  # Warn when capacity < 80% of design
        self.storage_io_error_threshold = 10  # Max I/O errors before alert
        self.storage_free_space_warning = 0.10  # Warn when < 10% free
        self.temperature_warning = 45.0  # Celsius
        self.power_outage_cluster_size = 3  # Nodes switching to battery simultaneously

    def get_battery_health(self) -> Dict:
        """
        Collect battery health metrics.

        Returns:
            dict with: percent, is_charging, time_remaining, health_status, cycles (Android only)
        """
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return {"available": False, "status": "no_battery"}

            health = {
                "available": True,
                "percent": battery.percent,
                "is_charging": battery.power_plugged,
                "time_remaining_seconds": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None,
                "timestamp": datetime.now(UTC).isoformat(),
            }

            # Android-specific: try to get charge cycles and capacity
            if self.is_android:
                health.update(self._get_android_battery_details())

            # Determine health status
            health["health_status"] = self._assess_battery_health(health)

            return health

        except Exception as e:
            logger.error(f"Error getting battery health: {e}")
            return {"available": False, "error": str(e)}

    def _get_android_battery_details(self) -> Dict:
        """
        Get Android-specific battery details via system files.

        Returns:
            dict with: charge_cycles, capacity_percent, temperature
        """
        details = {}

        try:
            # Read charge cycles (if available)
            cycle_path = Path("/sys/class/power_supply/battery/cycle_count")
            if cycle_path.exists():
                details["charge_cycles"] = int(cycle_path.read_text().strip())

            # Read capacity percentage (design vs current)
            capacity_path = Path("/sys/class/power_supply/battery/capacity")
            if capacity_path.exists():
                details["capacity_percent"] = int(capacity_path.read_text().strip())

            # Read temperature (in tenths of degree Celsius)
            temp_path = Path("/sys/class/power_supply/battery/temp")
            if temp_path.exists():
                temp_raw = int(temp_path.read_text().strip())
                details["temperature_celsius"] = temp_raw / 10.0

        except Exception as e:
            logger.warning(f"Could not read Android battery details: {e}")

        return details

    def _assess_battery_health(self, health: Dict) -> str:
        """
        Assess overall battery health status.

        Returns: "healthy", "degraded", "critical"
        """
        issues = []

        # Check charge cycles
        if health.get("charge_cycles", 0) > self.battery_cycle_warning:
            issues.append("high_cycles")

        # Check capacity degradation (Android only)
        if health.get("capacity_percent", 100) < (self.battery_degradation_warning * 100):
            issues.append("degraded_capacity")

        # Check temperature
        if health.get("temperature_celsius", 0) > self.temperature_warning:
            issues.append("high_temperature")

        if not issues:
            return "healthy"
        elif len(issues) == 1 or "degraded_capacity" not in issues:
            return "degraded"
        else:
            return "critical"

    def get_storage_health(self) -> Dict:
        """
        Collect storage health metrics.

        Returns:
            dict with: total_bytes, free_bytes, free_percent, io_errors, health_status
        """
        try:
            # Get disk usage for data directory
            usage = psutil.disk_usage("/")

            health = {
                "available": True,
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
                "free_percent": usage.percent / 100.0,
                "timestamp": datetime.now(UTC).isoformat(),
            }

            # Try to get I/O errors (Linux/Android)
            if self.platform == "Linux":
                health["io_errors"] = self._get_storage_io_errors()

            # Assess health
            health["health_status"] = self._assess_storage_health(health)

            return health

        except Exception as e:
            logger.error(f"Error getting storage health: {e}")
            return {"available": False, "error": str(e)}

    def _get_storage_io_errors(self) -> int:
        """
        Read I/O errors from system logs (Android/Linux).

        Returns:
            int: count of I/O errors in recent logs
        """
        try:
            # Check dmesg for I/O errors (requires root or special permissions)
            # In production, this would parse kernel ring buffer
            # For now, return 0 (would need proper permissions on Android)
            return 0
        except Exception as e:
            logger.warning(f"Could not read I/O errors: {e}")
            return 0

    def _assess_storage_health(self, health: Dict) -> str:
        """
        Assess overall storage health status.

        Returns: "healthy", "degraded", "critical"
        """
        free_percent = 1.0 - health["free_percent"]
        io_errors = health.get("io_errors", 0)

        if io_errors > self.storage_io_error_threshold:
            return "critical"
        elif free_percent < self.storage_free_space_warning:
            return "critical"
        elif free_percent < 0.20:
            return "degraded"
        else:
            return "healthy"

    def get_system_temperature(self) -> Dict:
        """
        Collect system temperature metrics.

        Returns:
            dict with temperatures by sensor
        """
        try:
            temps = psutil.sensors_temperatures() if hasattr(psutil, "sensors_temperatures") else {}

            if not temps:
                return {"available": False, "status": "no_sensors"}

            # Flatten sensor data
            temp_data = {
                "available": True,
                "sensors": {},
                "timestamp": datetime.now(UTC).isoformat(),
            }

            max_temp = 0.0
            for sensor_name, entries in temps.items():
                for entry in entries:
                    temp_data["sensors"][f"{sensor_name}_{entry.label or 'default'}"] = {
                        "current": entry.current,
                        "high": entry.high,
                        "critical": entry.critical,
                    }
                    max_temp = max(max_temp, entry.current)

            temp_data["max_temperature"] = max_temp
            temp_data["health_status"] = "critical" if max_temp > self.temperature_warning else "healthy"

            return temp_data

        except Exception as e:
            logger.error(f"Error getting temperature: {e}")
            return {"available": False, "error": str(e)}

    def get_network_health(self) -> Dict:
        """
        Collect network interface health metrics.

        Returns:
            dict with interface stats
        """
        try:
            stats = psutil.net_io_counters(pernic=True)

            health = {
                "available": True,
                "interfaces": {},
                "timestamp": datetime.now(UTC).isoformat(),
            }

            for interface, counters in stats.items():
                health["interfaces"][interface] = {
                    "bytes_sent": counters.bytes_sent,
                    "bytes_recv": counters.bytes_recv,
                    "packets_sent": counters.packets_sent,
                    "packets_recv": counters.packets_recv,
                    "errors_in": counters.errin,
                    "errors_out": counters.errout,
                    "drops_in": counters.dropin,
                    "drops_out": counters.dropout,
                }

            return health

        except Exception as e:
            logger.error(f"Error getting network health: {e}")
            return {"available": False, "error": str(e)}

    def get_full_health_report(self) -> Dict:
        """
        Generate comprehensive health report for this node.

        Returns:
            dict with all health metrics and overall status
        """
        report = {
            "node_id": self._get_node_id(),
            "timestamp": datetime.now(UTC).isoformat(),
            "platform": self.platform,
            "is_android": self.is_android,
            "battery": self.get_battery_health(),
            "storage": self.get_storage_health(),
            "temperature": self.get_system_temperature(),
            "network": self.get_network_health(),
        }

        # Determine overall health
        statuses = [
            report["battery"].get("health_status", "unknown"),
            report["storage"].get("health_status", "unknown"),
            report["temperature"].get("health_status", "unknown"),
        ]

        if "critical" in statuses:
            report["overall_status"] = "critical"
        elif "degraded" in statuses:
            report["overall_status"] = "degraded"
        else:
            report["overall_status"] = "healthy"

        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(report)

        return report

    def _get_node_id(self) -> str:
        """
        Get unique node identifier (derived from hardware).

        In production, this would use device serial or stable identifier.
        """
        try:
            # Use MAC address of first network interface as proxy
            import uuid
            mac = uuid.getnode()
            return f"node_{mac:012x}"
        except Exception as e:
            logger.warning(f"Could not determine node ID from MAC address: {e}")
            return "node_unknown"

    def _generate_recommendations(self, report: Dict) -> List[Dict]:
        """
        Generate actionable recommendations based on health report.

        Returns:
            list of dicts with: priority, action, reason
        """
        recommendations = []

        battery = report.get("battery", {})
        storage = report.get("storage", {})
        temperature = report.get("temperature", {})

        # Battery recommendations
        if battery.get("health_status") == "critical":
            if battery.get("charge_cycles", 0) > self.battery_cycle_warning:
                recommendations.append({
                    "priority": "high",
                    "action": "replace_battery",
                    "reason": f"Battery has {battery.get('charge_cycles')} charge cycles (threshold: {self.battery_cycle_warning})",
                    "resource_need": {
                        "type": "replacement_battery",
                        "specification": self._get_battery_specification(),
                    }
                })

            if battery.get("capacity_percent", 100) < (self.battery_degradation_warning * 100):
                recommendations.append({
                    "priority": "high",
                    "action": "replace_battery",
                    "reason": f"Battery capacity degraded to {battery.get('capacity_percent')}%",
                    "resource_need": {
                        "type": "replacement_battery",
                        "specification": self._get_battery_specification(),
                    }
                })

        # Storage recommendations
        if storage.get("health_status") == "critical":
            if storage.get("io_errors", 0) > self.storage_io_error_threshold:
                recommendations.append({
                    "priority": "urgent",
                    "action": "replace_storage",
                    "reason": f"Storage has {storage.get('io_errors')} I/O errors (threshold: {self.storage_io_error_threshold})",
                    "resource_need": {
                        "type": "microsd_card",
                        "specification": "32GB+ Class 10",
                    }
                })

            free_percent = 1.0 - storage.get("free_percent", 1.0)
            if free_percent < self.storage_free_space_warning:
                recommendations.append({
                    "priority": "medium",
                    "action": "free_storage_space",
                    "reason": f"Storage is {(1 - free_percent) * 100:.1f}% full",
                })

        # Temperature recommendations
        if temperature.get("health_status") == "critical":
            max_temp = temperature.get("max_temperature", 0)
            recommendations.append({
                "priority": "high",
                "action": "cool_device",
                "reason": f"System temperature is {max_temp:.1f}°C (threshold: {self.temperature_warning}°C)",
            })

        return recommendations

    def _get_battery_specification(self) -> str:
        """
        Get battery specification for replacement.

        In production, would query device model and lookup spec.
        """
        if self.is_android:
            return "Check device model for compatible battery"
        return "N/A"

    def detect_power_outage_cluster(self, node_health_reports: List[Dict]) -> Optional[Dict]:
        """
        Detect if multiple nodes in same cluster switched to battery simultaneously.

        Args:
            node_health_reports: List of recent health reports from nearby nodes

        Returns:
            dict with outage info if detected, None otherwise
        """
        # Look for nodes that switched to battery in last 5 minutes
        now = datetime.now(UTC)
        recent_battery_switches = []

        for report in node_health_reports:
            battery = report.get("battery", {})
            if not battery.get("is_charging") and battery.get("available"):
                # Node is on battery
                report_time = datetime.fromisoformat(report.get("timestamp", ""))
                if (now - report_time) < timedelta(minutes=5):
                    recent_battery_switches.append(report)

        # If >= threshold nodes on battery, likely power outage
        if len(recent_battery_switches) >= self.power_outage_cluster_size:
            return {
                "detected": True,
                "timestamp": now.isoformat(),
                "affected_nodes": [r["node_id"] for r in recent_battery_switches],
                "node_count": len(recent_battery_switches),
                "alert_type": "power_outage",
                "priority": "high",
            }

        return None
