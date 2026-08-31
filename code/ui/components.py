from __future__ import annotations

import html as _html
import re as _re
from urllib.parse import quote as _quote

GROWW_GREEN = "#00D09C"
GROWW_GREEN_DEEP = "#00A67B"
GROWW_BG = "#0B0F14"
GROWW_SURFACE = "#121A20"
GROWW_TEXT = "#E9F2ED"
GROWW_MUTED = "#8FA39A"

FONT_STACK = (
    '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, '
    '"Helvetica Neue", Arial, sans-serif'
)


def _svg_data(body: str, color: str = GROWW_GREEN) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round">{body}</svg>'
    )


def _icon_img(body: str, size: int = 18, color: str = GROWW_GREEN) -> str:
    return (
        f'<img src="data:image/svg+xml,{_quote(_svg_data(body, color))}" '
        f'width="{size}" height="{size}" alt="" aria-hidden="true">'
    )


def _icon_url(body: str, color: str = GROWW_GREEN) -> str:
    return "data:image/svg+xml," + _quote(_svg_data(body, color))


_IC_TREND = _icon_img(
    '<path d="M3.5 18.5V5.5" stroke-width="2.1"/>'
    '<path d="M3.5 14.5l5.2-3.4 3.4 1.7 6.1-5.8" stroke-width="2.1"/>'
    '<circle cx="16.3" cy="8.5" r="1.9"/>',
    24,
    "#03201A",
)
_IC_CHECK = _icon_img('<path d="M5 12.5 9.5 17 19 7" stroke-width="3"/>', 14)
_IC_SOURCE = _icon_img('<path d="M7 17 17 7M9 7h8v8"/>')
_IC_WARN = _icon_img(
    '<path d="M12 3.5 21 20.5H3z"/><path d="M12 9.8v4.2"/>'
    '<circle cx="12" cy="17.1" r="0.2" fill="#E3C48D" stroke="none"/>',
    16,
    "#E3C48D",
)
_IC_SPARK = _icon_img(
    '<path d="M12 3l2 5.2 5.2 2-5.2 2L12 17.4l-2-5.2-5.2-2 5.2-2z"/>'
    '<circle cx="18.6" cy="5.6" r="1.6"/>',
    27,
)
_IC_HDFC = _icon_img(
    '<rect x="4" y="5.6" width="2.6" height="12.8" rx="1.3"/>'
    '<rect x="17.4" y="5.6" width="2.6" height="12.8" rx="1.3"/>'
    '<rect x="8.6" y="10.4" width="6.8" height="3.2" rx="1.6"/>',
    20,
    "#E5484D",
)

_HDFC_ICON_URL = _icon_url(
    '<rect x="4" y="5.6" width="2.6" height="12.8" rx="1.3"/>'
    '<rect x="17.4" y="5.6" width="2.6" height="12.8" rx="1.3"/>'
    '<rect x="8.6" y="10.4" width="6.8" height="3.2" rx="1.6"/>',
    "#E5484D",
)

_SPARKLE_DATA_URI = _icon_url(
    '<path d="M12 4l1.9 5.3L19 11.2l-5.1 1.9L12 18.4l-1.9-5.3L5 11.2'
    'l5.1-1.9z" stroke-width="1.8"/>'
)


