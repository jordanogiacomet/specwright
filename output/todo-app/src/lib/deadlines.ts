const DATE_ONLY_PATTERN = /^(\d{4})-(\d{2})-(\d{2})$/;

function padDatePart(value: number): string {
  return `${value}`.padStart(2, "0");
}

function formatDateParts(year: number, month: number, day: number): string {
  return `${year}-${padDatePart(month)}-${padDatePart(day)}`;
}

function formatUtcDateOnly(value: Date): string {
  return formatDateParts(
    value.getUTCFullYear(),
    value.getUTCMonth() + 1,
    value.getUTCDate(),
  );
}

function formatLocalDateOnly(value: Date): string {
  return formatDateParts(
    value.getFullYear(),
    value.getMonth() + 1,
    value.getDate(),
  );
}

function parseDateOnlyString(value: string): string | null {
  const match = DATE_ONLY_PATTERN.exec(value);

  if (!match) {
    return null;
  }

  const year = Number.parseInt(match[1], 10);
  const month = Number.parseInt(match[2], 10);
  const day = Number.parseInt(match[3], 10);
  const parsedDate = new Date(Date.UTC(year, month - 1, day));

  if (
    parsedDate.getUTCFullYear() !== year ||
    parsedDate.getUTCMonth() + 1 !== month ||
    parsedDate.getUTCDate() !== day
  ) {
    return null;
  }

  return formatDateParts(year, month, day);
}

function parseDueDateString(value: string): string | null {
  const normalizedDateOnly = parseDateOnlyString(value);

  if (normalizedDateOnly) {
    return normalizedDateOnly;
  }

  const parsedDate = new Date(value);

  if (Number.isNaN(parsedDate.valueOf())) {
    return null;
  }

  return formatUtcDateOnly(parsedDate);
}

export function normalizeDueDateInput(value: unknown): {
  value: string | null;
  error: string | null;
} {
  if (value === undefined || value === null) {
    return {
      value: null,
      error: null,
    };
  }

  if (value instanceof Date) {
    if (Number.isNaN(value.valueOf())) {
      return {
        value: null,
        error: "must be a valid date.",
      };
    }

    return {
      value: formatUtcDateOnly(value),
      error: null,
    };
  }

  if (typeof value !== "string") {
    return {
      value: null,
      error: "must be a valid ISO 8601 date string or YYYY-MM-DD value.",
    };
  }

  const normalizedValue = value.trim();

  if (!normalizedValue) {
    return {
      value: null,
      error: null,
    };
  }

  const parsedDueDate = parseDueDateString(normalizedValue);

  if (!parsedDueDate) {
    return {
      value: null,
      error: "must be a valid ISO 8601 date string or YYYY-MM-DD value.",
    };
  }

  return {
    value: parsedDueDate,
    error: null,
  };
}

export function serializeDueDate(value: string | Date): string {
  const normalizedDueDate = normalizeDueDateInput(value);

  if (!normalizedDueDate.value || normalizedDueDate.error) {
    throw new Error("Unable to serialize due date.");
  }

  return normalizedDueDate.value;
}

export function formatDueDateForDisplay(
  dueDate: string,
  locale?: string,
): string {
  const normalizedDateOnly = parseDateOnlyString(dueDate);

  if (!normalizedDateOnly) {
    const parsedDate = new Date(dueDate);

    if (Number.isNaN(parsedDate.valueOf())) {
      return dueDate;
    }

    return new Intl.DateTimeFormat(locale, {
      dateStyle: "medium",
    }).format(parsedDate);
  }

  const [year, month, day] = normalizedDateOnly
    .split("-")
    .map((part) => Number.parseInt(part, 10));

  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
  }).format(new Date(year, month - 1, day));
}

export function isOverdueDueDate(
  dueDate: string | null,
  options: {
    completed?: boolean;
    referenceDate?: Date;
  } = {},
): boolean {
  if (!dueDate || options.completed) {
    return false;
  }

  const today = formatLocalDateOnly(options.referenceDate ?? new Date());

  return dueDate < today;
}
