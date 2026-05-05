import { Info, AlertTriangle, CheckCircle2, Calendar } from "lucide-react";

interface InfoCardProps {
  title: string;
  body: string;
  icon?: "info" | "warning" | "success" | "calendar";
}

const ICONS = {
  info: <Info className="w-4 h-4 text-blue-400" />,
  warning: <AlertTriangle className="w-4 h-4 text-amber-400" />,
  success: <CheckCircle2 className="w-4 h-4 text-green-400" />,
  calendar: <Calendar className="w-4 h-4 text-purple-400" />,
};

export function InfoCard({ props }: { props: Record<string, unknown>; onAction: unknown }) {
  const { title, body, icon } = props as unknown as InfoCardProps;

  return (
    <div className="rounded-lg bg-white/[.04] border border-white/[.08] px-3.5 py-2.5">
      <div className="flex items-center gap-2 mb-1.5">
        {icon && ICONS[icon]}
        <span className="text-[13px] font-medium text-neutral-200">{title}</span>
      </div>
      <p className="text-[13px] leading-relaxed text-neutral-400 whitespace-pre-wrap">{body}</p>
    </div>
  );
}