_CSS = """
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap");

:root {
  --green: #00D09C;
  --green-deep: #00A67B;
  --bg: #0B0F14;
  --surface: #121A20;
  --surface-2: #161F27;
  --text: #E9F2ED;
  --muted: #8FA39A;
  --border: rgba(255,255,255,0.08);
  color-scheme: dark;
}

html { color-scheme: dark; }
body, .stApp { font-family: __FONT__; }

.stApp {
  background:
    radial-gradient(900px 520px at 12% -8%, rgba(0,208,156,0.09), transparent 60%),
    radial-gradient(760px 480px at 96% -8%, rgba(0,132,166,0.11), transparent 60%),
    radial-gradient(900px 560px at 50% 115%, rgba(0,208,156,0.05), transparent 62%),
    linear-gradient(180deg, #0C1117 0%, #080B0F 100%);
  background-attachment: fixed;
}
.stAppViewContainer, .stMain { background: transparent; }

.stMainBlockContainer, main .block-container {
  max-width: 900px;
  padding: 1.4rem 1rem 2rem;
  position: relative;
  z-index: 1;
}

[data-testid="stHeader"],
[data-testid="stAppHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stMainMenu"],
[data-testid="stAppDeployButton"],
[data-testid="stStatusWidget"] { display: none !important; }
.stApp footer { display: none !important; }

::selection { background: rgba(0,208,156,0.28); }
a { color: var(--green); }

.brand {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 6px 2px 16px;
}
.brand-left { display: flex; align-items: center; gap: 13px; }
.brand-mark {
  flex: 0 0 auto;
  width: 46px;
  height: 46px;
  border-radius: 14px;
  background: linear-gradient(135deg, var(--green) 0%, var(--green-deep) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #042019;
  box-shadow: 0 8px 24px rgba(0,208,156,0.28), inset 0 1px 0 rgba(255,255,255,0.25);
}
.brand-mark img { width: 26px; height: 26px; }
.brand-title {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 0.4px;
  line-height: 1.2;
  color: var(--green);
}
.brand-title span { color: var(--text); font-weight: 700; }
.brand-sub {
  margin-top: 3px;
  color: var(--muted);
  font-size: 12.5px;
  font-weight: 500;
  letter-spacing: 0.2px;
}
.brand-right {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 6px 11px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: rgba(255,255,255,0.03);
  font-size: 11.5px;
  font-weight: 600;
  color: var(--muted);
  letter-spacing: 0.3px;
  flex: 0 0 auto;
}
.live-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--green);
  box-shadow: 0 0 0 3px rgba(0,208,156,0.18);
  animation: pulse 2.2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 3px rgba(0,208,156,0.16); }
  50% { box-shadow: 0 0 0 6px rgba(0,208,156,0.05); }
}

.hero { padding: 4px 2px 2px; }
.eyebrow {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--green);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}
.eyebrow-bar { width: 18px; height: 2px; border-radius: 2px; background: var(--green); }
.headline {
  margin: 10px 0 9px;
  font-size: clamp(25px, 4.1vw, 37px);
  font-weight: 800;
  line-height: 1.08;
  letter-spacing: -0.022em;
  color: var(--text);
}
.hl-accent { color: var(--green); }
.lede {
  margin: 0;
  max-width: 58ch;
  color: var(--muted);
  font-size: 15px;
  line-height: 1.6;
}
.trust {
  display: flex;
  flex-wrap: wrap;
  gap: 9px 18px;
  margin-top: 13px;
}
.trust-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #B9C8C0;
  font-size: 12.5px;
  font-weight: 550;
}
.trust-item img { width: 13px; height: 13px; }

.notadvice {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  margin-top: 12px;
  padding: 6px 11px;
  border: 1px dashed rgba(232,198,138,0.4);
  border-radius: 999px;
  background: rgba(255,185,100,0.06);
  color: #E3C48D;
  font-size: 11.5px;
  font-weight: 600;
  letter-spacing: 0.2px;
}
.notadvice img { width: 14px; height: 14px; }

.chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 7px;
  margin: 16px 0 4px;
}
.chips-label {
  color: var(--muted);
  font-size: 11.5px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-right: 4px;
}
.chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 11px;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 999px;
  background: rgba(255,255,255,0.028);
  color: #9DB0A6;
  font-size: 12.5px;
  font-weight: 500;
  letter-spacing: 0.1px;
  line-height: 1.3;
  cursor: default;
  user-select: none;
  transition: border-color .18s ease, background .18s ease,
              box-shadow .18s ease, color .18s ease;
}
.chip:hover {
  border-color: rgba(0,208,156,0.4);
  background: rgba(0,208,156,0.06);
  box-shadow: 0 0 0 3px rgba(0,208,156,0.06);
  color: #C9E4DC;
}
.chip::before {
  content: "";
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #1E9E7C;
  margin-right: 7px;
  flex: 0 0 auto;
}

.empty-state {
  text-align: left;
  padding: 24px 2px 18px;
  animation: rise .45s ease both;
}
.empty-mark {
  width: 58px;
  height: 58px;
  margin: 0 0 18px;
  border-radius: 17px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(0,208,156,0.18), rgba(0,208,156,0.04));
  border: 1px solid rgba(0,208,156,0.28);
  color: var(--green);
  box-shadow: 0 10px 34px rgba(0,208,156,0.14);
}
.empty-mark img { width: 27px; height: 27px; }
.empty-state h2 {
  margin: 0 0 7px;
  font-size: 20px;
  font-weight: 750;
  letter-spacing: -0.01em;
  color: var(--text);
}
.empty-state p {
  margin: 0;
  max-width: 62ch;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.65;
}

.section-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 18px 2px 12px;
  color: var(--muted);
  font-size: 11.5px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.section-label::after {
  content: "";
  flex: 1;
  height: 1px;
  background: var(--border);
}

[data-testid="stBaseButton-primary"] {
  width: 100%;
  height: 104px;
  min-height: 104px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: flex-start;
  gap: 10px;
  padding: 14px 15px;
  background: rgba(255,255,255,0.028);
  border: 1px solid var(--border);
  border-radius: 16px;
  color: var(--text) !important;
  font-family: inherit;
  font-size: 13.5px;
  font-weight: 600;
  line-height: 1.4;
  text-align: left;
  position: relative;
  cursor: pointer;
  overflow: hidden;
  transition: transform .18s ease, border-color .18s ease,
              background .18s ease, box-shadow .18s ease;
}
.stButton:hover [data-testid="stBaseButton-primary"] {
  transform: translateY(-2px);
  border-color: rgba(229,72,77,0.5);
  background: rgba(229,72,77,0.08);
  box-shadow: 0 14px 34px rgba(0,0,0,0.4);
}
[data-testid="stBaseButton-primary"]::before {
  content: "";
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background-color: rgba(229,72,77,0.12);
  border: 1px solid rgba(229,72,77,0.3);
  background-image: url('__HDFC_ICO__');
  background-repeat: no-repeat;
  background-position: center;
  background-size: 20px 20px;
}
[data-testid="stBaseButton-primary"]::after {
  content: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='none' stroke='%2300D09C' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4.5 11.5 11.5 4.5M6 4.5h5.5V10'/%3E%3C/svg%3E");
  position: absolute;
  top: 12px;
  right: 14px;
  width: 14px;
  height: 14px;
  line-height: 0;
  opacity: 0;
  transform: translate(-3px, 3px);
  transition: opacity .16s ease, transform .16s ease;
}
.stButton:hover [data-testid="stBaseButton-primary"]::after {
  opacity: 1;
  transform: translate(0, 0);
}
.stButton [data-testid="stBaseButton-primary"]:focus-visible {
  outline: 2px solid var(--green);
  outline-offset: 3px;
}
.stButton [data-testid="stBaseButton-primary"] p {
  margin: 0;
  padding-right: 18px;
}

[data-testid="stBaseButton-secondary"] {
  width: 100%;
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border);
  border-radius: 999px;
  color: #C7D3CE !important;
  font-family: inherit;
  font-size: 13px;
  font-weight: 550;
  line-height: 1.3;
  cursor: pointer;
  transition: border-color .15s ease, background .15s ease,
              color .15s ease, transform .15s ease;
}
.stButton:hover [data-testid="stBaseButton-secondary"] {
  border-color: rgba(0,208,156,0.4);
  background: rgba(0,208,156,0.06);
  color: var(--green) !important;
  transform: translateY(-1px);
}
.stButton [data-testid="stBaseButton-secondary"]:focus-visible {
  outline: 2px solid var(--green);
  outline-offset: 2px;
}
.stButton [data-testid="stBaseButton-secondary"] p { margin: 0; }
.stHorizontalBlock { gap: 12px; }

.input-help {
  text-align: center;
  color: rgba(143,163,154,0.85);
  font-size: 12px;
  letter-spacing: 0.1px;
  margin: 8px 0;
}

.chat-wrap { margin-top: 18px; }

.stChatMessage {
  animation: msg-in .32s cubic-bezier(0.2, 0.7, 0.3, 1) both;
  margin-bottom: 14px;
}
.stChatMessage:last-of-type { margin-bottom: 0; }
@keyframes msg-in {
  from { opacity: 0; transform: translateY(9px); }
  to { opacity: 1; transform: none; }
}
@keyframes rise {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: none; }
}

[data-testid="stChatMessage"] {
  padding: 0;
  border-radius: 0;
  border: none;
  background: transparent;
  box-shadow: none;
}

[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
  flex-direction: row-reverse;
  justify-content: flex-start;
  align-items: center;
  max-width: 78%;
  margin-left: auto;
  background: linear-gradient(135deg, #00C28F, #00A877);
  border-radius: 17px 17px 5px 17px;
  padding: 11px 15px;
  color: #042019;
  box-shadow: 0 6px 20px rgba(0,208,156,0.16);
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageAvatarUser"] { display: none; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
  margin: 0;
  padding: 0;
  color: inherit;
  display: flex;
  align-items: center;
  min-height: 24px;
  height: auto;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] > div,
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] .stMarkdown,
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] .stMarkdown > div {
  display: flex;
  align-items: center;
  height: auto !important;
  min-height: auto !important;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] p {
  margin: 0;
  padding: 0;
  color: inherit;
  font-weight: 550;
  line-height: 1.5;
}

[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  max-width: 100%;
  background: rgba(18,26,32,0.88);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 15px 17px;
  box-shadow: 0 8px 28px rgba(0,0,0,0.26);
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageAvatarAssistant"] {
  flex: 0 0 auto;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: rgba(0,208,156,0.14);
  border: 1px solid rgba(0,208,156,0.32);
  color: var(--green);
  box-shadow: 0 0 0 4px rgba(0,208,156,0.05);
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"] {
  margin: 0;
  flex: 1 1 auto;
  min-width: 0;
  padding: 0;
  font-size: 15px;
  line-height: 1.68;
  color: #E2EAE6;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"] > *:last-child { margin-bottom: 0; }

[data-testid="stChatMessageContent"] p { margin: 0 0 8px; }
[data-testid="stChatMessageContent"] p:last-child { margin-bottom: 0; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"] .num {
  color: var(--green);
  font-weight: 800;
  font-size: 1.16em;
  letter-spacing: -0.01em;
  padding: 0 1px;
}
[data-testid="stChatMessageContent"] h1, [data-testid="stChatMessageContent"] h2,
[data-testid="stChatMessageContent"] h3 {
  color: var(--text);
  font-weight: 700;
  line-height: 1.3;
  margin: 12px 0 6px;
}
[data-testid="stChatMessageContent"] ul, [data-testid="stChatMessageContent"] ol {
  padding-left: 20px;
  margin: 0 0 8px;
}
[data-testid="stChatMessageContent"] li { margin: 3px 0; }
[data-testid="stChatMessageContent"] li:last-child { margin-bottom: 0; }
[data-testid="stChatMessageContent"] code {
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.09);
  border-radius: 6px;
  padding: 1px 6px;
  font-size: 0.86em;
}
[data-testid="stChatMessageContent"] a {
  color: var(--green);
  text-decoration: none;
  border-bottom: 1px solid rgba(0,208,156,0.35);
  transition: border-color .15s ease;
}
[data-testid="stChatMessageContent"] a:hover { border-color: var(--green); }

.sources-wrap { margin-top: 18px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.07); }
.sources-head {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--muted);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  margin-bottom: 10px;
}
.sources-head img { width: 13px; height: 13px; }
.sources-list { display: flex; flex-wrap: wrap; gap: 9px; }
.source-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 13px;
  background: rgba(0,208,156,0.05);
  border: 1px solid rgba(0,208,156,0.28);
  border-radius: 11px;
  color: var(--text);
  text-decoration: none;
  font-size: 13px;
  font-weight: 550;
  transition: border-color .15s ease, background .15s ease, color .15s ease,
              box-shadow .15s ease;
}
.source-chip:hover {
  border-color: rgba(0,208,156,0.65);
  background: rgba(0,208,156,0.1);
  color: #FFFFFF;
  box-shadow: 0 4px 14px rgba(0,208,156,0.12);
}
.source-chip:focus-visible { outline: 2px solid var(--green); outline-offset: 2px; }
.source-chip .sc-ico { display: inline-flex; color: var(--green); }
.source-chip img { width: 14px; height: 14px; }
.source-chip .sc-label { color: #7BE5C6; }
.source-chip .sc-go { color: var(--muted); font-size: 13px; margin-left: 2px; }

.updated {
  margin-top: 12px;
  color: rgba(143,163,154,0.78);
  font-size: 11.5px;
}

.warn-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding: 7px 12px;
  border: 1px dashed rgba(232,198,138,0.4);
  border-radius: 12px;
  background: rgba(255,185,100,0.06);
  color: #E3C48D;
  font-size: 13px;
  font-weight: 550;
}
.warn-chip img { width: 15px; height: 15px; flex: 0 0 auto; }

.typing { display: inline-flex; align-items: center; gap: 5px; padding: 4px 2px; }
.typing span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--green);
  opacity: 0.35;
  animation: blink 1.2s ease-in-out infinite;
}
.typing span:nth-child(2) { animation-delay: .18s; }
.typing span:nth-child(3) { animation-delay: .36s; }
@keyframes blink {
  0%, 70%, 100% { opacity: .3; transform: translateY(0); }
  35% { opacity: 1; transform: translateY(-3px); }
}

.foot {
  margin-top: 30px;
  text-align: center;
  color: rgba(143,163,154,0.72);
  font-size: 12.5px;
  line-height: 1.8;
}
.foot a { color: rgba(0,208,156,0.9); text-decoration: none; }

.stChatInputRootWrapper > div { border: none !important; background: transparent !important; box-shadow: none !important; }
[data-testid="stChatInput"] * {
  border: none !important;
  background: transparent !important;
  box-shadow: none !important;
}
[data-testid="stChatInput"] {
  position: sticky;
  bottom: 0;
  z-index: 40;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 10px;
  width: 100%;
  max-width: 720px;
  margin-left: auto;
  margin-right: auto;
  background: rgba(15,20,26,0.72);
  -webkit-backdrop-filter: blur(18px);
  backdrop-filter: blur(18px);
  border: 1px solid rgba(0,208,156,0.22);
  border-radius: 17px;
  padding: 6px 8px 6px 16px;
  box-shadow: 0 12px 40px rgba(0,0,0,0.5), 0 0 0 1px rgba(0,208,156,0.04);
  transition: border-color .18s ease, box-shadow .18s ease;
}
[data-testid="stChatInput"]:focus-within {
  border-color: rgba(0,208,156,0.55);
  box-shadow: 0 12px 40px rgba(0,0,0,0.5), 0 0 0 3px rgba(0,208,156,0.12);
}
[data-testid="stChatInput"]::before {
  content: "";
  flex: 0 0 auto;
  width: 18px;
  height: 18px;
  background: url(__SPARK__) center / contain no-repeat;
  opacity: 0.9;
  pointer-events: none;
}
[data-testid="stChatInput"] > div {
  display: flex;
  flex-direction: row;
  align-items: center;
  flex: 1 1 auto;
  min-width: 0;
  padding: 0 !important;
}
[data-testid="stChatInput"] > div > div {
  display: flex;
  flex-direction: row;
  align-items: center;
  flex: 1 1 auto;
  min-width: 0;
  padding: 0 !important;
}
[data-testid="stChatInput"] > div > div > div:first-child {
  flex: 1 1 0% !important;
  min-width: 0 !important;
  max-width: 100% !important;
  width: auto !important;
  align-items: center;
  overflow: hidden;
}
[data-testid="stChatInput"] > div > div > div:last-child {
  flex: 0 0 auto !important;
  min-width: 0 !important;
  max-width: 60px !important;
  width: auto !important;
  display: flex;
  align-items: center;
  column-gap: 4px;
  overflow: hidden;
}
[data-testid="stChatInputTextArea"] {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  font-family: inherit !important;
  font-size: 15px !important;
  line-height: 22px !important;
  color: var(--text) !important;
  caret-color: var(--green);
  text-align: left !important;
  padding: 7px 4px 7px 0 !important;
  margin: 0 !important;
  width: 100% !important;
  height: auto !important;
  min-height: 22px !important;
  max-height: 120px !important;
  flex: 1 1 auto !important;
  min-width: 0 !important;
  display: inline-block;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  resize: none !important;
  white-space: pre-wrap !important;
  word-break: break-word !important;
}
[data-testid="stChatInputTextArea"]::placeholder {
  color: #74867E !important;
  opacity: 1;
}
[data-testid="stChatInputSubmitButton"],
[data-testid="stChatInputApproveButton"] {
  flex: 0 0 auto !important;
  width: 40px !important;
  height: 40px !important;
  min-height: 40px !important;
  background: linear-gradient(135deg, #00D09C, #00A67B) !important;
  border-radius: 12px !important;
  color: #03201A !important;
  box-shadow: 0 6px 18px rgba(0,208,156,0.34) !important;
  transition: transform .15s ease, box-shadow .15s ease, filter .15s ease !important;
}
[data-testid="stChatInputSubmitButton"] > span,
[data-testid="stChatInputSubmitButton"] > div,
[data-testid="stChatInputApproveButton"] > span,
[data-testid="stChatInputApproveButton"] > div {
  padding: 0 !important;
  margin: 0 !important;
  line-height: 0 !important;
}
[data-testid="stChatInputSubmitButton"]:hover:not(:disabled),
[data-testid="stChatInputApproveButton"]:hover:not(:disabled) {
  transform: scale(1.06);
  filter: brightness(1.05);
}
[data-testid="stChatInputSubmitButton"]:disabled,
[data-testid="stChatInputApproveButton"]:disabled {
  background: rgba(0,208,156,0.28) !important;
  box-shadow: none !important;
}
[data-testid="stChatInputMicButton"] { border-radius: 12px !important; }
[data-testid="stChatInputInstructions"] { display: none; }

.stAlert {
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border);
  border-radius: 12px;
  color: var(--text);
  font-size: 13.5px;
  margin: 10px 0;
}
.stAlertTitle { color: var(--text) !important; }
.stAlertDynamicIcon { color: var(--green); }

.stExpander {
  border: none !important;
  background: rgba(255,255,255,0.03) !important;
  border-radius: 12px !important;
  margin-top: 12px;
}
.stExpander summary { font-size: 13px; color: var(--muted); }
.stExpanderDetails { font-size: 13px; color: var(--muted); }

@media (max-width: 1024px) and (min-width: 721px) {
  [data-testid="stChatInput"] { max-width: 640px; }
}

@media (max-width: 720px) {
  .stHorizontalBlock { flex-direction: column; }
  .stHorizontalBlock > div { flex: 1 1 100% !important; width: 100% !important; }
  .headline { font-size: 27px; }
  .brand-title { font-size: 17px; }
  .brand-mark { width: 42px; height: 42px; border-radius: 13px; }
  .brand-sub { font-size: 11.5px; }
  .stChatMessage { margin-bottom: 12px; }
  [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { max-width: 92%; }
  [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
    padding: 12px 13px;
    gap: 10px;
  }
  [data-testid="stChatInput"] {
    max-width: 100%;
    padding: 8px 8px 8px 14px;
    border-radius: 15px;
  }
  .stMainBlockContainer, main .block-container { padding: 1.1rem 0.8rem 2.2rem; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
  }
}
"""


