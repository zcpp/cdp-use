"""Display custom HTML in a blank page using the Chrome DevTools Protocol.

Usage
-----
1. Start Chrome/Chromium in headful mode with remote debugging enabled, e.g.:

   ````bash
   chromium --remote-debugging-port=9222
   ````

2. Find the DevTools websocket URL from ``http://localhost:9222/json/version``.
3. Run this sample to navigate a page to ``about:blank`` and inject HTML content:

   ````bash
   python samples/display_html.py ws://127.0.0.1:9222/devtools/browser/<id> '<h1>Hello from CDP!</h1>'
   ````

   To load HTML from a file instead, pass ``--html-file path/to/file.html`` and omit the
   inline HTML argument.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional

from cdp_use.client import CDPClient

DEFAULT_HTML = """<!doctype html>\n<html>\n  <head>\n    <meta charset=\"utf-8\">\n    <title>CDP HTML Injection Sample</title>\n    <style>body { font-family: system-ui, sans-serif; padding: 2rem; }</style>\n  </head>\n  <body>\n    <h1>Success!</h1>\n    <p>This content was set via <code>Page.setDocumentContent</code>.</p>\n  </body>\n</html>\n"""


async def display_html(devtools_ws_url: str, html: str) -> None:
    """Navigate to a blank page and replace its contents with the provided HTML."""
    async with CDPClient(devtools_ws_url) as client:
        targets = await client.send.Target.getTargets()
        page_target = next(
            (target for target in targets["targetInfos"] if target["type"] == "page"),
            None,
        )
        if page_target is None:
            raise RuntimeError(
                "No page targets are available. Open a tab in the headful browser first."
            )

        attach_result = await client.send.Target.attachToTarget(
            {"targetId": page_target["targetId"], "flatten": True}
        )
        session_id: Optional[str] = attach_result.get("sessionId")
        if not session_id:
            raise RuntimeError("Failed to attach to the page target.")

        await client.send.Page.enable(session_id=session_id)

        navigate_result = await client.send.Page.navigate(
            {"url": "about:blank"}, session_id=session_id
        )

        error_text = navigate_result.get("errorText")
        if error_text:
            raise RuntimeError(f"Navigation to about:blank failed: {error_text}")

        frame_id = navigate_result.get("frameId")
        if not frame_id:
            raise RuntimeError("The navigation response did not include a frameId.")

        await client.send.Page.setDocumentContent(
            {"frameId": frame_id, "html": html},
            session_id=session_id,
        )

        print(f"Updated frame {frame_id} with provided HTML content.")


def parse_args(argv: list[str]) -> tuple[str, str]:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("devtools_ws_url", help="The browser-level DevTools websocket URL.")
    parser.add_argument(
        "html",
        nargs="?",
        help="HTML markup to render inside the blank page. Defaults to a sample snippet.",
    )
    parser.add_argument(
        "--html-file",
        dest="html_file",
        type=Path,
        help="Path to a file containing HTML markup. Overrides the inline HTML argument.",
    )
    args = parser.parse_args(argv[1:])

    if args.html and args.html_file:
        parser.error("Provide either inline HTML or --html-file, not both.")

    if args.html_file:
        html = args.html_file.read_text(encoding="utf-8")
    else:
        html = args.html if args.html is not None else DEFAULT_HTML

    return args.devtools_ws_url, html


async def main() -> None:
    devtools_ws_url, html = parse_args(sys.argv)
    await display_html(devtools_ws_url, html)


if __name__ == "__main__":
    asyncio.run(main())
