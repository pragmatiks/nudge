import { CheckCircle2, Circle } from "lucide-react";
import { cn } from "@/lib/utils";

interface Task {
  name: string;
  priority?: "p1" | "p2" | "p3" | "p4";
  due?: string;
  completed?: boolean;
}

interface TaskListProps {
  title?: string;
  tasks: Task[];
}

const PRIORITY_COLORS: Record<string, string> = {
  p1: "text-red-400",
  p2: "text-orange-400",
  p3: "text-blue-400",
};

export function TaskList({ props }: { props: Record<string, unknown>; onAction: unknown }) {
  const { title, tasks = [] } = props as unknown as TaskListProps;

  return (
    <div className="rounded-lg bg-white/[.04] border border-white/[.08] overflow-hidden">
      {title && (
        <div className="px-3 py-2 border-b border-white/[.06] text-[13px] font-medium text-neutral-200">
          {title}
        </div>
      )}
      <ul className="divide-y divide-white/[.04]">
        {tasks.map((task, i) => (
          <li key={i} className="flex items-start gap-2.5 px-3 py-2">
            {task.completed ? (
              <CheckCircle2 className="w-4 h-4 mt-0.5 text-green-400 shrink-0" />
            ) : (
              <Circle
                className={cn(
                  "w-4 h-4 mt-0.5 shrink-0",
                  PRIORITY_COLORS[task.priority ?? ""] || "text-neutral-500",
                )}
              />
            )}
            <div className="min-w-0 flex-1">
              <span
                className={cn(
                  "text-[13px] leading-snug",
                  task.completed ? "text-neutral-500 line-through" : "text-neutral-200",
                )}
              >
                {task.name}
              </span>
              {task.due && (
                <span className="ml-2 text-[11px] text-neutral-500">{task.due}</span>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