def render_styles() -> None:
    import streamlit as st

    css = (
        _CSS.replace("__FONT__", FONT_STACK)
        .replace("__SPARK__", _SPARKLE_DATA_URI)
        .replace("__HDFC_ICO__", _HDFC_ICON_URL)
    )
    st.html(f"<style>{css}</style>")


def header() -> str:
    return (
        '<header class="brand">'
        '<div class="brand-left">'
        f'<div class="brand-mark">{_IC_TREND}</div>'
        '<div class="brand-text">'
        '<div class="brand-title">GROWW <span>MUTUAL FUND FAQ BOT</span></div>'
        '<div class="brand-sub">AI-powered \u00b7 Source-grounded answers</div>'
        "</div>"
        "</div>"
        '<div class="brand-right"><span class="live-dot"></span>Live</div>'
        "</header>"
    )


def render_header() -> None:
    import streamlit as st

    st.html(header())


def hero() -> str:
    return (
        '<section class="hero">'
        '<div class="eyebrow"><span class="eyebrow-bar"></span>'
        "Source-grounded Mutual Fund Assistant</div>"
        '<h1 class="headline">Clear answers. <span class="hl-accent">'
        "Directly from official fund sources.</span></h1>"
        '<p class="lede">Ask factual questions about selected HDFC mutual funds. '
        "Every answer is grounded in the official fund information and includes a source.</p>"
        '<div class="trust">'
        f'<span class="trust-item">{_IC_CHECK} Facts only</span>'
        f'<span class="trust-item">{_IC_CHECK} Official sources</span>'
        f'<span class="trust-item">{_IC_CHECK} No investment advice</span>'
        "</div>"
        f'<span class="notadvice">{_IC_WARN} Not investment advice</span>'
        "</section>"
    )


