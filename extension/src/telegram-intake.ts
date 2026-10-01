const CARD_ID = "telegram-auto-bot-intake";
let checkingPrompt = false;

function requestFromExtension(path: string, body?: unknown): Promise<{ ok: boolean; content?: string; error?: string }> {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage({ type: "telegram-auto-bot-intake", path, body }, (response) => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
        return;
      }
      resolve(response as { ok: boolean; content?: string; error?: string });
    });
  });
}

function addStyle(): void {
  if (document.getElementById(`${CARD_ID}-style`)) return;
  const style = document.createElement("style");
  style.id = `${CARD_ID}-style`;
  style.textContent = `
     #${CARD_ID}{position:fixed;z-index:2147483647;right:18px;top:18px;width:320px;padding:16px;
     color:#182230;background:#fff;border:1px solid #d0d5dd;border-radius:12px;font:14px/1.4 system-ui;
     box-shadow:0 12px 32px #0003}
    #${CARD_ID} input{box-sizing:border-box;width:100%;margin:8px 0;padding:9px;border:1px solid #98a2b3;border-radius:6px}
    #${CARD_ID} button{padding:8px 10px;margin:4px 4px 0 0;border:0;border-radius:6px;cursor:pointer}
    #${CARD_ID} .add{background:#175cd3;color:#fff} #${CARD_ID} .skip{background:#f2f4f7;color:#344054}
    #${CARD_ID} .close{float:right;background:transparent} #${CARD_ID} small{color:#667085}
  `;
  document.documentElement.append(style);
}

function showPrompt(): void {
  if (document.getElementById(CARD_ID) || !document.body) return;
  addStyle();
  const card = document.createElement("section");
  card.id = CARD_ID;

  const title = document.createElement("strong");
  title.textContent = "Add this Telegram group to your feed?";

  const close = document.createElement("button");
  close.className = "close";
  close.textContent = "×";
  close.setAttribute("aria-label", "Dismiss group prompt");
  close.onclick = () => card.remove();

  const help = document.createElement("small");
  help.textContent = "Enter the group ID yourself. This extension does not read messages or post for you.";

  const groupId = document.createElement("input");
  groupId.placeholder = "Telegram group ID (manual)";
  const urlGroup = new URL(location.href).pathname.match(/\/(?:a\/)?(-?\d{5,}|[A-Za-z][A-Za-z0-9_]{4,})$/);
  const hashGroup = location.hash.match(/(-?\d{5,}|[A-Za-z][A-Za-z0-9_]{4,})/);
  groupId.value = urlGroup?.[1] || hashGroup?.[1] || "";

  const groupName = document.createElement("input");
  groupName.placeholder = "Group name (optional)";
  const detectGroupName = () => {
    const clean = (t: string) => {
      // remove common Telegram suffixes and trailing counts like "(123)"
      return t.replace(/\s*[|—–-]\s*Telegram.*$/i, "").replace(/\s*\(\s*\d[,\d]*\s*\)\s*$/i, "").trim();
    };
    // prefer meta tags if available
    try {
      const og = document.querySelector("meta[property='og:title'], meta[name='og:title']") as HTMLMetaElement | null;
      if (og?.content && og.content.trim()) return clean(og.content.trim());
    } catch {
      /* ignore */
    }
    const selectors = [
      "header h1",
      "header h2",
      "div[role='heading']",
      ".peer-title",
      ".tg_head_peer_title",
      ".chat-title",
      ".tg_head_title",
      ".tg_head_peer_title .peer-title",
      "h1",
      "h2",
      "title",
    ];
    for (const s of selectors) {
      try {
        const el = document.querySelector(s);
        const text = el && (el.textContent || (el as HTMLInputElement).value);
        if (text && text.trim()) return clean(text.trim());
      } catch {
        // ignore selector errors
      }
    }
    return clean(document.title || "");
  };
  groupName.value = detectGroupName();

  const status = document.createElement("small");

  const add = document.createElement("button");
  add.className = "add";
  add.textContent = "Add to feed";

  const skip = document.createElement("button");
  skip.className = "skip";
  skip.textContent = "Skip this group";

  const cancelBtn = document.createElement("button");
  cancelBtn.className = "skip close-btn";
  cancelBtn.textContent = "Cancel";
  cancelBtn.onclick = () => card.remove();

  const saveChoice = async (action: "add" | "skip") => {
    const id = groupId.value.trim();
    if (!id) {
      status.textContent = "Enter the group ID to save this choice.";
      groupId.focus();
      return;
    }
    add.disabled = true;
    skip.disabled = true;
    status.textContent = "Saving…";
    try {
      const response = await requestFromExtension("/api/groups/intake", {
        group_id: id,
        group_name: groupName.value.trim(),
        source_url: location.href,
        action,
      });
      if (!response.ok) throw new Error(response.content || response.error || "Could not save group choice");
      status.textContent = action === "add" ? "Added to your feed." : "Skipped for your account.";
      window.setTimeout(() => card.remove(), 1400);
    } catch (error) {
      status.textContent = error instanceof Error ? error.message : "Could not save group choice.";
      add.disabled = false;
      skip.disabled = false;
    }
  };

  add.onclick = () => void saveChoice("add");
  skip.onclick = () => void saveChoice("skip");

  // Append elements in a clean order
  card.append(close, title, help, groupName, groupId, add, skip, cancelBtn, status);
  document.body.append(card);
}

async function showPromptIfUndecided(): Promise<void> {
  if (checkingPrompt || document.getElementById(CARD_ID)) return;
  checkingPrompt = true;
  const current = location.href;
  const pathMatch = new URL(current).pathname.match(/\/(?:a\/)?(-?\d{5,}|[A-Za-z][A-Za-z0-9_]{4,})$/);
  const hashMatch = location.hash.match(/(-?\d{5,}|[A-Za-z][A-Za-z0-9_]{4,})/);
  const groupId = pathMatch?.[1] || hashMatch?.[1];
  if (!groupId) {
    checkingPrompt = false;
    return;
  }
  try {
    const response = await requestFromExtension(
      `/api/groups/intake-status/${encodeURIComponent(groupId)}`,
    );
    const result = response.ok && response.content
      ? (JSON.parse(response.content) as { decision?: string | null })
      : null;
    if (location.href === current && !result?.decision) showPrompt();
  } catch {
    if (location.href === current) showPrompt();
  } finally {
    checkingPrompt = false;
  }
}

if (location.hostname === "web.telegram.org") {
  let previousUrl = location.href;
  window.setInterval(() => {
    if (location.href !== previousUrl) {
      previousUrl = location.href;
      document.getElementById(CARD_ID)?.remove();
      void showPromptIfUndecided();
    }
  }, 1000);
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => void showPromptIfUndecided(), { once: true });
  } else {
    void showPromptIfUndecided();
  }
}
