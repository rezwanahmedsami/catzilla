"""
Catzilla Streaming Response Module

This module provides a streaming response system for the Catzilla web framework.
"""

import io
from typing import Any, Callable, Dict, Iterator, Optional, Union

from .types import Response


class StreamingResponse(Response):
    """
    Streaming HTTP response class that sends data incrementally to the client.

    This class enables efficient HTTP streaming without using async/await syntax,
    following Catzilla's synchronous-first approach. It can be used with any
    iterable, generator, or callable that produces strings or bytes.

    Example:
        ```python
        @app.get("/stream")
        def stream_response(request):
            def generate_data():
                for i in range(100):
                    yield f"data: {i}\n\n"
                    time.sleep(0.1)

            return StreamingResponse(generate_data())
        ```
    """

    def __init__(
        self,
        content: Optional[
            Union[
                Iterator[Union[str, bytes]],
                Callable[[], Iterator[Union[str, bytes]]],
                list,
            ]
        ] = None,
        content_type: str = "text/plain",
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize a streaming response.

        Args:
            content: An iterator, generator, callable, or list that produces strings or bytes
            content_type: MIME type of the response
            status_code: HTTP status code
            headers: Additional HTTP headers
        """
        # For now, we'll collect all the content into a single string/response
        # This is a temporary solution until we properly integrate with the C streaming API
        body = ""

        # Store original content for future reference
        self._content = content

        # Handle different types of content
        if content is not None:
            if isinstance(content, list):
                # If content is already a list, join it directly
                for chunk in content:
                    if isinstance(chunk, bytes):
                        chunk = chunk.decode("utf-8", errors="replace")
                    body += chunk
            elif callable(content):
                # If content is callable, call it to get an iterator
                iterator = content()
                for chunk in iterator:
                    if isinstance(chunk, bytes):
                        chunk = chunk.decode("utf-8", errors="replace")
                    body += chunk
            else:
                # Otherwise, treat it as an iterator
                for chunk in content:
                    if isinstance(chunk, bytes):
                        chunk = chunk.decode("utf-8", errors="replace")
                    body += chunk

        # Track closed state for writing
        self._closed = False
        self._native_response = None

        # Create headers dict if not provided
        if headers is None:
            headers = {}

        # Initialize the Response with the collected content
        super().__init__(
            status_code=status_code,
            content_type=content_type,
            body=body,
            headers=headers,
        )

        # Make sure custom headers are directly accessible via get method
        if headers:
            for key, value in headers.items():
                self._headers[key.lower()] = value

    @property
    def headers(self):
        """
        Get the response headers.

        Returns a dictionary-like object containing all headers.
        This ensures case-insensitive access to headers.
        """

        class CaseInsensitiveHeaderDict(dict):
            def get(self, key, default=None):
                return super().get(
                    key.lower() if isinstance(key, str) else key, default
                )

        return CaseInsensitiveHeaderDict(self._headers)

    def __iter__(self):
        """
        Iterate through the content.

        This allows StreamingResponse to be used as an iterator.
        """
        # Handle callables by calling them
        content = self._content() if callable(self._content) else self._content

        # Iterate through the content
        for chunk in content:
            if isinstance(chunk, str):
                chunk = chunk.encode("utf-8")
            yield chunk

    def write(self, data: Union[str, bytes]) -> None:
        """
        Write data directly to the stream.

        Args:
            data: String or bytes to write to the stream
        """
        if self._closed:
            raise RuntimeError("Cannot write to a closed StreamingResponse")

        if not self._native_response:
            raise RuntimeError("StreamingResponse not connected to a client")

        if isinstance(data, str):
            data = data.encode("utf-8")

        self._native_response.write(data)

    def close(self):
        """
        Close the streaming response.

        This marks the stream as closed and prevents further writes.
        """
        self._closed = True

    def flush(self):
        """
        Flush any buffered content to the client.

        Currently a no-op in the simplified implementation.
        """
        pass


class StreamingWriter(io.StringIO):
    """
    A file-like object for writing to a streaming response.

    This class provides a familiar file-like interface for writing to an HTTP stream,
    making it easy to adapt existing code that writes to files to use HTTP streaming.

    Example:
        ```python
        @app.get("/stream-writer")
        def stream_csv(request):
            response = StreamingResponse(content_type="text/csv")
            writer = StreamingWriter(response)

            import csv
            csv_writer = csv.writer(writer)
            for i in range(1000):
                csv_writer.writerow([f"row-{i}", i, i*i])

            writer.close()
            return response
        ```
    """

    def __init__(self, streaming_response: StreamingResponse):
        """
        Initialize a streaming writer.

        Args:
            streaming_response: The StreamingResponse to write to
        """
        super().__init__()
        self.response = streaming_response
        self._response = streaming_response
        self._closed = False

    def write(self, s):
        """Write a string to the underlying response."""
        result = super().write(s)
        if hasattr(self.response, "write"):
            self.response.write(s)
        return result

    @property
    def closed(self):
        """Check if the writer is closed."""
        return self._closed

    # Override close to update the response's body with our content
    def close(self) -> None:
        """Close the writer and update the response with the collected data."""
        if not self._closed:
            self.response.body = self.getvalue()
            self._closed = True
            super().close()


def stream_template(template: str, **context) -> StreamingResponse:
    """
    Stream a template response.

    This function renders a template and sends it as a streaming response.

    Args:
        template: Template name or path
        **context: Template rendering context

    Returns:
        StreamingResponse object

    Example:
        ```python
        @app.get("/report")
        def report(request):
            return stream_template("large_report.html", data=get_large_dataset())
        ```
    """
    try:
        from pathlib import Path

        from jinja2 import Environment, FileSystemLoader

        # Try to find templates in standard locations
        template_dirs = [
            Path.cwd() / "templates",
            Path.cwd() / "views",
            Path.cwd(),
        ]

        env = Environment(loader=FileSystemLoader(template_dirs))
        template_obj = env.get_template(template)
        content = template_obj.render(**context)

        return StreamingResponse(content=[content], content_type="text/html")
    except ImportError:
        # Jinja2 not installed
        return StreamingResponse(
            content=[
                f"<h1>Template Error</h1><p>Jinja2 is required for template rendering</p>"
            ],
            content_type="text/html",
            status_code=500,
        )
    except Exception as e:
        # Template not found or other error
        return StreamingResponse(
            content=[f"<h1>Template Error</h1><p>{str(e)}</p>"],
            content_type="text/html",
            status_code=500,
        )