def render_hero() -> None:
    import streamlit as st

    st.html(hero())


def fund_chips(funds: tuple[str, ...]) -> str:
    items = "".join(f'<span class="chip">{_html.escape(f)}</span>' for f in funds)
    return (
        '<div class="chips">'
        '<span class="chips-label">Covering</span>'
        f"{items}"
        "</div>"
    )


def render_fund_chips(funds: tuple[str, ...]) -> None:
    import streamlit as st

    st.html(fund_chips(funds))


def empty_state() -> str:
    return (
        '<section class="empty-state">'
        f'<div class="empty-mark">{_IC_SPARK}</div>'
        "<h2>Ask about these HDFC funds</h2>"
        "<p>Type any factual question below — answers come straight from the "
        "official fund pages, with a source you can check.</p>"
        "</section>"
    )


def render_empty_state() -> None:
    import streamlit as st

    st.html(empty_state())


def _render_suggestion_row(
    questions: tuple[str, ...], label: str, button_type: str, prefix: str
) -> str | None:
    import streamlit as st

    st.markdown(f'<div class="section-label">{_html.escape(label)}</div>', unsafe_allow_html=True)
    cols = st.columns(len(questions))
    chosen: str | None = None
    for col, q in zip(cols, questions):
        if col.button(
            q,
            key=f"{prefix}_{q}",
            type=button_type,  # type: ignore[arg-type]
            use_container_width=True,
        ):
            chosen = q
    return chosen


