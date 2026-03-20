import { logger, registerUnhandledErrorHandlers } from "./lib/logger";

type RequestErrorRequest = Readonly<{
  headers: NodeJS.Dict<string | string[]>;
  method: string;
  path: string;
}>;

type RequestErrorContext = Readonly<{
  renderSource?:
    | "react-server-components"
    | "react-server-components-payload"
    | "server-rendering";
  revalidateReason?: "on-demand" | "stale";
  routePath: string;
  routeType: "render" | "route" | "action" | "middleware";
  routerKind: "Pages Router" | "App Router";
}>;

export function register(): void {
  registerUnhandledErrorHandlers();
}

export async function onRequestError(
  error: unknown,
  request: RequestErrorRequest,
  context: RequestErrorContext,
): Promise<void> {
  logger.error("Request handling failed", {
    category: "request",
    error,
    method: request.method,
    path: request.path,
    renderSource: context.renderSource,
    revalidateReason: context.revalidateReason,
    routePath: context.routePath,
    routeType: context.routeType,
    routerKind: context.routerKind,
  });
}
