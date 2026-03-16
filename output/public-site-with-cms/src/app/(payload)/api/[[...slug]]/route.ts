import config from "@payload-config";
import {
  REST_DELETE,
  REST_GET,
  REST_OPTIONS,
  REST_PATCH,
  REST_POST,
  REST_PUT,
} from "@payloadcms/next/routes";

import { withObservedRoute } from "@/lib/observability";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const PAYLOAD_API_ROUTE = "/api/[[...slug]]";
const PAYLOAD_API_SERVICE = "payload-api";

export const GET = withObservedRoute({
  handler: REST_GET(config),
  rethrowErrors: true,
  route: PAYLOAD_API_ROUTE,
  service: PAYLOAD_API_SERVICE,
});
export const POST = withObservedRoute({
  handler: REST_POST(config),
  rethrowErrors: true,
  route: PAYLOAD_API_ROUTE,
  service: PAYLOAD_API_SERVICE,
});
export const DELETE = withObservedRoute({
  handler: REST_DELETE(config),
  rethrowErrors: true,
  route: PAYLOAD_API_ROUTE,
  service: PAYLOAD_API_SERVICE,
});
export const PATCH = withObservedRoute({
  handler: REST_PATCH(config),
  rethrowErrors: true,
  route: PAYLOAD_API_ROUTE,
  service: PAYLOAD_API_SERVICE,
});
export const PUT = withObservedRoute({
  handler: REST_PUT(config),
  rethrowErrors: true,
  route: PAYLOAD_API_ROUTE,
  service: PAYLOAD_API_SERVICE,
});
export const OPTIONS = withObservedRoute({
  handler: REST_OPTIONS(config),
  rethrowErrors: true,
  route: PAYLOAD_API_ROUTE,
  service: PAYLOAD_API_SERVICE,
});
