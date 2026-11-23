import React, { useCallback, useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { AlertTriangle, Info, Loader2 } from "lucide-react";

import { GLOSSARY, GlossaryKey } from "../lib/glossary";
import { signClass, signed } from "../lib/format";

const cx = (...c: Array<string | false | null | undefined>) => c.filter(Boolean).join(" ");

/* ------------------------------------------------------------------ Button */

type ButtonVariant = "primary" | "secondary" | "ghost" | "accent";
type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: React.ReactNode;
  iconOnly?: boolean;
  loading?: boolean;
}

export function buttonClass(variant: ButtonVariant = "secondary", size: ButtonSize = "md", iconOnly = false) {
  return cx("btn", `btn-${variant}`, size !== "md" && `btn-${size}`, iconOnly && "btn-icon");
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "secondary", size = "md", icon, iconOnly, loading, className, children, disabled, type, ...rest }, ref) => (
    <button
      ref={ref}
      type={type ?? "button"}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={cx(buttonClass(variant, size, iconOnly), className)}
      {...rest}
    >
      {loading ? <Loader2 className="animate-spin" aria-hidden /> : icon}
      {!iconOnly && children}
    </button>
  )
);
Button.displayName = "Button";

/* ---------------------------------------------------------- Form controls */

export const Select = React.forwardRef<HTMLSelectElement, React.SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, children, ...rest }, ref) => (
    <select ref={ref} className={cx("control control-select", className)} {...rest}>
      {children}
    </select>
  )
);
Select.displayName = "Select";

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...rest }, ref) => <input ref={ref} className={cx("control", className)} {...rest} />
);
Input.displayName = "Input";

export const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...rest }, ref) => <textarea ref={ref} className={cx("control control-textarea", className)} {...rest} />
);
Textarea.displayName = "Textarea";

interface FieldProps {
  label: React.ReactNode;
  term?: GlossaryKey;
  hint?: React.ReactNode;
  error?: React.ReactNode;
  htmlFor?: string;
  className?: string;
  children: React.ReactNode;
}

export const Field: React.FC<FieldProps> = ({ label, term, hint, error, htmlFor, className, children }) => (
  <div className={className}>
    <label className="field-label" htmlFor={htmlFor}>
      {label}
      {term && <HelpTip term={term} />}
    </label>
    {children}
    {error ? (
      <p className="mt-1 text-2xs text-truffle dark:text-truffle-soft" role="alert">
        {error}
      </p>
    ) : (
      hint && <p className="field-hint">{hint}</p>
    )}
  </div>
);

export const Checkbox = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement> & { label: React.ReactNode; description?: React.ReactNode }
>(({ label, description, className, ...rest }, ref) => (
  <label className={cx("flex items-start gap-2.5 cursor-pointer select-none", className)}>
    <input ref={ref} type="checkbox" className="checkbox mt-0.5" {...rest} />
    <span className="text-[13px] leading-snug text-abyssal dark:text-palladian">
      {label}
      {description && <span className="block text-2xs text-oatmeal-dark dark:text-oatmeal/80 mt-0.5">{description}</span>}
    </span>
  </label>
));
Checkbox.displayName = "Checkbox";

/* --------------------------------------------------------- Segmented tabs */

interface SegmentedProps<T extends string> {
  items: Array<{ value: T; label: React.ReactNode }>;
  value: T;
  onChange: (v: T) => void;
  label: string;
  variant?: "segmented" | "tabs";
  className?: string;
}

export function Segmented<T extends string>({ items, value, onChange, label, variant = "segmented", className }: SegmentedProps<T>) {
  const refs = useRef<Array<HTMLButtonElement | null>>([]);
  const onKey = (e: React.KeyboardEvent, idx: number) => {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    e.preventDefault();
    const next = (idx + (e.key === "ArrowRight" ? 1 : -1) + items.length) % items.length;
    onChange(items[next].value);
    refs.current[next]?.focus();
  };
  return (
    <div role="tablist" aria-label={label} className={cx(variant === "tabs" ? "tabrow" : "segmented", className)}>
      {items.map((it, i) => (
        <button
          key={it.value}
          ref={(el) => (refs.current[i] = el)}
          type="button"
          role="tab"
          aria-selected={it.value === value}
          tabIndex={it.value === value ? 0 : -1}
          onClick={() => onChange(it.value)}
          onKeyDown={(e) => onKey(e, i)}
          className={variant === "tabs" ? "tab" : "segmented-item"}
        >
          {it.label}
        </button>
      ))}
    </div>
  );
}

/* ---------------------------------------------------------------- Tooltip */

