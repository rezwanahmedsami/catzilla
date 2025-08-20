"""
Catzilla Streaming Response Module

This module provides a streaming response system for the Catzilla web framework.
"""

import io
import threading
import time
import uuid
import weakref
from typing import Any, Callable, Dict, Iterator, Optional, Union

from .types import Response

# Import the C streaming extension
try:
    # Try importing as installed package
    import catzilla._catzilla as _catzilla

    _HAS_C_STREAMING = hasattr(_catzilla, "_streaming") and hasattr(
        _catzilla._streaming, "connect_streaming_response"
    )
    _catzilla_streaming = _catzilla._streaming if _HAS_C_STREAMING else None
except ImportError:
    try:
        # Try importing from current directory context
        from . import _catzilla

        _HAS_C_STREAMING = hasattr(_catzilla, "_streaming") and hasattr(
            _catzilla._streaming, "connect_streaming_response"
        )
        _catzilla_streaming = _catzilla._streaming if _HAS_C_STREAMING else None
    except ImportError:
        try:
            # Try direct import
            import _catzilla

            _HAS_C_STREAMING = hasattr(_catzilla, "_streaming") and hasattr(
                _catzilla._streaming, "connect_streaming_response"
            )
            _catzilla_streaming = _catzilla._streaming if _HAS_C_STREAMING else None
        except ImportError:
            _HAS_C_STREAMING = False
            _catzilla = None
            _catzilla_streaming = None


# Global registry for streaming responses awaiting connection to C context
_streaming_responses = weakref.WeakValueDictionary()
_streaming_lock = threading.Lock()


def _register_streaming_response(
    streaming_id: str, response: "StreamingResponse"
) -> None:
    """Register a streaming response in the global registry."""
    with _streaming_lock:
        _streaming_responses[streaming_id] = response


def _get_streaming_response(streaming_id: str) -> Optional["StreamingResponse"]:
    """Get a streaming response from the global registry."""
    with _streaming_lock:
        return _streaming_responses.get(streaming_id)


def _unregister_streaming_response(streaming_id: str) -> None:
    """Unregister a streaming response from the global registry."""
    with _streaming_lock:
        _streaming_responses.pop(streaming_id, None)


# Make registry functions accessible for C extension
__all__ = [
    "StreamingResponse",
    "StreamingWriter",
    "stream_template",
    "_get_streaming_response",
    "_register_streaming_response",
    "_unregister_streaming_response",
]


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
        # Store the original content for streaming
        self._content = content
        self._content_type = content_type
        self._status_code = status_code
        self._headers = headers or {}

        # C streaming context (will be set by server when response is sent)
        self._stream_context = None
        self._is_streaming = content is not None
        self._streaming_id = None  # Unique ID for connecting to C context

        # For fallback compatibility, also create the collected response
        if not _HAS_C_STREAMING or not self._is_streaming:
            # Fallback to collecting all content
            body = self._collect_content()
        else:
            # Create a unique streaming ID for this response
            self._streaming_id = str(uuid.uuid4())
            # Mark this as a streaming response for server detection
            # Include the streaming ID so the server can connect back to this instance
            body = f"___CATZILLA_STREAMING___{self._streaming_id}___"

        # Track closed state for writing
        self._closed = False
        self._native_response = None

        # Initialize the Response with the collected content or marker
        # Pass the original headers parameter to parent (it handles None properly)
        super().__init__(
            status_code=status_code,
            content_type=content_type,
            body=body,
            headers=headers,
        )

        # Make sure custom headers are directly accessible via get method
        # Use self._headers which is set by the parent Response class
        if self._headers:
            for key, value in self._headers.items():
                # Headers are already lowercase from parent class
                pass  # No additional processing needed

        # Register this streaming response globally so server can find it
        if self._is_streaming and _HAS_C_STREAMING and self._streaming_id:
            _register_streaming_response(self._streaming_id, self)

    def _collect_content(self) -> str:
        """
        Collect all content for fallback mode when C streaming is not available.
        """
        if self._content is None:
            return ""

        body = ""
        content = self._content

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

        return body

    def is_streaming(self) -> bool:
        """
        Check if this response is using streaming.

        Returns:
            True if the response is using streaming, False otherwise
        """
        return self._is_streaming and _HAS_C_STREAMING

    def _connect_to_stream_context(self, stream_context):
        """
        Connect this response to a C streaming context.
        This is called internally by the server when setting up streaming.

        Args:
            stream_context: The C streaming context object
        """
        self._stream_context = stream_context
        self._native_response = stream_context

    def _start_streaming(self):
        """
        Start streaming the content if C streaming is available.
        This method is called by the server after headers are sent.
        """
        if not self.is_streaming() or not self._stream_context:
            return

        # Stream content directly through C core without threading
        try:
            content = self._content

            # Handle callable content
            if callable(content):
                content = content()

            # Stream the content chunk by chunk
            for chunk in content:
                if self._closed:
                    break

                if isinstance(chunk, str):
                    chunk = chunk.encode("utf-8")

                # Write to the C streaming context
                if self._stream_context:
                    self._stream_context.write(chunk)

        except Exception as e:
            # Handle errors during streaming
            error_msg = f"Streaming error: {str(e)}"
            if self._stream_context:
                self._stream_context.write(error_msg.encode("utf-8"))
        finally:
            # Always close the stream when done
            if not self._closed and self._stream_context:
                self._stream_context.close()
                self._closed = True

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

        # If we have C streaming available and connected, use it
        if self.is_streaming() and self._stream_context:
            if isinstance(data, str):
                data = data.encode("utf-8")
            self._stream_context.write(data)
        elif self._native_response:
            # Fallback to the existing native response method
            if isinstance(data, str):
                data = data.encode("utf-8")
            self._native_response.write(data)
        else:
            raise RuntimeError("StreamingResponse not connected to a client")

    def close(self):
        """
        Close the streaming response.

        This marks the stream as closed and prevents further writes.
        """
        if not self._closed:
            self._closed = True

            # Close the C streaming context if available
            if self.is_streaming() and self._stream_context:
                self._stream_context.close()

            # Unregister from global registry
            if self._streaming_id:
                _unregister_streaming_response(self._streaming_id)

            # Clean up references
            self._stream_context = None
            self._native_response = None

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
