import {
  isPermissionGranted,
  requestPermission,
  sendNotification,
} from "@tauri-apps/plugin-notification";
import { openUrl } from "@tauri-apps/plugin-opener";
import { readText, writeText } from "@tauri-apps/plugin-clipboard-manager";

type ToolHandler = (args: Record<string, unknown>) => Promise<Record<string, unknown>>;

const handlers: Record<string, ToolHandler> = {
  async notify(args) {
    let granted = await isPermissionGranted();
    if (!granted) {
      const permission = await requestPermission();
      granted = permission === "granted";
    }
    if (!granted) throw new Error("Notification permission denied");
    sendNotification({ title: args.title as string, body: args.body as string });
    return { sent: true };
  },

  async open_url(args) {
    await openUrl(args.url as string);
    return { opened: true };
  },

  async clipboard_write(args) {
    await writeText(args.text as string);
    return { written: true };
  },

  async clipboard_read() {
    const text = await readText();
    return { text: text ?? "" };
  },
};

export async function executeClientTool(
  name: string,
  args: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  const handler = handlers[name];
  if (!handler) throw new Error(`Unknown client tool: ${name}`);
  return handler(args);
}