def render_suggestion_cards(questions: tuple[str, ...]) -> str | None:
    return _render_suggestion_row(questions, "Try a question", "primary", "card")


def render_chat_prompts(questions: tuple[str, ...]) -> str | None:
    return _render_suggestion_row(questions, "Keep asking", "secondary", "chip")


def input_helper(disclaimer_notes: str = "") -> None:
    import streamlit as st

    note = f" \u00b7 {disclaimer_notes}" if disclaimer_notes else ""
    st.html(
        f'<div class="input-help">Answers are grounded in available fund documents{note}'
        " \u00b7 Enter to send \u00b7 Shift\u21b5 for a new line</div>"
    )


def typing_indicator() -> str:
    return (
        '<div class="typing" role="status" aria-label="Assistant is thinking">'
        "<span></span><span></span><span></span>"
        "</div>"
    )


def warning_chip(message: str) -> str:
    return (
        f'<div class="warn-chip" role="note">{_IC_WARN} '
        f"{_html.escape(message)}</div>"
    )


def _source_label(url: str, fund_by_url: dict[str, str]) -> str:
    if fund_by_url.get(url):
        return fund_by_url[url]
    trimmed = url.rstrip("/")
    tail = trimmed.rsplit("/", 1)[-1]
    if tail:
        return tail.replace("-", " ").title()
    from urllib.parse import urlparse

    host = urlparse(url).netloc.removeprefix("www.")
    return host


