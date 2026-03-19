#!/usr/bin/env python3
import asyncio
import json
import os

from playwright.async_api import async_playwright


SESSION = os.environ.get("YRX_SESSIONID", "").strip()
BASE = "https://match.yuanrenxue.cn/match/10"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DEFAULT_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
YRX_UA = "yuanrenxue"

INIT = r"""
(() => {
  function patchSource(src) {
    src = String(src);
    if (src.includes("_yrxyA$") && src.trim().endsWith("})();")) {
      const idx = src.lastIndexOf("})();");
      if (idx !== -1) {
        src =
          src.slice(0, idx) +
          "window.__yrx_exports={gen:typeof _yrxyA$!=='undefined'?_yrxyA$:null,q:typeof _yrxQ9C!=='undefined'?_yrxQ9C:null,bxt:typeof _yrxBXT!=='undefined'?_yrxBXT:null,vfu:typeof _yrxvFU!=='undefined'?_yrxvFU:null};})();";
      }
    }
    return src;
  }
  const origEval = window.eval;
  window.eval = new Proxy(origEval, {
    apply(target, thisArg, args) {
      if (args.length) args[0] = patchSource(args[0]);
      return Reflect.apply(target, thisArg, args);
    },
  });
})();
"""


async def protocol_sequence(page_ua: str, req_ua_by_page: dict[int, str]) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path=CHROME,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = await browser.new_context(user_agent=page_ua)
        await ctx.add_cookies(
            [
                {
                    "name": "sessionid",
                    "value": SESSION,
                    "domain": "match.yuanrenxue.cn",
                    "path": "/",
                    "secure": True,
                    "sameSite": "Lax",
                }
            ]
        )
        page = await ctx.new_page()
        await page.add_init_script(INIT)
        await page.goto(BASE, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_function(
            "() => !!(window.__yrx_exports && window.__yrx_exports.gen)",
            timeout=20000,
        )
        await page.wait_for_timeout(6000)

        steps = []
        for page_no in range(1, 6):
            url = await page.evaluate(
                "(pageNo) => window.__yrx_exports.gen(`/api/question/10?page=${pageNo}`)",
                page_no,
            )
            req_ua = req_ua_by_page[page_no]
            response = await ctx.request.get(
                url,
                headers={
                    "User-Agent": req_ua,
                    "Referer": BASE,
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                },
            )
            text = await response.text()
            step = {
                "page": page_no,
                "url": url,
                "req_ua": req_ua,
                "status": response.status,
                "text": text,
                "cookie": await page.evaluate("document.cookie"),
            }
            try:
                parsed = json.loads(text)
            except Exception:
                parsed = None
            if parsed and isinstance(parsed, dict) and parsed.get("k", {}).get("k"):
                name, value = parsed["k"]["k"].split("|", 1)
                await page.evaluate(
                    "([name, value]) => { window[name] = parseInt(value, 10); }",
                    [name, value],
                )
                step["applied_k"] = parsed["k"]["k"]
            steps.append(step)
        await browser.close()
        return {
            "page_ua": page_ua,
            "steps": steps,
        }


async def replay_with_cookie_variants(url: str, ua: str) -> list[dict]:
    headers = {
        "User-Agent": ua,
        "Referer": BASE,
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    }
    values = ["pua", "155"] + [f"{i:x}5" for i in range(16)]
    out = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path=CHROME,
            args=["--disable-blink-features=AutomationControlled"],
        )
        for value in values:
            ctx = await browser.new_context(user_agent=ua)
            await ctx.add_cookies(
                [
                    {
                        "name": "sessionid",
                        "value": SESSION,
                        "domain": "match.yuanrenxue.cn",
                        "path": "/",
                        "secure": True,
                        "sameSite": "Lax",
                    },
                    {
                        "name": "m",
                        "value": value,
                        "domain": "match.yuanrenxue.cn",
                        "path": "/",
                        "secure": True,
                        "sameSite": "Lax",
                    },
                ]
            )
            response = await ctx.request.get(url, headers=headers)
            body = await response.text()
            out.append(
                {
                    "cookie_m": value,
                    "status": response.status,
                    "body": body,
                }
            )
            await ctx.close()
        await browser.close()
    return out


async def main():
    if not SESSION:
        raise SystemExit("Missing YRX_SESSIONID environment variable")

    all_yuanrenxue = await protocol_sequence(YRX_UA, {i: YRX_UA for i in range(1, 6)})
    default_then_switch = await protocol_sequence(
        DEFAULT_UA,
        {1: DEFAULT_UA, 2: DEFAULT_UA, 3: DEFAULT_UA, 4: DEFAULT_UA, 5: YRX_UA},
    )
    fresh_page5_url = all_yuanrenxue["steps"][-1]["url"]
    replay = await replay_with_cookie_variants(fresh_page5_url, YRX_UA)
    result = {
        "target": BASE,
        "sessionid": "<from YRX_SESSIONID>",
        "all_yuanrenxue": all_yuanrenxue,
        "default_then_switch_p5": default_then_switch,
        "fresh_page5_replay": replay,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
