import { TaskList } from "./TaskList";
import { InfoCard } from "./InfoCard";
import { Confirm } from "./Confirm";

interface Props {
  component: string;
  props: Record<string, unknown>;
  onAction: (action: string, payload: Record<string, unknown>) => void;
}

const COMPONENTS: Record<string, React.ComponentType<{ props: Record<string, unknown>; onAction: Props["onAction"] }>> = {
  task_list: TaskList,
  info_card: InfoCard,
  confirm: Confirm,
};

export function ComponentRenderer({ component, props, onAction }: Props) {
  const Component = COMPONENTS[component];

  if (!Component) {
    return (
      <div className="px-3 py-2 rounded-lg bg-white/[.04] border border-white/[.08] text-neutral-400 text-[13px] font-mono">
        <div className="text-neutral-500 text-[11px] mb-1">Unknown component: {component}</div>
        <pre className="whitespace-pre-wrap">{JSON.stringify(props, null, 2)}</pre>
      </div>
    );
  }

  return <Component props={props} onAction={onAction} />;
}