function useFloating() {
  const anchor = useRef<HTMLElement | null>(null);
  const [pos, setPos] = useState<{ top: number; left: number; above: boolean } | null>(null);
  const show = useCallback(() => {
    const el = anchor.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const width = 280;
    const left = Math.min(Math.max(8, r.left + r.width / 2 - width / 2), window.innerWidth - width - 8);
    const above = r.bottom + 140 > window.innerHeight;
    setPos({ top: above ? r.top - 8 : r.bottom + 8, left, above });
  }, []);
  const hide = useCallback(() => setPos(null), []);
  useEffect(() => {
    if (!pos) return;
    const close = () => setPos(null);
    window.addEventListener("scroll", close, true);
    window.addEventListener("resize", close);
    return () => {
      window.removeEventListener("scroll", close, true);
      window.removeEventListener("resize", close);
    };
  }, [pos]);
  return { anchor, pos, show, hide };
}

const TooltipBubble: React.FC<{ id: string; pos: { top: number; left: number; above: boolean }; children: React.ReactNode }> = ({ id, pos, children }) =>
  createPortal(
    <div
      id={id}
      role="tooltip"
      style={{ top: pos.top, left: pos.left, width: 280, transform: pos.above ? "translateY(-100%)" : undefined }}
      className="fixed z-50 rounded-md border border-blue-fantastic-light bg-abyssal px-3 py-2 text-xs leading-relaxed text-palladian shadow-[0_6px_20px_rgba(19,28,37,0.25)] pointer-events-none"
    >
      {children}
    </div>,
    document.body
  );

/** Inline financial term with a dotted underline and a plain-English explanation. */
export const Term: React.FC<{ k: GlossaryKey; children: React.ReactNode; className?: string }> = ({ k, children, className }) => {
  const id = useId();
  const { anchor, pos, show, hide } = useFloating();
  return (
    <>
      <span
        ref={(el) => (anchor.current = el)}
        tabIndex={0}
        aria-describedby={pos ? id : undefined}
        onMouseEnter={show}
        onMouseLeave={hide}
        onFocus={show}
        onBlur={hide}
        className={cx(
          "cursor-help underline decoration-dotted decoration-oatmeal-dark/70 dark:decoration-oatmeal/50 underline-offset-[3px] rounded-sm",
          className
        )}
      >
        {children}
      </span>
      {pos && <TooltipBubble id={id} pos={pos}>{GLOSSARY[k]}</TooltipBubble>}
    </>
  );
};

/** Small "?" affordance next to form labels. */
export const HelpTip: React.FC<{ term: GlossaryKey }> = ({ term }) => {
  const id = useId();
  const { anchor, pos, show, hide } = useFloating();
  return (
    <>
      <button
        type="button"
        ref={(el) => (anchor.current = el)}
        aria-label="What does this mean?"
        aria-describedby={pos ? id : undefined}
        onMouseEnter={show}
        onMouseLeave={hide}
        onFocus={show}
        onBlur={hide}
        onClick={(e) => {
          e.preventDefault();
          pos ? hide() : show();
        }}
        className="inline-grid place-items-center w-3.5 h-3.5 rounded-full border border-oatmeal-dark/50 dark:border-oatmeal/40 text-[9px] font-semibold leading-none text-oatmeal-dark dark:text-oatmeal hover:border-blue-fantastic hover:text-blue-fantastic dark:hover:border-palladian dark:hover:text-palladian"
      >
        ?
      </button>
      {pos && <TooltipBubble id={id} pos={pos}>{GLOSSARY[term]}</TooltipBubble>}
    </>
  );
};

/* --------------------------------------------------------------- Surfaces */

interface PanelProps {
  title?: React.ReactNode;
  sub?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
  bodyClassName?: string;
  children: React.ReactNode;
  as?: "section" | "div" | "aside" | "article";
}

export const Panel: React.FC<PanelProps> = ({ title, sub, actions, className, bodyClassName, children, as = "section" }) => {
  const Tag = as;
  return (
    <Tag className={cx("panel", className)}>
      {(title || actions) && (
        <header className="panel-head">
          <div className="min-w-0">
            {title && <h2 className="panel-title">{title}</h2>}
            {sub && <p className="panel-sub">{sub}</p>}
          </div>
          {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
        </header>
      )}
      <div className={cx(bodyClassName ?? "p-4")}>{children}</div>
    </Tag>
  );
};

export const PageHeader: React.FC<{ title: string; description?: React.ReactNode; actions?: React.ReactNode }> = ({ title, description, actions }) => (
  <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-3 pb-1">
    <div className="min-w-0 max-w-3xl">
      <h1 className="text-[22px] leading-tight font-semibold tracking-[-0.01em] text-abyssal dark:text-palladian">{title}</h1>
      {description && <p className="mt-1.5 text-sm leading-relaxed text-blue-fantastic/80 dark:text-oatmeal">{description}</p>}
    </div>
    {actions && <div className="flex flex-wrap items-end gap-2.5">{actions}</div>}
  </div>
);

/** Filter / toolbar row. Children are Field elements laid out on one line when space allows. */
export const Toolbar: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className }) => (
  <div className={cx("panel px-4 py-3 flex flex-wrap items-end gap-3", className)}>{children}</div>
);

