"""Web-based dashboard"""
import os, sys
from core.plugin import Plugin

class WebDashboardPlugin(Plugin):
    name = "web_dashboard"
    version = "1.0.0"
    author = "MEGASUS"
    description = "Web-based dashboard"

    def initialize(self):
        self.log("Initialized " + self.name)

    def shutdown(self):
        self.log("Shutdown " + self.name)

def register():
    return WebDashboardPlugin