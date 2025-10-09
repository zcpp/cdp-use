"""Resize a headful Chromium window via the Chrome DevTools Protocol.

Usage
-----
1. Start Chrome/Chromium in **headful** mode with remote debugging enabled, e.g.:

   ````bash
   chromium --remote-debugging-port=9222
   ````

2. Find the DevTools websocket URL from ``http://localhost:9222/json/version``.
3. Run this sample to resize the window:

   ````bash
   python samples/resize_window.py ws://127.0.0.1:9222/devtools/browser/<id> 1280 720
   ````

Optional ``left`` and ``top`` arguments move the window in addition to resizing it.
"""

from __future__ import annotations

import asyncio
import sys
from typing import Optional

from cdp_use.client import CDPClient


async def resize_window(
    devtools_ws_url: str,
    width: int,
    height: int,
    left: Optional[int] = None,
    top: Optional[int] = None,
) -> None:
    """Connect to a browser target and change its window bounds."""
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

        window_info = await client.send.Browser.getWindowForTarget(
            {"targetId": page_target["targetId"]}
        )
        window_id = window_info["windowId"]

        bounds: dict[str, int] = {"width": width, "height": height}
        if left is not None:
            bounds["left"] = left
        if top is not None:
            bounds["top"] = top

        await client.send.Browser.setWindowBounds(
            {"windowId": window_id, "bounds": bounds}
        )

        print(
            f"Resized window {window_id} to width={bounds.get('width')} "
            f"height={bounds.get('height')} left={bounds.get('left')} top={bounds.get('top')}"
        )


def parse_args(argv: list[str]) -> tuple[str, int, int, Optional[int], Optional[int]]:
    if len(argv) < 4:
        raise SystemExit(
            "Usage: python samples/resize_window.py <devtools-ws-url> <width> <height> [left] [top]"
        )

    devtools_ws_url = argv[1]
    width = int(argv[2])
    height = int(argv[3])
    left = int(argv[4]) if len(argv) > 4 else None
    top = int(argv[5]) if len(argv) > 5 else None
    return devtools_ws_url, width, height, left, top


async def main() -> None:
    devtools_ws_url, width, height, left, top = parse_args(sys.argv)
    await resize_window(devtools_ws_url, width, height, left, top)


if __name__ == "__main__":
    asyncio.run(main())
