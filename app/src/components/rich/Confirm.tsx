import { Button } from "@/components/ui/button";

interface ConfirmAction {
  label: string;
  value: string;
}

interface ConfirmProps {
  title: string;
  message: string;
  actions: ConfirmAction[];
}

export function Confirm({
  props,
  onAction,
}: {
  props: Record<string, unknown>;
  onAction: (action: string, payload: Record<string, unknown>) => void;
}) {
  const { title, message, actions } = props as unknown as ConfirmProps;

  return (
    <div className="rounded-lg bg-white/[.04] border border-white/[.08] px-3.5 py-2.5">
      <div className="text-[13px] font-medium text-neutral-200 mb-1">{title}</div>
      <p className="text-[13px] leading-relaxed text-neutral-400 mb-3">{message}</p>
      <div className="flex gap-2">
        {actions.map((action, i) => (
          <Button
            key={action.value}
            size="sm"
            variant={i === actions.length - 1 ? "default" : "secondary"}
            onClick={() => onAction("confirm", { value: action.value })}
          >
            {action.label}
          </Button>
        ))}
      </div>
    </div>
  );
}
