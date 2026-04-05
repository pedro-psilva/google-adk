import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost";

interface ButtonProps extends PropsWithChildren, ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  stretch?: boolean;
  busy?: boolean;
}

export function Button({
  children,
  className = "",
  disabled,
  variant = "primary",
  stretch = false,
  busy = false,
  ...props
}: ButtonProps) {
  return (
    <button
      className={`button button--${variant} ${stretch ? "button--stretch" : ""} ${className}`.trim()}
      disabled={disabled || busy}
      {...props}
    >
      <span className="button__label">{children}</span>
      {busy ? <span className="button__spinner" aria-hidden="true" /> : null}
    </button>
  );
}