def sources(result: dict) -> str:
    url = result.get("source_url") or ""
    retrieved = result.get("retrieved") or []
    fund_by_url: dict[str, str] = {}
    for row in retrieved:
        src = row.get("source_url") or ""
        if src and (row.get("fund_name") or ""):
            fund_by_url.setdefault(src, row["fund_name"])

    ordered = [url] if url else []
    for row in retrieved:
        src = row.get("source_url") or ""
        if src not in ordered:
            ordered.append(src)
    if not ordered:
        return ""

    chips = []
    seen: set[str] = set()
    for u in ordered:
        if u in seen or len(chips) >= 3:
            continue
        seen.add(u)
        label = _source_label(u, fund_by_url)
        chips.append(
            f'<a class="source-chip" href="{_html.escape(u, quote=True)}" '
            f'target="_blank" rel="noopener noreferrer" '
            f'aria-label="Open source: {_html.escape(label, quote=True)}">'
            f'<span class="sc-ico">{_IC_SOURCE}</span>'
            f"<span class=\"sc-label\">{_html.escape(label)}</span>"
            '<span class="sc-go">\u2197</span>'
            "</a>"
        )

    return (
        '<div class="sources-wrap">'
        f'<div class="sources-head">{_IC_SOURCE} Sources</div>'
        f'<div class="sources-list">{"".join(chips)}</div>'
        "</div>"
    )


def updated_note(iso_date: str) -> str:
    return f'<div class="updated">Last updated from sources \u00b7 {_html.escape(iso_date)}</div>'


def footer() -> str:
    return (
        '<footer class="foot">'
        "Powered by Chroma, embeddings &amp; Mistral \u00b7 "
        "Facts-only, sourced from official fund pages \u00b7 "
        "<b>Not investment advice</b>"
        "</footer>"
    )


def render_footer() -> None:
    import streamlit as st

    st.html(footer())


_NUM_TOKEN = _re.compile(
    r"(?<![\w*\]\)`])((?:\u20b9|Rs\.?)\s?\d[\d,]*(?:\.\d+)?%?"
    r"|\d[\d,]*\.\d+%|\d[\d,]*%|\d[\d,]*\.\d+)(?![\w%*])"
)


def emphasize_numbers(text: str) -> str:
    """Wrap standalone numeric tokens (percentages, rupee amounts, decimals)
    in a <span class="num"> so the assistant answer's key value stands out.
    Presentational only; the underlying text is unchanged."""
    if not text:
        return text
    return _NUM_TOKEN.sub(r'<span class="num">\1</span>', text)