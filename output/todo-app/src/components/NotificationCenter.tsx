"use client";

import Link from "next/link";
import { useEffect, useState, type ChangeEvent } from "react";

import type { AppLocale } from "@/lib/i18n";

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
  "http://localhost:3001";

const notificationPriorities = ["low", "normal", "high", "critical"] as const;

type NotificationPriority = (typeof notificationPriorities)[number];

type NotificationRecord = {
  id: string;
  eventKey: string;
  type: string;
  priority: NotificationPriority;
  title: string;
  body: string;
  isRead: boolean;
  readAt: string | null;
  createdAt: string;
};

type NotificationPreferences = {
  notificationsEnabled: boolean;
  minimumPriority: NotificationPriority;
  updatedAt: string;
};

type NotificationInbox = {
  items: NotificationRecord[];
  unreadCount: number;
  preferences: NotificationPreferences;
};

type NotificationTriggerResponse = {
  delivered: boolean;
  message: string;
  notification: NotificationRecord | null;
  preferences: NotificationPreferences;
};

type StatusState = {
  tone: "neutral" | "success" | "error";
  message: string;
};

type NotificationCenterProps = {
  locale: AppLocale;
};

const copy = {
  en: {
    eyebrow: "Notifications",
    title: "Notification center",
    description:
      "Review in-app notifications, manage read state, and control delivery rules for your user.",
    loading: "Loading notifications...",
    unauthorizedTitle: "Authentication required",
    unauthorizedBody:
      "Sign in first, then return here to inspect the notification inbox.",
    signInLabel: "Open login",
    refresh: "Refresh",
    trigger: "Trigger sample notification",
    triggerHint:
      "The sample event is created with high priority so it appears with the default rules.",
    preferencesTitle: "Preferences",
    notificationsEnabled: "Enable in-app notifications",
    minimumPriority: "Minimum priority to store",
    savePreferences: "Save preferences",
    updatedAt: "Updated",
    unread: "Unread",
    read: "Read",
    markRead: "Mark as read",
    markUnread: "Mark as unread",
    noNotifications: "No notifications yet. Trigger one to validate the flow.",
    refreshSuccess: "Notification center updated.",
    loadError: "Unable to reach the notifications API.",
    saveSuccess: "Notification preferences saved.",
    triggerSuccess: "Notification created.",
    triggerSkipped:
      "Notification skipped because your current preferences filtered it out.",
    toggleReadSuccess: "Notification state updated.",
  },
  pt: {
    eyebrow: "Notificacoes",
    title: "Central de notificacoes",
    description:
      "Revise notificacoes no aplicativo, controle o estado de leitura e ajuste as regras de entrega do usuario.",
    loading: "Carregando notificacoes...",
    unauthorizedTitle: "Autenticacao obrigatoria",
    unauthorizedBody:
      "Entre primeiro e depois volte para ver a caixa de notificacoes.",
    signInLabel: "Abrir login",
    refresh: "Atualizar",
    trigger: "Gerar notificacao de teste",
    triggerHint:
      "O evento de teste usa prioridade high para aparecer com as regras padrao.",
    preferencesTitle: "Preferencias",
    notificationsEnabled: "Ativar notificacoes no aplicativo",
    minimumPriority: "Prioridade minima para salvar",
    savePreferences: "Salvar preferencias",
    updatedAt: "Atualizado",
    unread: "Nao lida",
    read: "Lida",
    markRead: "Marcar como lida",
    markUnread: "Marcar como nao lida",
    noNotifications:
      "Ainda nao ha notificacoes. Gere uma para validar o fluxo.",
    refreshSuccess: "Central de notificacoes atualizada.",
    loadError: "Nao foi possivel acessar a API de notificacoes.",
    saveSuccess: "Preferencias de notificacao salvas.",
    triggerSuccess: "Notificacao criada.",
    triggerSkipped:
      "A notificacao foi ignorada porque as preferencias atuais a filtraram.",
    toggleReadSuccess: "O estado da notificacao foi atualizado.",
  },
} satisfies Record<AppLocale, Record<string, string>>;

const priorityLabels: Record<NotificationPriority, string> = {
  low: "Low",
  normal: "Normal",
  high: "High",
  critical: "Critical",
};

async function parseResponse(response: Response) {
  const contentType = response.headers.get("content-type") ?? "";

  if (!contentType.includes("application/json")) {
    return null;
  }

  return (await response.json()) as Record<string, unknown>;
}

function getResponseMessage(body: unknown, fallbackMessage: string): string {
  if (
    typeof body === "object" &&
    body !== null &&
    "message" in body &&
    typeof body.message === "string"
  ) {
    return body.message;
  }

  return fallbackMessage;
}

