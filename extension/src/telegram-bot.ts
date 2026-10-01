type BotActionRequest =
  | { type: "telegram-auto-bot-action"; action: "count_messages" }
  | { type: "telegram-auto-bot-action"; action: "delete_previous" }
  | { type: "telegram-auto-bot-action"; action: "insert_and_send"; content: string }
  | { type: "telegram-auto-bot-action"; action: "perform_post"; content: string; minMessages: number };

type BotActionResponse = { ok: boolean; reason?: string; details?: unknown };

function findMessageElements(): Element[] {
  const candidates = Array.from(document.querySelectorAll("div[role=article], div.message, li[role=listitem], div[data-peer-id] div.message"));
  if (candidates.length) return candidates as Element[];
  // fallback: any div with some text inside message list
  return Array.from(document.querySelectorAll("div")).filter((el) => el.textContent && el.textContent.trim().length > 0);
}

function findComposer(): HTMLElement | null {
  // common Telegram web composer targets
  const selectors = [
    "div.composer_rich_textarea[contenteditable=true]",
    "div[contenteditable=plaintext-only]",
    "div[contenteditable=true]",
    "textarea",
    "input[type=text]",
  ];
  for (const s of selectors) {
    const el = document.querySelector<HTMLElement>(s);
    if (el) return el;
  }
  return null;
}

function findSendButton(): HTMLElement | null {
  const candidates = [
    "button[aria-label=Send]",
    "button.send",
    "button[type=submit]",
    "div[aria-label=Send]",
  ];
  for (const s of candidates) {
    const el = document.querySelector<HTMLElement>(s);
    if (el) return el;
  }
  // try to find a button in composer area
  const composer = findComposer();
  if (composer) {
    const parent = composer.parentElement;
    if (parent) {
      const btn = parent.querySelector<HTMLElement>("button");
      if (btn) return btn;
    }
  }
  return null;
}

async function countMessagesSinceLastAppPost(): Promise<number> {
  try {
    const msgs = findMessageElements();
    // find last app-post marker: we look for messages authored by "you" or containing the marker "[app-post]"
    let lastAppIndex = -1;
    for (let i = msgs.length - 1; i >= 0; i--) {
      const t = (msgs[i].textContent || "").toLowerCase();
      if (t.includes("[app-post]") || t.includes("you") || t.includes("you:")) {
        lastAppIndex = i;
        break;
      }
    }
    if (lastAppIndex === -1) return msgs.length; // treat whole list as new
    return msgs.length - 1 - lastAppIndex;
  } catch (err) {
    return -1;
  }
}

async function deletePreviousAppPost(): Promise<boolean> {
  try {
    const msgs = findMessageElements();
    for (let i = msgs.length - 1; i >= 0; i--) {
      const el = msgs[i];
      const t = (el.textContent || "").toLowerCase();
      if (t.includes("[app-post]") || t.includes("you") || t.includes("you:")) {
        // try to find menu button inside this message and click delete
        const menu = el.querySelector<HTMLElement>("button[aria-label*='More'], button[aria-label*='Menu'], .message__actions, .menu, .dropdown");
        if (menu) {
          menu.click();
          await new Promise((r) => setTimeout(r, 300));
          // look for delete option
          const del = Array.from(document.querySelectorAll("button, div[role='menuitem']")).find((n) => /delete/i.test(n.textContent || "")) as HTMLElement | undefined;
          if (del) {
            del.click();
            await new Promise((r) => setTimeout(r, 300));
            const confirm = Array.from(document.querySelectorAll("button")).find((n) => /delete/i.test(n.textContent || "")) as HTMLElement | undefined;
            if (confirm) {
              confirm.click();
              return true;
            }
          }
        }
        // fallback: remove element from DOM (non-persistent)
        el.remove();
        return true;
      }
    }
    return false;
  } catch (err) {
    return false;
  }
}

async function insertAndSend(content: string): Promise<boolean> {
  try {
    const composer = findComposer();
    if (!composer) return false;
    if (composer instanceof HTMLInputElement || composer instanceof HTMLTextAreaElement) {
      composer.value = content + " [app-post]";
      composer.dispatchEvent(new Event("input", { bubbles: true }));
    } else {
      composer.focus();
      // for contenteditable
      composer.textContent = content + " [app-post]";
      composer.dispatchEvent(new InputEvent("input", { bubbles: true }));
    }
    await new Promise((r) => setTimeout(r, 150));
    const send = findSendButton();
    if (send) {
      send.click();
      return true;
    }
    // try Enter key
    const ev = new KeyboardEvent("keydown", { bubbles: true, cancelable: true, key: "Enter" });
    composer.dispatchEvent(ev);
    return true;
  } catch (err) {
    return false;
  }
}

chrome.runtime.onMessage.addListener((message: unknown, sender, sendResponse) => {
  console.debug("[telegram-bot] received message", message, { sender });
  const req = message as BotActionRequest;
  (async () => {
    if (!req || req.type !== "telegram-auto-bot-action") {
      sendResponse({ ok: false, reason: "unsupported" } as BotActionResponse);
      return;
    }
    if (req.action === "count_messages") {
      const count = await countMessagesSinceLastAppPost();
      const resp = { ok: true, details: { count } } as BotActionResponse;
      console.debug("[telegram-bot] count_messages ->", resp);
      sendResponse(resp);
      return;
    }
    if (req.action === "delete_previous") {
      const ok = await deletePreviousAppPost();
      const resp = { ok, reason: ok ? undefined : "not_found" } as BotActionResponse;
      console.debug("[telegram-bot] delete_previous ->", resp);
      sendResponse(resp);
      return;
    }
    if (req.action === "insert_and_send") {
      const ok = await insertAndSend(req.content);
      const resp = { ok, reason: ok ? undefined : "failed" } as BotActionResponse;
      console.debug("[telegram-bot] insert_and_send ->", resp);
      sendResponse(resp);
      return;
    }
    if (req.action === "perform_post") {
      const count = await countMessagesSinceLastAppPost();
      if (count < 0) {
        sendResponse({ ok: false, reason: "count_failed" } as BotActionResponse);
        return;
      }
      if (count < req.minMessages) {
        sendResponse({ ok: false, reason: "not_enough_messages", details: { count } } as BotActionResponse);
        return;
      }
      // delete previous
      await deletePreviousAppPost().catch(() => undefined);
      const posted = await insertAndSend(req.content);
      const resp = { ok: posted, reason: posted ? undefined : "send_failed" } as BotActionResponse;
      console.debug("[telegram-bot] perform_post ->", resp);
      sendResponse(resp);
      return;
    }
    sendResponse({ ok: false, reason: "unknown_action" } as BotActionResponse);
  })();
  return true;
});

// Expose a small global for debugging
(window as any).__telegram_auto_bot = { countMessagesSinceLastAppPost, deletePreviousAppPost, insertAndSend };