interface StatProps {
  label: React.ReactNode;
  term?: GlossaryKey;
  value: React.ReactNode;
  sub?: React.ReactNode;
  valueClassName?: string;
  className?: string;
}

export const Stat: React.FC<StatProps> = ({ label, term, value, sub, valueClassName, className }) => (
  <div className={cx("min-w-0", className)}>
    <div className="text-xs text-oatmeal-dark dark:text-oatmeal flex items-center gap-1">
      {term ? <Term k={term}>{label}</Term> : label}
    </div>
    <div className={cx("mt-1 text-xl font-semibold tabular tracking-[-0.01em] text-abyssal dark:text-palladian", valueClassName)}>{value}</div>
    {sub && <div className="mt-0.5 text-xs text-oatmeal-dark dark:text-oatmeal/80 tabular">{sub}</div>}
  </div>
);

/** A row of stats sharing one surface, divided by 1px rules rather than separate cards. */
export const StatRow: React.FC<{ children: React.ReactNode; className?: string; cols?: string }> = ({ children, className, cols }) => (
  <div
    className={cx(
      "grid gap-px overflow-hidden rounded-md border border-oatmeal/80 bg-oatmeal/60 dark:border-blue-fantastic dark:bg-blue-fantastic",
      cols ?? "grid-cols-2 md:grid-cols-3 xl:grid-cols-6",
      "[&>*]:bg-palladian-light dark:[&>*]:bg-abyssal-mid [&>*]:px-4 [&>*]:py-3.5",
      className
    )}
  >
    {children}
  </div>
);

export const Signed: React.FC<{ value: number | null | undefined; digits?: number; unit?: string; className?: string }> = ({ value, digits = 2, unit = "", className }) => (
  <span className={cx("tabular", signClass(value), className)}>{signed(value, digits, unit)}</span>
);

/* ------------------------------------------------------------ Feedback UI */

export const Notice: React.FC<{ tone?: "info" | "warn"; title?: React.ReactNode; children: React.ReactNode; className?: string }> = ({ tone = "info", title, children, className }) => {
  const Icon = tone === "warn" ? AlertTriangle : Info;
  return (
    <div
      className={cx(
        "flex gap-3 rounded-md border px-4 py-3 text-[13px] leading-relaxed",
        tone === "warn"
          ? "border-truffle/30 bg-truffle/[0.06] text-abyssal dark:text-palladian dark:border-truffle-soft/30"
          : "border-oatmeal/80 bg-palladian-light text-abyssal dark:bg-abyssal-mid dark:border-blue-fantastic dark:text-palladian",
        className
      )}
    >
      <Icon className={cx("w-4 h-4 shrink-0 mt-0.5", tone === "warn" ? "text-truffle dark:text-truffle-soft" : "text-blue-fantastic dark:text-oatmeal")} aria-hidden />
      <div className="min-w-0">
        {title && <div className="font-medium mb-0.5">{title}</div>}
        <div className="text-blue-fantastic/90 dark:text-oatmeal">{children}</div>
      </div>
    </div>
  );
};

export const EmptyState: React.FC<{ title: string; children?: React.ReactNode; action?: React.ReactNode; className?: string }> = ({ title, children, action, className }) => (
  <div className={cx("py-10 px-4 text-center", className)}>
    <p className="text-sm font-medium text-abyssal dark:text-palladian">{title}</p>
    {children && <p className="mt-1 text-[13px] text-oatmeal-dark dark:text-oatmeal max-w-md mx-auto">{children}</p>}
    {action && <div className="mt-4 flex justify-center">{action}</div>}
  </div>
);

export const ErrorState: React.FC<{ error: unknown; onRetry?: () => void; what?: string }> = ({ error, onRetry, what = "this data" }) => (
  <EmptyState
    title={`Couldn't load ${what}`}
    action={onRetry && <Button size="sm" onClick={onRetry}>Try again</Button>}
  >
    {error instanceof Error ? error.message : "The server did not respond."} Check that the MacroPulse API is running on port 8001.
  </EmptyState>
);

export const Skeleton: React.FC<{ className?: string }> = ({ className }) => <div className={cx("skeleton", className)} aria-hidden />;

export const TableSkeleton: React.FC<{ rows?: number; cols: number }> = ({ rows = 6, cols }) => (
  <>
    {[...Array(rows)].map((_, r) => (
      <tr key={r}>
        {[...Array(cols)].map((__, c) => (
          <td key={c}>
            <Skeleton className="h-3.5 w-full max-w-[7rem]" />
          </td>
        ))}
      </tr>
    ))}
  </>
);

export { cx };
