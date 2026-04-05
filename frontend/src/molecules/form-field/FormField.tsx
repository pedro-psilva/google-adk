import type { PropsWithChildren } from "react";

interface FormFieldProps extends PropsWithChildren {
  label: string;
  hint?: string;
}

export function FormField({ label, hint, children }: FormFieldProps) {
  return (
    <label className="form-field">
      <span className="form-field__label">{label}</span>
      {hint ? <span className="form-field__hint">{hint}</span> : null}
      {children}
    </label>
  );
}