async function request<T>(
  path: string,
  init: RequestInit,
): Promise<{ ok: boolean; status: number; body: T | null }> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });

  return {
    ok: response.ok,
    status: response.status,
    body: (await parseResponse(response)) as T | null,
  };
}

function formatTimestamp(value: string): string {
  return new Date(value).toLocaleString();
}

export function NotificationCenter({ locale }: NotificationCenterProps) {
  const localeCopy = copy[locale];
  const [notificationInbox, setNotificationInbox] =
    useState<NotificationInbox | null>(null);
  const [preferencesForm, setPreferencesForm] = useState<{
    notificationsEnabled: boolean;
    minimumPriority: NotificationPriority;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [activeAction, setActiveAction] = useState<string | null>(null);
  const [status, setStatus] = useState<StatusState>({
    tone: "neutral",
    message: localeCopy.description,
  });

  async function loadNotificationInbox(options?: { preserveStatus?: boolean }) {
    setIsLoading(true);

    try {
      const response = await request<NotificationInbox>("/api/notifications", {
        method: "GET",
      });

      if (response.status === 401) {
        setIsAuthenticated(false);
        setNotificationInbox(null);
        setPreferencesForm(null);

        if (!options?.preserveStatus) {
          setStatus({
            tone: "neutral",
            message: localeCopy.unauthorizedBody,
          });
        }

        return;
      }

      if (!response.ok || !response.body) {
        setStatus({
          tone: "error",
          message: getResponseMessage(response.body, localeCopy.loadError),
        });
        return;
      }

      setIsAuthenticated(true);
      setNotificationInbox(response.body);
      setPreferencesForm({
        notificationsEnabled: response.body.preferences.notificationsEnabled,
        minimumPriority: response.body.preferences.minimumPriority,
      });

      if (!options?.preserveStatus) {
        setStatus({
          tone: "success",
          message: localeCopy.refreshSuccess,
        });
      }
    } catch {
      setStatus({
        tone: "error",
        message: localeCopy.loadError,
      });
    } finally {
      setIsLoading(false);
      setActiveAction(null);
    }
  }

  useEffect(() => {
    let isMounted = true;

    setIsLoading(true);

    void request<NotificationInbox>("/api/notifications", {
      method: "GET",
    })
      .then((response) => {
        if (!isMounted) {
          return;
        }

        if (response.status === 401) {
          setIsAuthenticated(false);
          setNotificationInbox(null);
          setPreferencesForm(null);
          return;
        }

        if (!response.ok || !response.body) {
          setStatus({
            tone: "error",
            message: getResponseMessage(response.body, localeCopy.loadError),
          });
          return;
        }

        setIsAuthenticated(true);
        setNotificationInbox(response.body);
        setPreferencesForm({
          notificationsEnabled: response.body.preferences.notificationsEnabled,
          minimumPriority: response.body.preferences.minimumPriority,
        });
      })
      .catch(() => {
        if (!isMounted) {
          return;
        }

        setStatus({
          tone: "error",
          message: localeCopy.loadError,
        });
      })
      .finally(() => {
        if (!isMounted) {
          return;
        }

        setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [locale, localeCopy]);

  async function handleRefresh() {
    setActiveAction("refresh");
    await loadNotificationInbox();
  }

  async function handleTrigger() {
    setActiveAction("trigger");

    try {
      const response = await request<NotificationTriggerResponse>(
        "/api/notifications/trigger",
        {
          method: "POST",
          body: JSON.stringify({
            eventKey: "manual.trigger",
            type: "system",
            priority: "high",
            title:
              locale === "pt" ? "Notificacao de teste" : "Sample notification",
            body:
              locale === "pt"
                ? "Este evento foi criado manualmente para validar a central de notificacoes."
                : "This event was created manually to validate notification delivery.",
          }),
        },
      );

      if (response.status === 401) {
        setIsAuthenticated(false);
        setNotificationInbox(null);
        setPreferencesForm(null);
        setStatus({
          tone: "neutral",
          message: localeCopy.unauthorizedBody,
        });
        return;
      }

      if (!response.ok || !response.body) {
        setStatus({
          tone: "error",
          message: getResponseMessage(response.body, localeCopy.loadError),
        });
        return;
      }

      await loadNotificationInbox({ preserveStatus: true });
      setStatus({
        tone: response.body.delivered ? "success" : "neutral",
        message: response.body.delivered
          ? localeCopy.triggerSuccess
          : localeCopy.triggerSkipped,
      });
    } catch {
      setStatus({
        tone: "error",
        message: localeCopy.loadError,
      });
    } finally {
      setActiveAction(null);
    }
  }

  async function handleToggleRead(notification: NotificationRecord) {
    setActiveAction(`toggle:${notification.id}`);

    try {
      const response = await request<NotificationRecord>(
        `/api/notifications/${notification.id}`,
        {
          method: "PATCH",
          body: JSON.stringify({
            isRead: !notification.isRead,
          }),
        },
      );

      if (response.status === 401) {
        setIsAuthenticated(false);
        setNotificationInbox(null);
        setPreferencesForm(null);
        setStatus({
          tone: "neutral",
          message: localeCopy.unauthorizedBody,
        });
        return;
      }

      if (!response.ok || !response.body) {
        setStatus({
          tone: "error",
          message: getResponseMessage(response.body, localeCopy.loadError),
        });
        return;
      }

      await loadNotificationInbox({ preserveStatus: true });
      setStatus({
        tone: "success",
        message: localeCopy.toggleReadSuccess,
      });
    } catch {
      setStatus({
        tone: "error",
        message: localeCopy.loadError,
      });
    } finally {
      setActiveAction(null);
    }
  }

  async function handleSavePreferences() {
    if (!preferencesForm) {
      return;
    }

    setActiveAction("preferences");

    try {
      const response = await request<NotificationPreferences>(
        "/api/notifications/preferences",
        {
          method: "PUT",
          body: JSON.stringify(preferencesForm),
        },
      );

      if (response.status === 401) {
        setIsAuthenticated(false);
        setNotificationInbox(null);
        setPreferencesForm(null);
        setStatus({
          tone: "neutral",
          message: localeCopy.unauthorizedBody,
        });
        return;
      }

      if (!response.ok || !response.body) {
        setStatus({
          tone: "error",
          message: getResponseMessage(response.body, localeCopy.loadError),
        });
        return;
      }

      const updatedPreferences = response.body;

      setNotificationInbox((currentInbox) =>
        currentInbox
          ? {
              ...currentInbox,
              preferences: updatedPreferences,
            }
          : currentInbox,
      );
      setPreferencesForm({
        notificationsEnabled: updatedPreferences.notificationsEnabled,
        minimumPriority: updatedPreferences.minimumPriority,
      });
      setStatus({
        tone: "success",
        message: localeCopy.saveSuccess,
      });
    } catch {
      setStatus({
        tone: "error",
        message: localeCopy.loadError,
      });
    } finally {
      setActiveAction(null);
    }
  }

  function handlePreferencesToggle(event: ChangeEvent<HTMLInputElement>) {
    const { checked } = event.target;

    setPreferencesForm((currentForm) =>
      currentForm
        ? {
            ...currentForm,
            notificationsEnabled: checked,
          }
        : currentForm,
    );
  }

  function handlePriorityChange(event: ChangeEvent<HTMLSelectElement>) {
    const value = event.target.value as NotificationPriority;

    setPreferencesForm((currentForm) =>
      currentForm
        ? {
            ...currentForm,
            minimumPriority: value,
          }
        : currentForm,
    );
  }

  return (
    <section className="space-y-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-4 border-b border-slate-200 pb-6 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
            {localeCopy.eyebrow}
          </p>
          <div className="space-y-2">
            <h3 className="text-2xl font-semibold tracking-tight text-slate-950">
              {localeCopy.title}
            </h3>
            <p className="max-w-2xl text-sm text-slate-600">
              {localeCopy.description}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <span className="rounded-full bg-slate-900 px-3 py-1 text-sm font-medium text-white">
            {notificationInbox?.unreadCount ?? 0} {localeCopy.unread}
          </span>
          <button
            type="button"
            onClick={handleRefresh}
            disabled={activeAction !== null}
            className="rounded-full border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-950 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {localeCopy.refresh}
          </button>
          <button
            type="button"
            onClick={handleTrigger}
            disabled={activeAction !== null || isAuthenticated === false}
            className="rounded-full bg-slate-950 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {localeCopy.trigger}
          </button>
        </div>
      </div>

      <div
        className={`rounded-2xl px-4 py-3 text-sm ${
          status.tone === "error"
            ? "bg-rose-50 text-rose-700"
            : status.tone === "success"
              ? "bg-emerald-50 text-emerald-700"
              : "bg-slate-100 text-slate-700"
        }`}
      >
        {status.message}
      </div>

      {isLoading ? (
        <div className="rounded-2xl border border-dashed border-slate-300 px-4 py-8 text-sm text-slate-500">
          {localeCopy.loading}
        </div>
      ) : null}

      {!isLoading && isAuthenticated === false ? (
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
          <div className="space-y-2">
            <h4 className="text-lg font-semibold text-slate-950">
              {localeCopy.unauthorizedTitle}
            </h4>
            <p className="text-sm text-slate-600">
              {localeCopy.unauthorizedBody}
            </p>
            <Link
              href="/login"
              className="inline-flex rounded-full bg-slate-950 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800"
            >
              {localeCopy.signInLabel}
            </Link>
          </div>
        </div>
      ) : null}

      {!isLoading && isAuthenticated ? (
        <div className="grid gap-6 lg:grid-cols-[minmax(0,18rem)_minmax(0,1fr)]">
          <aside className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-5">
            <div className="space-y-1">
              <h4 className="text-lg font-semibold text-slate-950">
                {localeCopy.preferencesTitle}
              </h4>
              <p className="text-sm text-slate-600">{localeCopy.triggerHint}</p>
            </div>

            {preferencesForm ? (
              <div className="space-y-4">
                <label className="flex items-start gap-3 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={preferencesForm.notificationsEnabled}
                    onChange={handlePreferencesToggle}
                    className="mt-1 size-4 rounded border-slate-300"
                  />
                  <span>{localeCopy.notificationsEnabled}</span>
                </label>

                <label className="flex flex-col gap-2 text-sm text-slate-700">
                  <span>{localeCopy.minimumPriority}</span>
                  <select
                    value={preferencesForm.minimumPriority}
                    onChange={handlePriorityChange}
                    className="rounded-2xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900"
                  >
                    {notificationPriorities.map((priority) => (
                      <option key={priority} value={priority}>
                        {priorityLabels[priority]}
                      </option>
                    ))}
                  </select>
                </label>

                <button
                  type="button"
                  onClick={handleSavePreferences}
                  disabled={activeAction !== null}
                  className="w-full rounded-full bg-slate-950 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {localeCopy.savePreferences}
                </button>

                {notificationInbox ? (
                  <p className="text-xs text-slate-500">
                    {localeCopy.updatedAt}:{" "}
                    {formatTimestamp(notificationInbox.preferences.updatedAt)}
                  </p>
                ) : null}
              </div>
            ) : null}
          </aside>

          <div className="space-y-4">
            {notificationInbox && notificationInbox.items.length > 0 ? (
              notificationInbox.items.map((notification) => (
                <article
                  key={notification.id}
                  className={`rounded-2xl border p-5 transition ${
                    notification.isRead
                      ? "border-slate-200 bg-slate-50"
                      : "border-sky-200 bg-sky-50/70"
                  }`}
                >
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div className="space-y-3">
                      <div className="flex flex-wrap items-center gap-2 text-xs font-medium uppercase tracking-[0.16em] text-slate-500">
                        <span>{notification.type}</span>
                        <span className="rounded-full bg-white px-2 py-1 tracking-normal text-slate-700">
                          {priorityLabels[notification.priority]}
                        </span>
                        <span className="rounded-full bg-white px-2 py-1 tracking-normal text-slate-700">
                          {notification.isRead
                            ? localeCopy.read
                            : localeCopy.unread}
                        </span>
                      </div>
                      <div className="space-y-1">
                        <h5 className="text-lg font-semibold text-slate-950">
                          {notification.title}
                        </h5>
                        <p className="text-sm text-slate-700">
                          {notification.body}
                        </p>
                      </div>
                      <dl className="flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-slate-500">
                        <div>
                          <dt className="inline font-medium">Event:</dt>{" "}
                          <dd className="inline">{notification.eventKey}</dd>
                        </div>
                        <div>
                          <dt className="inline font-medium">Created:</dt>{" "}
                          <dd className="inline">
                            {formatTimestamp(notification.createdAt)}
                          </dd>
                        </div>
                        {notification.readAt ? (
                          <div>
                            <dt className="inline font-medium">Read:</dt>{" "}
                            <dd className="inline">
                              {formatTimestamp(notification.readAt)}
                            </dd>
                          </div>
                        ) : null}
                      </dl>
                    </div>

                    <button
                      type="button"
                      onClick={() => {
                        void handleToggleRead(notification);
                      }}
                      disabled={activeAction !== null}
                      className="rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-950 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {notification.isRead
                        ? localeCopy.markUnread
                        : localeCopy.markRead}
                    </button>
                  </div>
                </article>
              ))
            ) : (
              <div className="rounded-2xl border border-dashed border-slate-300 px-4 py-8 text-sm text-slate-500">
                {localeCopy.noNotifications}
              </div>
            )}
          </div>
        </div>
      ) : null}
    </section>
  );
}
