#!/usr/bin/env python3
"""
RAGSPRO Content Creation Agent
Self-monitoring agent that generates content continuously
Integrates with existing content_engine.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict
import subprocess

sys.path.insert(0, str(Path(__file__).parent.parent))

from . import BaseAgent


class ContentCreationAgent(BaseAgent):
    """
    Self-monitoring agent for continuous content creation
    - Generates daily content at 6 AM
    - Creates Instagram content 3x/day
    - Monitors content performance
    - Alerts on low engagement
    """

    def __init__(self):
        super().__init__(
            name="ContentCreationAgent",
            description="Generates LinkedIn, Twitter, Instagram, Reel content automatically"
        )

        # Add tasks
        self.add_task("daily_content", "Generate daily content batch", self._generate_daily_content, 1440)  # 24 hours
        self.add_task("content_health", "Check content generation health", self._content_health_check, 60)  # 1 hour
        self.add_task("queue_check", "Verify content queue", self._check_queue, 360)  # 6 hours

    def _generate_daily_content(self) -> Dict:
        """Generate daily content using existing content_engine.py"""
        try:
            result = subprocess.run(
                ["python3", str(Path(__file__).parent.parent / "content_engine.py")],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                # Check how many pieces were generated
                generated_count = 0
                for line in result.stdout.split("\n"):
                    if "Generated" in line and "pieces" in line:
                        try:
                            generated_count = int(line.split()[1])
                        except:
                            pass

                self.send_alert(
                    f"✅ Generated {generated_count} content pieces for today!\nCheck RAGS HUB page.",
                    priority="normal"
                )

                return {"success": True, "generated": generated_count}
            else:
                raise Exception(f"Content generation failed: {result.stderr}")

        except Exception as e:
            raise Exception(f"Daily content generation failed: {e}")

    def _content_health_check(self) -> Dict:
        """Check if content is being generated properly"""
        try:
            from config import DATA_DIR

            content_dir = DATA_DIR / "content"
            today_folder = content_dir / datetime.now().strftime("%Y-%m-%d")

            if not today_folder.exists():
                # No content for today - try to generate
                self.log("No content for today, triggering generation...")
                self._generate_daily_content()
                return {"success": True, "message": "Triggered content generation"}

            # Check files
            files = list(today_folder.glob("*.txt"))
            if len(files) < 4:
                self.send_alert(
                    f"⚠️ Only {len(files)}/4 content files generated today",
                    priority="normal"
                )

            return {"success": True, "files_generated": len(files)}

        except Exception as e:
            raise Exception(f"Content health check failed: {e}")

    def _check_queue(self) -> Dict:
        """Check content queue and schedule posts"""
        try:
            # Check if there are scheduled posts
            from config import DATA_DIR

            queue_file = DATA_DIR / "content_queue.json"
            if queue_file.exists():
                import json
                with open(queue_file) as f:
                    queue = json.load(f)

                scheduled = [q for q in queue if q.get("status") == "scheduled"]

                if len(scheduled) < 7:  # Less than a week
                    self.send_alert(
                        f"📢 Content queue running low: {len(scheduled)} posts scheduled",
                        priority="normal"
                    )

                return {"success": True, "scheduled_posts": len(scheduled)}

            return {"success": True, "message": "No queue file"}

        except Exception as e:
            raise Exception(f"Queue check failed: {e}")


if __name__ == "__main__":
    agent = ContentCreationAgent()
    agent.start()

    import time
    while True:
        time.sleep(1)
