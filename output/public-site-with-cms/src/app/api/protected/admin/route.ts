import { getCurrentUserFromRequest } from "@/lib/auth";
import { withObservedRoute } from "@/lib/observability";
import { isAdminUser } from "@/lib/permissions";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const NO_STORE_HEADERS = {
  "Cache-Control": "no-store",
};

const handleGet = async (request: Request) => {
  const currentUser = await getCurrentUserFromRequest(request);

  if (!currentUser) {
    return Response.json(
      {
        message: "Unauthorized",
      },
      {
        headers: NO_STORE_HEADERS,
        status: 401,
      },
    );
  }

  if (!isAdminUser(currentUser)) {
    return Response.json(
      {
        message: "Forbidden",
      },
      {
        headers: NO_STORE_HEADERS,
        status: 403,
      },
    );
  }

  return Response.json(
    {
      authorized: true,
      user: currentUser,
    },
    {
      headers: NO_STORE_HEADERS,
      status: 200,
    },
  );
};

export const GET = withObservedRoute({
  handler: handleGet,
  route: "/api/protected/admin",
  service: "api",
});
