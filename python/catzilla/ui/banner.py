"""
Startup banner renderer for Catzilla web framework.
"""

from datetime import datetime
from typing import List

from .collectors import ServerInfo, ServerInfoCollector
from .formatters import COLORS, ColorFormatter


class BannerRenderer:
    """Renders beautiful startup banners for Catzilla"""

    def __init__(self, enable_colors: bool = True):
        """Initialize banner renderer with color support"""
        self.formatter = ColorFormatter(enable_colors)
        self.box_width = (
            62  # Width of the banner box content (adjusted for proper alignment)
        )

    def render_startup_banner(self, server_info: ServerInfo) -> str:
        """Render the complete startup banner"""
        lines = []

        # Header section
        lines.extend(self._render_header(server_info))
        lines.append("║" + " " * (self.box_width + 6) + "║")

        # Configuration sections
        lines.extend(self._render_dev_config_section(server_info))
        lines.append("║" + " " * (self.box_width + 6) + "║")

        lines.extend(self._render_server_section(server_info))
        lines.append("║" + " " * (self.box_width + 6) + "║")

        lines.extend(self._render_system_section(server_info))
        lines.append("║" + " " * (self.box_width + 6) + "║")

        # Footer section
        lines.extend(self._render_footer(server_info))

        return "\n".join(lines)

    def render_minimal_banner(self, server_info: ServerInfo) -> str:
        """Render a minimal banner for production mode"""
        return (
            f"Catzilla v{server_info.version} - "
            f"{server_info.protocol}://{server_info.host}:{server_info.port} - "
            f"{server_info.route_count} routes - "
            f"PID {server_info.pid}"
        )

    def _render_header(self, info: ServerInfo) -> List[str]:
        """Render the header section with title and URL"""
        lines = []

        # Top border
        lines.append("╔" + "═" * (self.box_width + 6) + "╗")

        # Title line with version and mode
        version_text = f"🐱 Catzilla v{info.version}"
        mode_text = f" - {info.mode.upper()}"
        title_line = version_text + mode_text

        if self.formatter.colors_enabled:
            title_line = (
                self.formatter.colorize("🐱 Catzilla", COLORS.BRIGHT_RED)
                + self.formatter.colorize(f" v{info.version}", COLORS.BRIGHT_WHITE)
                + self.formatter.colorize(
                    mode_text,
                    (
                        COLORS.BRIGHT_YELLOW
                        if info.mode == "development"
                        else COLORS.BRIGHT_GREEN
                    ),
                )
            )

        # Remove ANSI codes for length calculation
        clean_title = self._strip_ansi(title_line)
        total_width = self.box_width + 6
        line_content = f" {title_line}"
        pad_len = total_width - 2 - len(self._strip_ansi(line_content))  # 2 for ║ ║
        lines.append(f"║{line_content}{' ' * pad_len}║")

        # URL line
        url = f"{info.protocol}://{info.host}:{info.port}"
        if self.formatter.colors_enabled:
            url = self.formatter.colorize(url, COLORS.BRIGHT_WHITE)

        line_content = f" {url}"
        pad_len = total_width - 2 - len(self._strip_ansi(line_content))
        lines.append(f"║{line_content}{' ' * pad_len}║")

        # Bind info line
        bind_info = f"(bound on host {info.host} and port {info.port})"
        line_content = f" {bind_info}"
        pad_len = total_width - 2 - len(self._strip_ansi(line_content))
        lines.append(f"║{line_content}{' ' * pad_len}║")

        return lines

    def _render_dev_config_section(self, info: ServerInfo) -> List[str]:
        """Render development-specific configuration"""
        lines = []

        config_items = [
            ("Environment", info.mode.title()),
            ("Debug", "Enabled" if info.debug_enabled else "Disabled"),
            ("Hot Reload", "Enabled" if info.hot_reload_enabled else "Disabled"),
        ]

        for label, value in config_items:
            lines.append(self._format_info_line(label, value))

        return lines

    def _render_server_section(self, info: ServerInfo) -> List[str]:
        """Render server configuration section"""
        lines = []

        server_items = [
            ("Routes", str(info.route_count)),
            ("Workers", str(info.worker_count)),
            (
                "Prefork",
                (
                    f"Enabled ({info.prefork_processes} processes)"
                    if info.prefork_enabled
                    else "Disabled"
                ),
            ),
            ("jemalloc", "Enabled" if info.jemalloc_enabled else "Disabled"),
            ("Cache", info.cache_info),
            (
                "Profiling",
                (
                    f"Enabled ({info.profiling_interval}s interval)"
                    if info.profiling_enabled
                    else "Disabled"
                ),
            ),
        ]

        for label, value in server_items:
            lines.append(self._format_info_line(label, value))

        return lines

    def _render_system_section(self, info: ServerInfo) -> List[str]:
        """Render system information section"""
        lines = []

        system_items = [
            ("PID", str(info.pid)),
            ("Memory", info.memory_usage),
            ("Started", info.start_time.strftime("%Y-%m-%d %H:%M:%S")),
        ]

        for label, value in system_items:
            lines.append(self._format_info_line(label, value))

        return lines

    def _render_footer(self, info: ServerInfo) -> List[str]:
        """Render footer section"""
        lines = []

        # Development message or minimal production message
        if info.debug_enabled:
            message = "💡 Request logging enabled - watching for changes..."
            if self.formatter.colors_enabled:
                message = self.formatter.colorize(message, COLORS.BRIGHT_YELLOW)
        else:
            message = "🚀 Production server ready"
            if self.formatter.colors_enabled:
                message = self.formatter.colorize(message, COLORS.BRIGHT_GREEN)

        line_content = f" {message}"
        pad_len = (
            self.box_width + 4 - len(self._strip_ansi(line_content))
        )  # 4 because '║ ' and ' ║'
        lines.append(f"║{line_content}{' ' * pad_len}║")

        # Bottom border
        lines.append("╚" + "═" * (self.box_width + 6) + "╝")

        return lines

    def _format_info_line(self, label: str, value: str) -> str:
        """Format an information line with proper padding"""
        max_label_width = 20  # Maximum width for labels

        # Truncate label if too long
        if len(label) > max_label_width:
            label = label[: max_label_width - 3] + "..."

        # Calculate dots needed
        dots_needed = max_label_width - len(label)
        dots = "." * dots_needed

        # Format the line
        formatted_line = f" {label} {dots} {value}"

        # Apply colors if enabled
        if self.formatter.colors_enabled:
            # Color the label in cyan
            label_colored = self.formatter.colorize(label, COLORS.BRIGHT_CYAN)
            # Color dots in dark gray
            dots_colored = self.formatter.colorize(dots, COLORS.BRIGHT_BLACK)
            # Color value based on content
            value_colored = self._color_value(value)
            formatted_line = f" {label_colored} {dots_colored} {value_colored}"

        # Calculate padding needed (account for leading and trailing spaces)
        total_width = self.box_width + 6
        line_content = f"{formatted_line}"
        pad_len = total_width - 2 - len(self._strip_ansi(line_content))  # 2 for ║ ║
        return f"║{line_content}{' ' * pad_len}║"

    def _color_value(self, value: str) -> str:
        """Apply appropriate color to a value based on its content"""
        if not self.formatter.colors_enabled:
            return value

        value_lower = value.lower()

        # Color by content
        if "enabled" in value_lower:
            return self.formatter.colorize(value, COLORS.BRIGHT_GREEN)
        elif "disabled" in value_lower:
            return self.formatter.colorize(value, COLORS.BRIGHT_RED)
        elif value_lower in ["development"]:
            return self.formatter.colorize(value, COLORS.BRIGHT_YELLOW)
        elif value_lower in ["production"]:
            return self.formatter.colorize(value, COLORS.BRIGHT_GREEN)
        else:
            return self.formatter.colorize(value, COLORS.BRIGHT_WHITE)

    def _strip_ansi(self, text: str) -> str:
        """Remove ANSI escape codes from text for length calculation"""
        import re

        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", text)


# Re-export ServerInfoCollector for convenience
__all__ = ["BannerRenderer", "ServerInfoCollector"]
