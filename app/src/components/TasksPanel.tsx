import { useMemo, useState, type KeyboardEvent } from "react";
import { CheckCircle2, Circle, Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { useDataStore } from "../store/dataStore";
import type { DataOpType, Task } from "../types/protocol";

interface Props {
  sendDataOp: (type: DataOpType, payload: Record<string, unknown>) => void;
}

const PRIORITY_RING: Record<number, string> = {
  1: "text-red-400",
  2: "text-orange-400",
  3: "text-blue-400",
};

function formatDue(due: string | null): string | null {
  if (!due) return null;
  // Date-only (YYYY-MM-DD) is rendered as a local date — bypass `new Date()`
  // which would parse it as UTC midnight and drift in non-UTC timezones.
  const dateOnly = /^\d{4}-\d{2}-\d{2}$/.test(due);
  if (dateOnly) {
    const [y, m, day] = due.split("-").map(Number);
    return new Date(y, m - 1, day).toLocaleString("en-GB", {
      month: "short",
      day: "numeric",
    });
  }
  const d = new Date(due);
  if (isNaN(d.getTime())) return due;
  const isMidnight = d.getHours() === 0 && d.getMinutes() === 0;
  return d.toLocaleString("en-GB", {
    month: "short",
    day: "numeric",
    ...(isMidnight ? {} : { hour: "2-digit", minute: "2-digit", hour12: false }),
  });
}

export function TasksPanel({ sendDataOp }: Props) {
  const tasks = useDataStore((s) => s.tasks);
  const [draft, setDraft] = useState("");

  const { active, completed } = useMemo(() => {
    const a: Task[] = [];
    const c: Task[] = [];
    for (const t of tasks) (t.completed ? c : a).push(t);
    return { active: a, completed: c };
  }, [tasks]);

  const submit = () => {
    const title = draft.trim();
    if (!title) return;
    sendDataOp("task_create", { title });
    setDraft("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="flex flex-col h-full min-h-0">
      <ScrollArea className="flex-1 min-h-0">
        <div className="px-3 py-2">
          {tasks.length === 0 && (
            <div className="text-center text-neutral-500 text-[14px] mt-12">
              No tasks yet. Add one below.
            </div>
          )}

          {active.length > 0 && (
            <ul className="flex flex-col gap-0.5">
              {active.map((task) => (
                <TaskRow key={task.id} task={task} sendDataOp={sendDataOp} />
              ))}
            </ul>
          )}

          {completed.length > 0 && (
            <>
              <div className="px-1 mt-4 mb-1 text-[11px] uppercase tracking-wide text-neutral-600">
                Completed
              </div>
              <ul className="flex flex-col gap-0.5 opacity-60">
                {completed.map((task) => (
                  <TaskRow key={task.id} task={task} sendDataOp={sendDataOp} />
                ))}
              </ul>
            </>
          )}
        </div>
      </ScrollArea>

      <div className="shrink-0 flex gap-2 px-3 py-2 border-t border-white/[.06]">
        <Textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Add a task..."
          rows={1}
          className="flex-1 min-h-9 max-h-32 rounded-lg border-white/[.08] text-[14px] resize-none bg-white/[.04] text-neutral-200 placeholder:text-neutral-500 focus-visible:ring-white/[.12]"
        />
        <Button
          size="icon"
          variant="ghost"
          onClick={submit}
          disabled={!draft.trim()}
          className="rounded-lg shrink-0 text-neutral-400 hover:text-neutral-200 hover:bg-white/[.06] disabled:opacity-30"
          aria-label="Add task"
        >
          <Plus className="size-4" />
        </Button>
      </div>
    </div>
  );
}

function TaskRow({ task, sendDataOp }: { task: Task } & Props) {
  const toggle = () =>
    sendDataOp("task_complete", { id: task.id, completed: !task.completed });
  const remove = () => sendDataOp("task_delete", { id: task.id });
  const due = formatDue(task.due);

  return (
    <li className="group flex items-start gap-2.5 px-2 py-2 rounded-md hover:bg-white/[.03]">
      <Button
        size="icon-xs"
        variant="ghost"
        onClick={toggle}
        className="mt-0 shrink-0 size-[22px] hover:bg-transparent"
        aria-label={task.completed ? "Mark incomplete" : "Mark complete"}
      >
        {task.completed ? (
          <CheckCircle2 className="size-[18px] text-green-400" />
        ) : (
          <Circle
            className={cn(
              "size-[18px]",
              PRIORITY_RING[task.priority] || "text-neutral-500",
            )}
          />
        )}
      </Button>
      <div className="min-w-0 flex-1">
        <div
          className={cn(
            "text-[14px] leading-snug",
            task.completed ? "text-neutral-500 line-through" : "text-neutral-200",
          )}
        >
          {task.title}
        </div>
        {(task.notes || due) && (
          <div className="mt-0.5 flex items-center gap-2 text-[12px] text-neutral-500">
            {due && <span>{due}</span>}
            {task.notes && <span className="truncate">{task.notes}</span>}
          </div>
        )}
      </div>
      <Button
        size="icon-xs"
        variant="ghost"
        onClick={remove}
        className="opacity-0 group-hover:opacity-100 shrink-0 size-7 text-neutral-500 hover:text-red-400 hover:bg-white/[.04]"
        aria-label="Delete task"
      >
        <Trash2 className="size-3.5" />
      </Button>
    </li>
  );
}
