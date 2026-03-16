import { captureError, createLogger } from "@/lib/observability";

type RequestErrorContext = {
  renderSource?:
    | "react-server-components"
    | "react-server-components-payload"
    | "server-rendering";
  revalidateReason: "on-demand" | "stale" | undefined;
  routePath: string;
  routeType: "render" | "route" | "action" | "middleware";
  routerKind: "Pages Router" | "App Router";
};

type RequestErrorRequest = Readonly<{
  headers: NodeJS.Dict<string | string[]>;
  method: string;
  path: string;
}>;

const logger = createLogger({
  scope: "instrumentation",
  service: "next-app",
});

export function register(): void {
  logger.info("instrumentation-registered", {
    runtime: process.env.NEXT_RUNTIME ?? "nodejs",
  });
}

export const onRequestError = async (
  error: unknown,
  request: RequestErrorRequest,
  context: RequestErrorContext,
) => {
  captureError({
    details: {
      method: request.method,
      path: request.path,
      renderSource: context.renderSource ?? null,
      revalidateReason: context.revalidateReason ?? null,
      routePath: context.routePath,
      routeType: context.routeType,
      routerKind: context.routerKind,
    },
    error,
    event: "next-request-error",
    scope: "request",
    service: "next-app",
  });
};
